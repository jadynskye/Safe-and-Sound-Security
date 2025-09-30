# backend/app.py

# Importing all FastAPI tools needed
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
from .db import Base, engine, SessionLocal
from .models import User, Device
import asyncio

# Creating Safe&Sound FastAPI App
app = FastAPI(title="Safe&Sound API")

# Registers CORS → lets our HTML/JS talk to this API without being blocked
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow everything for now (dev only)
    allow_methods=["*"],   # allow all request types (GET, POST, etc.)
    allow_headers=["*"],   # allow all headers
)

# Function that makes a database session every time needed
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Creates tables in database if they don't exist 
Base.metadata.create_all(bind=engine)

# function 'seed' puts the demo data in the database if it’s empty
def seed(db: Session):
    # if no user with this email yet, add demo user
    if not db.query(User).filter(User.email == "demo@safesound.com").first():
        db.add(User(email="demo@safesound.com", password="password"))
    # add demo devices if none exist
    if db.query(Device).count() == 0:
        demo = [
            Device(name="Living Light", room="living", kind="bulb", online=True),
            Device(name="Thermostat",   room="living", kind="thermostat", online=False),
            Device(name="Door Sensor",  room="entrance", kind="sensor", online=True),
            Device(name="Camera",       room="entrance", kind="camera", online=True),
            Device(name="Smoke Alarm",  room="kitchen", kind="sensor", online=True),
            Device(name="Motion Sensor",room="hallway", kind="sensor", online=True),
        ]
        db.add_all(demo)
    db.commit()

# run the seed once when the app starts
with SessionLocal() as _db:
    seed(_db)

# Request/ response models → these shape the data we send/receive

class LoginIn(BaseModel):   # info coming in when logging in
    email: str
    password: str

class LoginOut(BaseModel):  # info going back after login
    ok: bool
    token: str

class DeviceOut(BaseModel): # info we send about devices
    id: int
    name: str
    room: str
    kind: str
    online: bool

class DevicePatchIn(BaseModel):  # info for updating device state
    online: bool

# test endpoint aka tells if API is alive
@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.utcnow().isoformat()}

# Login expected by login.js (frontend)
@app.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    # look for user by email
    user = db.query(User).filter(User.email == payload.email).first()
    # if not found or wrong password → error
    if not user or user.password != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # fake token for demo (not real security)
    token = f"demo-{user.id or 1}"
    return {"ok": True, "token": token}

# Get all devices → used by dashboard.js
@app.get("/devices", response_model=List[DeviceOut])
def list_devices(db: Session = Depends(get_db)):
    rows = db.query(Device).all()  # don’t need order_by, simpler
    return [
        DeviceOut(id=d.id, name=d.name, room=d.room, kind=d.kind, online=d.online)
        for d in rows
    ]

# Update device’s online/offline state
@app.patch("/devices/{device_id}")
def update_device(device_id: int, body: DevicePatchIn, db: Session = Depends(get_db)):
    d = db.query(Device).filter(Device.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")
    # update the device and save
    d.online = body.online
    db.commit()
    # Notify WebSocket about it (tell everyone connected)
    for sock in list(CONNECTIONS):
        try:
            asyncio.create_task(sock.send_json(
                {"type": "device", "id": d.id, "online": d.online}
            ))
        except Exception:
            pass
    return {"ok": True}

# List of people connected over WebSocket atm
CONNECTIONS: List[WebSocket] = []

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    CONNECTIONS.append(ws)
    try:
        while True:
            # wait for a message from the client
            data = await ws.receive_json()
            # send the same message to everyone connected
            for sock in list(CONNECTIONS):
                try:
                    await sock.send_json(data)
                except Exception:
                    pass
    except WebSocketDisconnect:
        pass
    finally:
        # clean up when someone disconnects!
        if ws in CONNECTIONS:
            CONNECTIONS.remove(ws)