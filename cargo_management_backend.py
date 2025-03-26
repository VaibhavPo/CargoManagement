from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
import sqlite3
import json

app = FastAPI()

# Database Initialization
def init_db():
    conn = sqlite3.connect("cargo.db", check_same_thread=False)  # ✅ Allow multiple threads
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")  # ✅ Enable WAL mode
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
                      item_id TEXT PRIMARY KEY,
                      name TEXT,
                      width INTEGER,
                      depth INTEGER,
                      height INTEGER,
                      priority INTEGER,
                      expiry_date TEXT,
                      usage_limit INTEGER,
                      preferred_zone TEXT,
                      container_id TEXT,
                      pos_x INTEGER,
                      pos_y INTEGER,
                      pos_z INTEGER
                  )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS containers (
                      container_id TEXT PRIMARY KEY,
                      zone TEXT,
                      width INTEGER,
                      depth INTEGER,
                      height INTEGER
                  )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                      log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TEXT,
                      user_id TEXT,
                      action_type TEXT,
                      item_id TEXT,
                      details TEXT
                  )''')
    conn.commit()
    conn.close()

init_db()

# Data Models
class Item(BaseModel):
    item_id: str
    name: str
    width: int
    depth: int
    height: int
    priority: int
    expiry_date: Optional[str] = None
    usage_limit: Optional[int] = None
    preferred_zone: str
    container_id: Optional[str] = None
    pos_x: Optional[int] = None
    pos_y: Optional[int] = None
    pos_z: Optional[int] = None

class Container(BaseModel):
    container_id: str
    zone: str
    width: int
    depth: int
    height: int

class PlacementRequest(BaseModel):
    items: List[Item]
    containers: List[Container]

# Logging Function
def log_action(user_id: str, action_type: str, item_id: str, details: dict):
    conn = sqlite3.connect("cargo.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs (timestamp, user_id, action_type, item_id, details)
        VALUES (?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), user_id, action_type, item_id, json.dumps(details)))
    conn.commit()
    conn.close()
# Rearrangement Algorithm
def rearrange_items():
    with sqlite3.connect("cargo.db", check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT item_id, container_id, width, depth, height, priority FROM items ORDER BY priority ASC")
        items = cursor.fetchall()
        
        cursor.execute("SELECT container_id, width, depth, height FROM containers")
        containers = cursor.fetchall()
        
        rearrangements = []
        
        for item in items:
            item_id, current_container, width, depth, height, priority = item
            for container in containers:
                container_id, c_width, c_depth, c_height = container
                if container_id != current_container and c_width >= width and c_depth >= depth and c_height >= height:
                    rearrangements.append({
                        "item_id": item_id,
                        "from_container": current_container,
                        "to_container": container_id
                    })
                    cursor.execute("UPDATE items SET container_id = ? WHERE item_id = ?", (container_id, item_id))
                    log_action("system", "rearrangement", item_id, {"from": current_container, "to": container_id})
                    break  
        conn.commit()
    return {"success": True, "rearrangements": rearrangements}

# Placement Algorithm
def place_items(items: List[Item], containers: List[Container]):
    placements = []
    
    with sqlite3.connect("cargo.db", check_same_thread=False) as conn:
        cursor = conn.cursor()
        conn.execute("PRAGMA journal_mode=WAL;")  # ✅ Enable WAL mode

        containers.sort(key=lambda c: c.width * c.depth * c.height, reverse=True)  
        items.sort(key=lambda i: i.priority, reverse=True)  

        for item in items:
            placed = False
            for container in containers:
                if item.preferred_zone == container.zone:
                    if container.width >= item.width and container.depth >= item.depth and container.height >= item.height:
                        placements.append({
                            "item_id": item.item_id,
                            "container_id": container.container_id,
                            "position": {
                                "startCoordinates": {"width": 0, "depth": 0, "height": 0},
                                "endCoordinates": {"width": item.width, "depth": item.depth, "height": item.height}
                            }
                        })
                        cursor.execute("""
                            INSERT INTO items (item_id, name, width, depth, height, priority, expiry_date, usage_limit, preferred_zone, container_id, pos_x, pos_y, pos_z)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (item.item_id, item.name, item.width, item.depth, item.height, item.priority, 
                              item.expiry_date, item.usage_limit, item.preferred_zone, container.container_id, 0, 0, 0))
                        conn.commit()  # ✅ Ensure data is saved
                        placed = True
                        break

            if not placed:
                raise HTTPException(status_code=400, detail=f"Item {item.item_id} could not be placed.")

    return placements

# Retrieval Optimization Algorithm
def retrieve_item(item_id: str, user_id: str):
    conn = sqlite3.connect("cargo.db")
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, name, container_id FROM items WHERE item_id = ?", (item_id,))
    item = cursor.fetchone()
    
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    
    log_action(user_id, "retrieval", item_id, {"container_id": item[2]})
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Item retrieved successfully"}

# Waste Management Algorithm
def identify_waste():
    conn = sqlite3.connect("cargo.db")
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, name, expiry_date, usage_limit FROM items")
    items = cursor.fetchall()
    
    waste_items = []
    for item in items:
        item_id, name, expiry_date, usage_limit = item
        expired = expiry_date and datetime.strptime(expiry_date, "%Y-%m-%d") < datetime.now()
        depleted = usage_limit is not None and usage_limit <= 0
        
        if expired or depleted:
            waste_items.append({
                "item_id": item_id,
                "name": name,
                "reason": "Expired" if expired else "Out of Uses"
            })
    
    conn.close()
    return {"success": True, "wasteItems": waste_items}

# API Endpoints
@app.post("/api/placement")
def placement(req: PlacementRequest):
    return {"success": True, "placements": place_items(req.items, req.containers)}

@app.get("/api/search")
def search_item(item_id: Optional[str] = None, item_name: Optional[str] = None):
    conn = sqlite3.connect("cargo.db")
    cursor = conn.cursor()
    query = "SELECT * FROM items WHERE item_id = ? OR name = ?"
    cursor.execute(query, (item_id, item_name))
    item = cursor.fetchone()
    conn.close()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"success": True, "item": item}

@app.post("/api/retrieve")
def retrieve(item_id: str, user_id: str):
    return retrieve_item(item_id, user_id)

@app.get("/api/waste/identify")
def waste_identification():
    return identify_waste()

@app.get("/api/logs")
def get_logs():
    conn = sqlite3.connect("cargo.db")
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, user_id, action_type, item_id, details FROM logs")
    logs = cursor.fetchall()
    conn.close()
    return {"success": True, "logs": logs}

@app.post("/api/rearrange")
def rearrange():
    return rearrange_items()


# Run with: uvicorn filename:app --reload



# Retrieval Optimization

# Waste Management

# Time Simulation

# Logging & Docker Setup