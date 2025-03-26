# routes/placement.py
from fastapi import APIRouter, HTTPException
from models import PlacementRequest
from database import get_db_connection

router = APIRouter(prefix="/api/placement")

@router.post("/")
def recommend_placement(request: PlacementRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    placements = []
    
    for item in request.items:
        cursor.execute("SELECT containerId, width, depth, height FROM containers WHERE zone = ?", (item.preferredZone,))
        containers = cursor.fetchall()
        
        if not containers:
            raise HTTPException(status_code=400, detail=f"No available containers in preferred zone: {item.preferredZone}")
        
        for container in containers:
            containerId, c_width, c_depth, c_height = container
            if item.width <= c_width and item.depth <= c_depth and item.height <= c_height:
                cursor.execute("UPDATE items SET containerId = ?, startX = 0, startY = 0, startZ = 0 WHERE itemId = ?", (containerId, item.itemId))
                placements.append({"itemId": item.itemId, "containerId": containerId, "position": {"startX": 0, "startY": 0, "startZ": 0}})
                break
    
    conn.commit()
    conn.close()
    return {"success": True, "placements": placements}

