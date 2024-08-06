from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

load_dotenv() 

password = os.environ.get("PASSWORD")
klekovaca = os.environ.get("POSTGRES_DB")
host = os.environ.get("HOST")
port= os.environ.get("PORT")
algorithm= os.environ.get("ALGORITHM")
access_token_expire_minutes= os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")
email = os.environ.get("EMAIL")
epassword= os.environ.get("EPASSWORD")
secret_key= os.environ.get("SECRET_KEY")

DATABASE_URL = f'postgresql+psycopg2://postgres:{password}@{host}:{port}/{klekovaca}'

engine = create_engine(DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session
    

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.environ.get("SECRET_KEY"), algorithm=os.environ.get("ALGORITHM"))
    return encoded_jwt