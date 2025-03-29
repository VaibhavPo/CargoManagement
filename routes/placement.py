from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

router = APIRouter(prefix="/api/placement")

# Define request models
class Item(BaseModel):
    itemId: str
    name: str
    width: int
    depth: int
    height: int
    priority: int = Field(ge=1, le=100, description="Priority must be between 1 and 100")
    expiryDate: str  # ISO format "YYYY-MM-DDTHH:MM:SSZ"
    usageLimit: int
    preferredZone: str

    def parsed_expiry(self):
        try:
            return datetime.strptime(self.expiryDate, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid expiry date format: {self.expiryDate}")

class Container(BaseModel):
    containerId: str
    zone: str
    width: int
    depth: int
    height: int

class PlacementRequest(BaseModel):
    items: List[Item]
    containers: List[Container]

@router.post("/")
def recommend_placement(request: PlacementRequest):
    placements = []
    rearrangements = []
    
    # Sort items by priority (descending) and expiry date (earliest first)
    try:
        sorted_items = sorted(request.items, key=lambda x: (-x.priority, x.parsed_expiry()))
    except HTTPException as e:
        return {"success": False, "error": str(e.detail)}

    container_space = {c.containerId: {"width": c.width, "depth": c.depth, "height": c.height} for c in request.containers}

    for item in sorted_items:
        placed = False
        best_fit_container = None
        best_fit_waste = float("inf")  # Minimize wasted space
        
        for container in request.containers:
            if item.preferredZone == container.zone:
                remaining_space = (
                    (container.width - item.width) * (container.depth - item.depth) * (container.height - item.height)
                )
                if remaining_space >= 0 and remaining_space < best_fit_waste:
                    best_fit_container = container
                    best_fit_waste = remaining_space

        if best_fit_container:
            placements.append({
                "itemId": item.itemId,
                "containerId": best_fit_container.containerId,
                "position": {
                    "startCoordinates": {"width": 0, "depth": 0, "height": 0},
                    "endCoordinates": {"width": item.width, "depth": item.depth, "height": item.height}
                }
            })
            container_space[best_fit_container.containerId]["width"] -= item.width
            container_space[best_fit_container.containerId]["depth"] -= item.depth
            container_space[best_fit_container.containerId]["height"] -= item.height
            placed = True
        
        if not placed:
            rearrangements.append({
                "step": len(rearrangements) + 1,
                "action": "rearrange",  # Try moving items
                "itemId": item.itemId,
                "suggestedContainers": [
                    {"containerId": c.containerId, "zone": c.zone} for c in request.containers if c.zone != item.preferredZone
                ]
            })

    return {
        "success": True,
        "placements": placements,
        "rearrangements": rearrangements
    }
