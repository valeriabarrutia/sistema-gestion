from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

DB_FILE = "sistema.db"

# Inicialización de la base de datos SQLite
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Tabla Entidades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL,
            cuit TEXT DEFAULT '',
            email TEXT DEFAULT '',
            telefono TEXT DEFAULT '',
            direccion TEXT DEFAULT ''
        )
    ''')
    
    # Tabla Facturas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entidad_id INTEGER NOT NULL,
            entidad_nombre TEXT DEFAULT '',
            tipo_comprobante TEXT NOT NULL,
            numero TEXT NOT NULL,
            fecha TEXT NOT NULL,
            monto_neto REAL NOT NULL,
            alicuota_iva REAL NOT NULL,
            monto_iva REAL NOT NULL,
            monto_total REAL NOT NULL,
            concepto TEXT DEFAULT ''
        )
    ''')
    
    # Tabla Pagos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entidad_id INTEGER NOT NULL,
            entidad_nombre TEXT DEFAULT '',
            tipo_operacion TEXT NOT NULL,
            medio_pago TEXT NOT NULL,
            fecha TEXT NOT NULL,
            monto REAL NOT NULL,
            observaciones TEXT DEFAULT ''
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Modelos Pydantic
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
    tipo_operacion: str  # COBRO / PAGO
    medio_pago: str      # Efectivo, Transferencia, Cheque
    fecha: str
    monto: float
    observaciones: str = ""

# --- ENDPOINTS ENTIDADES ---
@app.get("/api/entidades")
def obtener_entidades():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entidades")
    filas = cursor.fetchall()
    conn.close()
    return [dict(f) for f in filas]

@app.post("/api/entidades")
def guardar_entidad(entidad: Entidad):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO entidades (nombre, tipo, cuit, email, telefono, direccion) VALUES (?, ?, ?, ?, ?, ?)",
        (entidad.nombre, entidad.tipo, entidad.cuit, entidad.email, entidad.telefono, entidad.direccion)
    )
    entidad_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    entidad_dict = entidad.dict()
    entidad_dict["id"] = entidad_id
    return entidad_dict

@app.delete("/api/entidades/{entidad_id}")
def eliminar_entidad(entidad_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entidades WHERE id = ?", (entidad_id,))
    filas_afectadas = cursor.rowcount
    conn.commit()
    conn.close()
    
    if filas_afectadas == 0:
        raise HTTPException(status_code=404, detail="Entidad no encontrada")
    return {"message": "Entidad eliminada"}

# --- ENDPOINTS FACTURACIÓN ---
@app.get("/api/facturas")
def obtener_facturas():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM facturas")
    filas = cursor.fetchall()
    conn.close()
    return [dict(f) for f in filas]

@app.post("/api/facturas")
def guardar_factura(factura: Factura):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO facturas 
           (entidad_id, entidad_nombre, tipo_comprobante, numero, fecha, monto_neto, alicuota_iva, monto_iva, monto_total, concepto) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (factura.entidad_id, factura.entidad_nombre, factura.tipo_comprobante, factura.numero, 
         factura.fecha, factura.monto_neto, factura.alicuota_iva, factura.monto_iva, factura.monto_total, factura.concepto)
    )
    factura_id = cursor.lastrowid
    conn.commit()
    conn.close()

    factura_dict = factura.dict()
    factura_dict["id"] = factura_id
    return factura_dict

@app.delete("/api/facturas/{factura_id}")
def eliminar_factura(factura_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM facturas WHERE id = ?", (factura_id,))
    filas_afectadas = cursor.rowcount
    conn.commit()
    conn.close()

    if filas_afectadas == 0:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return {"ok": True, "message": "Factura eliminada"}

# --- ENDPOINTS COBROS Y PAGOS ---
@app.get("/api/pagos")
def obtener_pagos():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pagos")
    filas = cursor.fetchall()
    conn.close()
    return [dict(f) for f in filas]

@app.post("/api/pagos")
def guardar_pago(pago: ComprobantePago):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO pagos 
           (entidad_id, entidad_nombre, tipo_operacion, medio_pago, fecha, monto, observaciones) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (pago.entidad_id, pago.entidad_nombre, pago.tipo_operacion, pago.medio_pago, pago.fecha, pago.monto, pago.observaciones)
    )
    pago_id = cursor.lastrowid
    conn.commit()
    conn.close()

    pago_dict = pago.dict()
    pago_dict["id"] = pago_id
    return pago_dict

# --- ENDPOINT ESTADO DE CUENTA ---
@app.get("/api/estado-cuenta/{entidad_id}")
def obtener_estado_cuenta(entidad_id: int):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM facturas WHERE entidad_id = ?", (entidad_id,))
    facturas = [dict(f) for f in cursor.fetchall()]

    cursor.execute("SELECT * FROM pagos WHERE entidad_id = ?", (entidad_id,))
    pagos = [dict(p) for p in cursor.fetchall()]
    conn.close()

    movimientos = []

    for fact in facturas:
        monto_total = fact.get("monto_total", 0.0)
        movimientos.append({
            "fecha": fact.get("fecha", ""),
            "comprobante": f"{fact.get('tipo_comprobante', '')} N° {fact.get('numero', '')}",
            "concepto": fact.get("concepto", ""),
            "debe": monto_total,
            "haber": 0.0
        })

    for p in pagos:
        es_cobro = p.get("tipo_operacion") == "COBRO"
        movimientos.append({
            "fecha": p.get("fecha", ""),
            "comprobante": f"Recibo ({p.get('tipo_operacion', '')} - {p.get('medio_pago', '')})",
            "concepto": p.get("observaciones", ""),
            "debe": 0.0 if es_cobro else p.get("monto", 0.0),
            "haber": p.get("monto", 0.0) if es_cobro else 0.0
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