# backend/models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .db import Base

# table for users (login info)
class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True, index=True)
    email    = Column(String, unique=True, index=True)
    password = Column(String)  # simple demo only

# table for devices in the smart home
class Device(Base):
    __tablename__ = "devices"
    id       = Column(Integer, primary_key=True, index=True)
    name     = Column(String)
    room     = Column(String)     
    kind     = Column(String)     
    online   = Column(Boolean, default=True)


# table for schedules (when devices should do stuff)
class Schedule(Base):
    __tablename__ = "schedules"
    id        = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    action    = Column(String)    
    when_utc  = Column(DateTime)  