from fastapi import APIRouter
from database import get_db_connection
from datetime import datetime

router = APIRouter(prefix="/api/waste")

@router.get("/identify")
def identify_waste():
    conn = get_db_connection()
    cursor = conn.cursor()
    current_date = datetime.now().isoformat()
    cursor.execute("SELECT itemId, name FROM items WHERE expiryDate <= ?", (current_date,))
    waste_items = cursor.fetchall()
    conn.close()
    return {"success": True, "wasteItems": [{"itemId": w[0], "name": w[1], "reason": "Expired"} for w in waste_items]}
