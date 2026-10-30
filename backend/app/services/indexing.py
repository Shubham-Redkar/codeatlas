from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Repository
from ..database.repositories import (
    create_repository_file,
    delete_repository_file,
    get_indexed_files,
    get_repository_files_by_paths,
    get_repository_symbols,
    replace_file_dependencies,
    replace_symbol_relationships,
    replace_symbols,
    update_repository_file,
)
from ..graph import build_python_dependency_graph, resolve_python_import
from ..ingestion import (
    FileChange,
    FileChangeType,
    build_current_file_state,
    compare_files,
    detect_language,
    discover_files,
    filter_files,
)
from ..parser import (
    SupportedLanguage,
    extract_imports,
    extract_relationships,
    extract_symbols,
    parse_source,
)


async def index_repository(
    session: AsyncSession,
    repository: Repository,
    repository_path: Path,
) -> list[FileChange]:
    """
    Synchronize repository file state with the database.
    """
    discovered_files = discover_files(repository_path)
    filtered_files = filter_files(discovered_files)

    current_files = build_current_file_state(
        repository_path=repository_path,
        files=filtered_files,
    )

    async with session.begin():
        indexed_files = await get_indexed_files(
            session=session,
            repository_id=repository.id,
        )

        changes = compare_files(
            current_files=current_files,
            indexed_files=indexed_files,
        )

        for change in changes:
            match change.change_type:
                case FileChangeType.NEW | FileChangeType.CHANGED:
                    file_path = repository_path / change.path
                    size_bytes = file_path.stat().st_size
                    content_hash = current_files[change.path]

                    if change.change_type is FileChangeType.NEW:
                        repository_file = await create_repository_file(
                            session=session,
                            repository_id=repository.id,
                            path=change.path,
                            content_hash=content_hash,
                            size_bytes=size_bytes,
                        )
                    else:
                        repository_file = await update_repository_file(
                            session=session,
                            repository_id=repository.id,
                            path=change.path,
                            content_hash=content_hash,
                            size_bytes=size_bytes,
                        )

                    if repository_file is None or repository_file.language is None:
                        continue

                    language = SupportedLanguage(repository_file.language)
                    source = file_path.read_bytes()
                    tree = parse_source(source, language)
                    symbols = extract_symbols(tree.root_node, language.value)
                    relationships = extract_relationships(tree.root_node, language.value)

                    persisted_symbols = await replace_symbols(
                        session=session,
                        repository_file_id=repository_file.id,
                        symbols=symbols,
                    )

                    symbol_ids_by_name: dict[str, list[UUID]] = {}
                    for symbol in persisted_symbols:
                        symbol_ids_by_name.setdefault(symbol.name, []).append(symbol.id)

                    relationship_edges = []
                    for relationship in relationships:
                        source_ids = symbol_ids_by_name.get(relationship.source, [])
                        target_ids = symbol_ids_by_name.get(relationship.target, [])

                        if len(source_ids) != 1 or len(target_ids) != 1:
                            continue

                        relationship_edges.append(
                            (
                                source_ids[0],
                                target_ids[0],
                                relationship.kind.value,
                                relationship.line,
                            )
                        )

                    await replace_symbol_relationships(
                        session=session,
                        repository_file_id=repository_file.id,
                        relationships=relationship_edges,
                    )

                case FileChangeType.DELETED:
                    await delete_repository_file(
                        session=session,
                        repository_id=repository.id,
                        path=change.path,
                    )

                case FileChangeType.UNCHANGED:
                    pass

        repository_files = await get_repository_files_by_paths(
            session=session,
            repository_id=repository.id,
            paths=current_files.keys(),
        )

        repository_files_by_path = {
            repository_file.path: repository_file for repository_file in repository_files
        }

        persisted_symbols = await get_repository_symbols(
            session=session,
            repository_id=repository.id,
        )

        file_paths_by_id = {
            repository_file.id: repository_file.path for repository_file in repository_files
        }

        symbols_by_file_and_name: dict[tuple[str, str], list[UUID]] = {}

        for symbol in persisted_symbols:
            symbol_path = file_paths_by_id.get(symbol.repository_file_id)

            if symbol_path is not None:
                symbols_by_file_and_name.setdefault(
                    (symbol_path, symbol.name),
                    [],
                ).append(symbol.id)

        imports_by_file = {}
        available_files = set(current_files)

        for file_path in filtered_files:
            detected_language = detect_language(file_path)

            if detected_language is None or detected_language.value != "python":
                continue

            relative_path = file_path.relative_to(repository_path).as_posix()
            repository_file = repository_files_by_path.get(relative_path)

            if repository_file is None:
                continue

            source = file_path.read_bytes()
            tree = parse_source(source, SupportedLanguage.PYTHON)

            imports = extract_imports(
                tree.root_node,
                SupportedLanguage.PYTHON.value,
            )
            imports_by_file[relative_path] = imports

            imported_symbols: dict[str, tuple[str, str]] = {}

            for import_statement in imports:
                target_path = resolve_python_import(
                    import_statement,
                    available_files,
                    source=relative_path,
                )

                if target_path is None:
                    continue

                aliases = dict(import_statement.aliases)

                for imported_name in import_statement.imported_names:
                    if imported_name == "*":
                        continue

                    local_name = aliases.get(imported_name, imported_name)

                    imported_symbols[local_name] = (
                        target_path,
                        imported_name,
                    )

            relationships = extract_relationships(
                tree.root_node,
                SupportedLanguage.PYTHON.value,
            )

            relationship_edges = []

            for relationship in relationships:
                source_ids = symbols_by_file_and_name.get(
                    (relative_path, relationship.source),
                    [],
                )

                if len(source_ids) != 1:
                    continue

                target_ids = symbols_by_file_and_name.get(
                    (relative_path, relationship.target),
                    [],
                )

                if len(target_ids) > 1:
                    continue

                if len(target_ids) == 1:
                    target_id = target_ids[0]
                else:
                    imported_target = imported_symbols.get(relationship.target)

                    if imported_target is None:
                        continue

                    target_path, target_name = imported_target

                    imported_target_ids = symbols_by_file_and_name.get(
                        (target_path, target_name),
                        [],
                    )

                    if len(imported_target_ids) != 1:
                        continue

                    target_id = imported_target_ids[0]

                relationship_edges.append(
                    (
                        source_ids[0],
                        target_id,
                        relationship.kind.value,
                        relationship.line,
                    )
                )

            await replace_symbol_relationships(
                session=session,
                repository_file_id=repository_file.id,
                relationships=relationship_edges,
            )

        dependency_graph = build_python_dependency_graph(
            imports_by_file=imports_by_file,
            available_files=set(current_files),
        )

        await replace_file_dependencies(
            session=session,
            repository_id=repository.id,
            dependencies=dependency_graph.dependencies,
        )

    return changes
