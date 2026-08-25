from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import os

app = FastAPI()

DB_FILE = "datos.json"
FACTURAS_FILE = "facturas.json"
PAGOS_FILE = "pagos.json"

# Inicialización de archivos JSON
for archivo in [DB_FILE, FACTURAS_FILE, PAGOS_FILE]:
    if not os.path.exists(archivo):
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump([], f)

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
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/entidades")
def guardar_entidad(entidad: Entidad):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        datos = json.load(f)
    entidad_dict = entidad.dict()
    entidad_dict["id"] = len(datos) + 1
    datos.append(entidad_dict)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
    return entidad_dict

@app.delete("/api/entidades/{entidad_id}")
def eliminar_entidad(entidad_id: int):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        datos = json.load(f)
    nuevos_datos = [e for e in datos if e.get("id") != entidad_id]
    if len(datos) == len(nuevos_datos):
        raise HTTPException(status_code=404, detail="Entidad no encontrada")
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(nuevos_datos, f, ensure_ascii=False, indent=4)
    return {"message": "Entidad eliminada"}

# --- ENDPOINTS FACTURACIÓN ---
@app.get("/api/facturas")
def obtener_facturas():
    with open(FACTURAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/facturas")
def guardar_factura(factura: Factura):
    with open(FACTURAS_FILE, "r", encoding="utf-8") as f:
        datos = json.load(f)
    factura_dict = factura.dict()
    factura_dict["id"] = len(datos) + 1
    datos.append(factura_dict)
    with open(FACTURAS_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
    return factura_dict

@app.delete("/api/facturas/{factura_id}")
def eliminar_factura(factura_id: int):
    with open(FACTURAS_FILE, "r", encoding="utf-8") as f:
        datos = json.load(f)
    nuevos_datos = [f for f in datos if f.get("id") != factura_id]
    if len(datos) == len(nuevos_datos):
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    with open(FACTURAS_FILE, "w", encoding="utf-8") as f:
        json.dump(nuevos_datos, f, ensure_ascii=False, indent=4)
    return {"ok": True, "message": "Factura eliminada"}

# --- ENDPOINTS COBROS Y PAGOS ---
@app.get("/api/pagos")
def obtener_pagos():
    with open(PAGOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/pagos")
def guardar_pago(pago: ComprobantePago):
    with open(PAGOS_FILE, "r", encoding="utf-8") as f:
        datos = json.load(f)
    pago_dict = pago.dict()
    pago_dict["id"] = len(datos) + 1
    datos.append(pago_dict)
    with open(PAGOS_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
    return pago_dict

# --- ENDPOINT ESTADO DE CUENTA ---
@app.get("/api/estado-cuenta/{entidad_id}")
def obtener_estado_cuenta(entidad_id: int):
    with open(FACTURAS_FILE, "r", encoding="utf-8") as f:
        facturas = json.load(f)
    with open(PAGOS_FILE, "r", encoding="utf-8") as f:
        pagos = json.load(f)

    movimientos = []

    # Filtrar facturas de la entidad
    for fact in facturas:
        if fact.get("entidad_id") == entidad_id:
            monto_total = fact.get("monto_total", fact.get("monto", 0))
            movimientos.append({
                "fecha": fact.get("fecha", ""),
                "comprobante": f"{fact.get('tipo_comprobante', '')} N° {fact.get('numero', '')}",
                "concepto": fact.get("concepto", ""),
                "debe": monto_total,
                "haber": 0.0
            })

    # Filtrar cobros/pagos de la entidad
    for p in pagos:
        if p.get("entidad_id") == entidad_id:
            es_cobro = p.get("tipo_operacion") == "COBRO"
            movimientos.append({
                "fecha": p.get("fecha", ""),
                "comprobante": f"Recibo ({p.get('tipo_operacion', '')} - {p.get('medio_pago', '')})",
                "concepto": p.get("observaciones", ""),
                "debe": 0.0 if es_cobro else p.get("monto", 0.0),
                "haber": p.get("monto", 0.0) if es_cobro else 0.0
            })

    # Ordenar por fecha
    movimientos.sort(key=lambda x: x["fecha"])

    # Calcular saldo acumulado
    saldo = 0.0
    for mov in movimientos:
        saldo += mov["debe"] - mov["haber"]
        mov["saldo"] = saldo

    return movimientos

# --- RUTA PRINCIPAL ---
@app.get("/")
def home():
    return FileResponse("index.html")