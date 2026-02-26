from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import load_env
from server.api.routers import auth, kb, rag, text


ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]


def create_app() -> FastAPI:
    load_env()
    app = FastAPI(title="LLM + RAG Web API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(text.router)
    app.include_router(kb.router)
    app.include_router(rag.router)

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app


app = create_app()
