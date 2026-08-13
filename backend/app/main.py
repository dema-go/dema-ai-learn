from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.events import router as events_router
from app.api.feedback import router as feedback_router
from app.api.home import router as home_router
from app.api.material import router as material_router
from app.api.quiz import router as quiz_router
from app.db import init_db
from app.errors import DomainError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="考我一下", lifespan=lifespan)

    @app.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(home_router)
    app.include_router(quiz_router)
    app.include_router(feedback_router)
    app.include_router(material_router)
    app.include_router(events_router)
    return app


app = create_app()
