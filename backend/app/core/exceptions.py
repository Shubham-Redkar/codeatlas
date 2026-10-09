class CodeAtlasError(Exception):
    """Base exception for application-specific errors."""


class GitError(CodeAtlasError):
    """Base exception for Git-related errors."""


class GitCloneError(GitError):
    """Raised when a Git repository cannot be cloned."""


class RepositoryPathError(CodeAtlasError):
    """Raised when a repository path is invalid."""
