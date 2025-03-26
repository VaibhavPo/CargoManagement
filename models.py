from pydantic import BaseModel
from typing import List

class Item(BaseModel):
    itemId: str
    name: str
    width: int
    depth: int
    height: int
    priority: int
    expiryDate: str
    usageLimit: int
    preferredZone: str

class Container(BaseModel):
    containerId: str
    zone: str
    width: int
    depth: int
    height: int

class PlacementRequest(BaseModel):
    items: List[Item]
    containers: List[Container]
