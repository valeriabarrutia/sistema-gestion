import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Se agrega prepare_threshold=None para compatibilidad con el Pooler de Supabase en psycopg2
engine = create_engine(
    DATABASE_URL,
    connect_args={"prepare_threshold": None},
    pool_pre_ping=True,
    pool_recycle=300,
    pool_timeout=30
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

try:
    Base.metadata.create_all(bind=engine)
    print("Conexión con Supabase exitosa.")
except Exception as e:
    print(f"Error al conectar con Supabase: {e}")