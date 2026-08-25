from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# ⚠️ PONÉ ACÁ TU CONTRASEÑA REAL DE SUPABASE
DATABASE_URL = "postgresql://postgres:VEB-2026*2050@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- TABLAS EN POSTGRESQL ---
class EntidadDB(Base):
    __tablename__ = "entidades"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    cuit = Column(String, default="")
    email = Column(String, default="")
    telefono = Column(String, default="")
    direccion = Column(String, default="")

class FacturaDB(Base):
    __tablename__ = "facturas"
    id = Column(Integer, primary_key=True, index=True)
    entidad_id = Column(Integer, nullable=False)
    entidad_nombre = Column(String, default="")
    tipo_comprobante = Column(String, nullable=False)
    numero = Column(String, nullable=False)
    fecha = Column(String, nullable=False)
    monto_neto = Column(Float, nullable=False)
    alicuota_iva = Column(Float, nullable=False)
    monto_iva = Column(Float, nullable=False)
    monto_total = Column(Float, nullable=False)
    concepto = Column(String, default="")

class PagoDB(Base):
    __tablename__ = "pagos"
    id = Column(Integer, primary_key=True, index=True)
    entidad_id = Column(Integer, nullable=False)
    entidad_nombre = Column(String, default="")
    tipo_operacion = Column(String, nullable=False)
    medio_pago = Column(String, nullable=False)
    fecha = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    observaciones = Column(String, default="")

# Crear automáticamente las tablas en Supabase
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- MODELOS PYDANTIC ---
class Entidad(BaseModel):
    id: int | None = None
    nombre: str
    tipo: str
    cuit: str = ""
    email: str = ""
    telefono: str = ""
    direccion: str = ""

class Factura(BaseModel):
    id: int | None = None
    entidad_id: int
    entidad_nombre: str = ""
    tipo_comprobante: str
    numero: str
    fecha: str
    monto_neto: float
    alicuota_iva: float
    monto_iva: float
    monto_total: float
    concepto: str = ""

class ComprobantePago(BaseModel):
    id: int | None = None
    entidad_id: int
    entidad_nombre: str = ""
    tipo_operacion: str
    medio_pago: str
    fecha: str
    monto: float
    observaciones: str = ""

# --- ENDPOINTS ENTIDADES ---
@app.get("/api/entidades")
def obtener_entidades():
    db = SessionLocal()
    entidades = db.query(EntidadDB).all()
    db.close()
    return [
        {
            "id": e.id, "nombre": e.nombre, "tipo": e.tipo,
            "cuit": e.cuit, "email": e.email, "telefono": e.telefono, "direccion": e.direccion
        } for e in entidades
    ]

@app.post("/api/entidades")
def guardar_entidad(entidad: Entidad):
    db = SessionLocal()
    db_entidad = EntidadDB(**entidad.dict(exclude={"id"}))
    db.add(db_entidad)
    db.commit()
    db.refresh(db_entidad)
    db.close()
    return db_entidad

@app.delete("/api/entidades/{entidad_id}")
def eliminar_entidad(entidad_id: int):
    db = SessionLocal()
    entidad = db.query(EntidadDB).filter(EntidadDB.id == entidad_id).first()
    if not entidad:
        db.close()
        raise HTTPException(status_code=404, detail="Entidad no encontrada")
    db.delete(entidad)
    db.commit()
    db.close()
    return {"message": "Entidad eliminada"}

# --- ENDPOINTS FACTURACIÓN ---
@app.get("/api/facturas")
def obtener_facturas():
    db = SessionLocal()
    facturas = db.query(FacturaDB).all()
    db.close()
    return [
        {
            "id": f.id, "entidad_id": f.entidad_id, "entidad_nombre": f.entidad_nombre,
            "tipo_comprobante": f.tipo_comprobante, "numero": f.numero, "fecha": f.fecha,
            "monto_neto": f.monto_neto, "alicuota_iva": f.alicuota_iva,
            "monto_iva": f.monto_iva, "monto_total": f.monto_total, "concepto": f.concepto
        } for f in facturas
    ]

@app.post("/api/facturas")
def guardar_factura(factura: Factura):
    db = SessionLocal()
    db_factura = FacturaDB(**factura.dict(exclude={"id"}))
    db.add(db_factura)
    db.commit()
    db.refresh(db_factura)
    db.close()
    return db_factura

@app.delete("/api/facturas/{factura_id}")
def eliminar_factura(factura_id: int):
    db = SessionLocal()
    factura = db.query(FacturaDB).filter(FacturaDB.id == factura_id).first()
    if not factura:
        db.close()
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    db.delete(factura)
    db.commit()
    db.close()
    return {"ok": True, "message": "Factura eliminada"}

# --- ENDPOINTS COBROS Y PAGOS ---
@app.get("/api/pagos")
def obtener_pagos():
    db = SessionLocal()
    pagos = db.query(PagoDB).all()
    db.close()
    return [
        {
            "id": p.id, "entidad_id": p.entidad_id, "entidad_nombre": p.entidad_nombre,
            "tipo_operacion": p.tipo_operacion, "medio_pago": p.medio_pago,
            "fecha": p.fecha, "monto": p.monto, "observaciones": p.observaciones
        } for p in pagos
    ]

@app.post("/api/pagos")
def guardar_pago(pago: ComprobantePago):
    db = SessionLocal()
    db_pago = PagoDB(**pago.dict(exclude={"id"}))
    db.add(db_pago)
    db.commit()
    db.refresh(db_pago)
    db.close()
    return db_pago

# --- ENDPOINT ESTADO DE CUENTA ---
@app.get("/api/estado-cuenta/{entidad_id}")
def obtener_estado_cuenta(entidad_id: int):
    db = SessionLocal()
    facturas = db.query(FacturaDB).filter(FacturaDB.entidad_id == entidad_id).all()
    pagos = db.query(PagoDB).filter(PagoDB.entidad_id == entidad_id).all()
    db.close()

    movimientos = []

    for fact in facturas:
        movimientos.append({
            "fecha": fact.fecha or "",
            "comprobante": f"{fact.tipo_comprobante} N° {fact.numero}",
            "concepto": fact.concepto or "",
            "debe": fact.monto_total,
            "haber": 0.0
        })

    for p in pagos:
        es_cobro = p.tipo_operacion == "COBRO"
        movimientos.append({
            "fecha": p.fecha or "",
            "comprobante": f"Recibo ({p.tipo_operacion} - {p.medio_pago})",
            "concepto": p.observaciones or "",
            "debe": 0.0 if es_cobro else p.monto,
            "haber": p.monto if es_cobro else 0.0
        })

    movimientos.sort(key=lambda x: x["fecha"])

    saldo = 0.0
    for mov in movimientos:
        saldo += mov["debe"] - mov["haber"]
        mov["saldo"] = saldo

    return movimientos

# --- RUTA PRINCIPAL ---
@app.get("/")
def home():
    return FileResponse("index.html")