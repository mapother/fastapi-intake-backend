# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import init_db
from .config import settings
from .routers import health as health_router
from .routers import auth as auth_router
from .routers import chat as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (optional cleanup)


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description=(
            "Memory-enabled chatbot backend with user authentication, "
            "conversation persistence, and Claude AI integration."
        ),
        lifespan=lifespan,
    )

    # CORS - allow frontend to connect
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",      # Vite default
            "http://127.0.0.1:5173",
            "http://localhost:3000",      # Common React port
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router.router, prefix=settings.API_PREFIX)
    app.include_router(auth_router.router, prefix=settings.API_PREFIX)
    app.include_router(chat_router.router, prefix=settings.API_PREFIX)

    return app


app = create_application()
