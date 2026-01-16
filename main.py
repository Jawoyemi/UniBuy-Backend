from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import router as auth_router

app = FastAPI(
    title="Unibuy API",
    description="Unibuy API",
    version="0.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to Unibuy API"}

@app.get("/health")
def read_health():
    return {"message": "Unibuy API is running"}

