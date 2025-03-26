# main.py
from fastapi import FastAPI
from database import init_db
from routes import placement, retrieval, waste_management, simulation, logs

app = FastAPI()

init_db()

app.include_router(placement.router)
app.include_router(retrieval.router)
app.include_router(waste_management.router)
app.include_router(simulation.router)
app.include_router(logs.router)

# uvicorn main:app --host 127.0.0.1 --port 8000 --reload

