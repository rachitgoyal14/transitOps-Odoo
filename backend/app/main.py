from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.session import AsyncSessionLocal
from app.db.init_db import seed_default_admin
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed the default admin user on startup
    async with AsyncSessionLocal() as session:
        await seed_default_admin(session)
    yield

app = FastAPI(
    title="TransitOps API",
    description="Backend API for TransitOps Fleet Management System",
    version="1.0.0",
    lifespan=lifespan
)

# Include the API version 1 router
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}
