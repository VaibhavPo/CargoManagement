# routes/retrieval.py
from fastapi import APIRouter
from database import get_db_connection

router = APIRouter(prefix="/api/retrieve")

@router.post("/")
def retrieve_item(itemId: str, userId: str, timestamp: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT containerId FROM items WHERE itemId = ?", (itemId,))
    item = cursor.fetchone()
    if not item:
        return {"success": False, "message": "Item not found"}
    containerId = item[0]
    cursor.execute("DELETE FROM items WHERE itemId = ?", (itemId,))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Item {itemId} retrieved from {containerId}"}
