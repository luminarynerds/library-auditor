from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.scans import router as scans_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="The Library Auditor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scans_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
