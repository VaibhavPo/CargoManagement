# routes/logs.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/logs")

@router.get("/")
def get_logs():
    return {"logs": []}