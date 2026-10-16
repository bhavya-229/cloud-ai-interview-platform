import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # Ensure all SQLAlchemy models are registered
from app.api.routes import auth, jobs, resumes, interviews, candidates, recruiters

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist in local SQLite (or RDS database)
    logger.info("Initializing relational database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Local implementation of Cloud-Based AI Interview and Candidate Assessment Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under settings.API_V1_STR ("/api")
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(resumes.router, prefix=settings.API_V1_STR)
app.include_router(interviews.router, prefix=settings.API_V1_STR)
app.include_router(candidates.router, prefix=settings.API_V1_STR)
app.include_router(recruiters.router, prefix=settings.API_V1_STR)


import os
from starlette.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Dist directory path for built React frontend
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")
assets_dir = os.path.join(frontend_dist, "assets")
if os.path.isdir(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/")
def root():
    index_html = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_html):
        return FileResponse(index_html)
    return {
        "name": settings.PROJECT_NAME,
        "status": "online",
        "storage": settings.STORAGE_BACKEND,
        "docs_url": "/docs"
    }


@app.get("/api/health")
def health_check():
    db_type = "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql (rds)"
    return {
        "status": "healthy",
        "storage": settings.STORAGE_BACKEND,
        "database": db_type,
        "aws_region": settings.AWS_REGION,
        "question_target": settings.INTERVIEW_QUESTION_COUNT
    }


if os.path.isdir(frontend_dist):
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")
        target_file = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(target_file):
            return FileResponse(target_file)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
