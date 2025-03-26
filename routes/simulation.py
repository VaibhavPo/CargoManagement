# routes/simulation.py
from fastapi import APIRouter
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/simulate")

@router.post("/day")
def simulate_day(numOfDays: int):
    new_date = datetime.now() + timedelta(days=numOfDays)
    return {"success": True, "newDate": new_date.isoformat(), "changes": {}}