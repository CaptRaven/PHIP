import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .routers import data, predictions, auth, reports, sms

app = FastAPI(title="Predictive Health Intelligence Platform (PHIP)", version="0.1.0")

# Get allowed origins from environment variable or default to local
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
if allowed_origins_str == "*":
    origins = ["*"]
else:
    origins = [origin.strip().rstrip("/") for origin in allowed_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(sms.router, prefix="/sms", tags=["sms"])
