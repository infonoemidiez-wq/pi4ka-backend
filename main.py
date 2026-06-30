from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv
import os

# ── Configuración ──────────────────────────────────────────────
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME   = os.getenv("DB_NAME", "pi4kaDB")

app = FastAPI(title="PI4KA España API")

# Permite que el HTML llame a esta API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Conexión a MongoDB Atlas ───────────────────────────────────
@app.on_event("startup")
async def conectar_db():
    app.client = AsyncIOMotorClient(MONGO_URI)
    app.db     = app.client[DB_NAME]
    print(f"✅ Conectado a MongoDB Atlas / base de datos: {DB_NAME}")

@app.on_event("shutdown")
async def cerrar_db():
    app.client.close()

# ── Modelo de datos ────────────────────────────────────────────
class Caso(BaseModel):
    familia:          str
    ciudad:           str
    anio_diagnostico: int
    nombre_nino:      str
    historia:         str
    publicado:        bool = False

# ── Función auxiliar ───────────────────────────────────────────
def caso_a_dict(caso) -> dict:
    caso["id"] = str(caso["_id"])
    del caso["_id"]
    return caso

# ── RUTAS ──────────────────────────────────────────────────────

@app.get("/")
async def raiz():
    return {"mensaje": "API PI4KA España funcionando correctamente 🧬"}

@app.get("/casos")
async def obtener_casos_publicados():
    casos = []
    cursor = app.db.casos.find({"publicado": True})
    async for caso in cursor:
        casos.append(caso_a_dict(caso))
    return casos

@app.get("/casos/todos")
async def obtener_todos_los_casos():
    casos = []
    cursor = app.db.casos.find()
    async for caso in cursor:
        casos.append(caso_a_dict(caso))
    return casos

@app.post("/casos", status_code=201)
async def crear_caso(caso: Caso):
    resultado = await app.db.casos.insert_one(caso.dict())
    return {"mensaje": "Caso creado correctamente", "id": str(resultado.inserted_id)}

@app.patch("/casos/{caso_id}/publicar")
async def publicar_caso(caso_id: str, publicado: bool):
    resultado = await app.db.casos.update_one(
        {"_id": ObjectId(caso_id)},
        {"$set": {"publicado": publicado}}
    )
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    estado = "publicado" if publicado else "ocultado"
    return {"mensaje": f"Caso {estado} correctamente"}

@app.put("/casos/{caso_id}")
async def editar_caso(caso_id: str, caso: Caso):
    resultado = await app.db.casos.update_one(
        {"_id": ObjectId(caso_id)},
        {"$set": caso.dict()}
    )
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    return {"mensaje": "Caso actualizado correctamente"}

@app.delete("/casos/{caso_id}")
async def eliminar_caso(caso_id: str):
    resultado = await app.db.casos.delete_one({"_id": ObjectId(caso_id)})
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    return {"mensaje": "Caso eliminado correctamente"}
