from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.staticfiles import StaticFiles

from app.api import auth, images, profile, project_technologies, projects, public, technologies
from app.core.config import settings
from app.utils.errors import (
    AppError,
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.utils.images import uploads_dir
from app.utils.seed import seed_technologies


@asynccontextmanager
async def lifespan(_: FastAPI):
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        seed_technologies(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Portfolio Platform API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Unified error format: {"error": {"code": "...", "message": "..."}}
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(StarletteHTTPException, lambda req, exc: JSONResponse(
    status_code=exc.status_code,
    content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}},
))
app.add_exception_handler(404, lambda req, exc: JSONResponse(
    status_code=404,
    content={"error": {"code": "NOT_FOUND", "message": "Ресурс не найден."}},
))
app.add_exception_handler(Exception, unhandled_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

api_prefix = "/api/v1"


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
    )
    if request.headers.get("x-forwarded-proto") == "https":
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


app.include_router(auth.router, prefix=api_prefix)
app.include_router(profile.router, prefix=api_prefix)
app.include_router(projects.router, prefix=api_prefix)
app.include_router(project_technologies.router, prefix=api_prefix)
app.include_router(technologies.router, prefix=api_prefix)
app.include_router(images.router, prefix=api_prefix)
app.include_router(public.router, prefix=api_prefix)


@app.get("/api/v1/health", tags=["system"])
def health():
    return {"status": "ok"}


# Uploaded files are served from /uploads (declared after API routers
# so that /api/v1 routes take priority).
app.mount("/uploads", StaticFiles(directory=uploads_dir(), check_dir=False), name="uploads")
