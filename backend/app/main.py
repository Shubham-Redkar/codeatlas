from fastapi import FastAPI

app = FastAPI(
    title="CodeAtlas API",
    description="AI-powered codebase intelligence platform",
    version="0.1.0",
)


@app.get(
    "/",
    tags=["Root"],
)
async def home() -> dict[str, str]:
    return {
        "service": "CodeAtlas API",
        "message": "API is live and ready to serve requests",
        "status": "operational",
    }


@app.get(
    "/health",
    tags=["Health"],
)
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
