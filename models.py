from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Float, Date, Time, ForeignKey, DateTime, BigInteger
from geoalchemy2 import Geometry
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String)
    phone = Column(BigInteger)
    is_admin = Column(Boolean)
    email_alert = Column(Boolean)
    sms_alert = Column(Boolean)
    date = Column(DateTime(timezone=True), server_default=func.now())
    
    parcels = relationship("Parcel", back_populates="owners")

class Parcel(Base):
    __tablename__ = "parcels"
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    crop_id = Column(Integer, ForeignKey('crops.id', ondelete='CASCADE'), nullable=False)
    name = Column(String)
    location = Column(Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True))
    sow_complete = Column(Boolean, default=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    
    owners = relationship("User", back_populates="parcels")
    devices = relationship("Sensor", back_populates="sensor_locations")
    alerts = relationship("Alert", back_populates="parcel_alert")

class Sensor(Base):
    __tablename__ = "sensors"
    
    id = Column(Integer, primary_key=True)
    parcel_id = Column(Integer, ForeignKey('parcels.id', ondelete="CASCADE"), nullable=False)
    sensor_id = Column(Integer, unique=True, nullable=False)
    config = Column(Integer)
    location = Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True))
    date = Column(DateTime(timezone=True), server_default=func.now())
    
    sensor_locations = relationship("Parcel", back_populates="devices")
    measurement = relationship("SensorData", back_populates="data")

class Crop(Base):
    __tablename__ = "crops"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    temp_min = Column(Float)
    temp_max = Column(Float)
    moist_min = Column(Float)
    moist_max = Column(Float)
    altitude = Column(String)
    variety = Column(String)
    clima = Column(String)
    season_start = Column(DateTime(timezone=True))
    season_end = Column(DateTime(timezone=True))
    distance = Column(String)
    density = Column(String)
    depth = Column(String)
    norm = Column(String)
    method = Column(String)
    min_temp = Column(String)
    fertilization = Column(String)
    watering = Column(String)
    care = Column(String)
    protection = Column(String)
    utilization = Column(String)
    harvest = Column(String)
    storage = Column(String)
    crop_yield = Column(String)
    rain = Column(Float)
    date = Column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True)
    parcel_id = Column(Integer, ForeignKey('parcels.id', ondelete="CASCADE"), nullable=False)
    text = Column(String)
    is_active = Column(Boolean)
    date = Column(DateTime(timezone=True), server_default=func.now())
    
    parcel_alert = relationship("Parcel", back_populates="alerts")

class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True)
    sensor_id = Column(Integer, ForeignKey('sensors.sensor_id'), nullable=False)
    temperature = Column(Float)
    moisture = Column(Float)
    date = Column(Date)
    time = Column(Time)
    battery = Column(Float)
    status = Column(Integer)
    server_time_date = Column(DateTime(timezone=True), server_default=func.now())
    
    data = relationship("Sensor", back_populates="measurement")
    