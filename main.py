from fastapi import FastAPI, HTTPException, Header
import os

app = FastAPI()

CONTAINER_DATA_CACHE = {}

# Obligatorio: Si no hay variable de entorno, lanza un error de configuración
ADMIN_SECRET_TOKEN = os.getenv("ADMIN_TOKEN")
if not ADMIN_SECRET_TOKEN:
    raise RuntimeError("La variable de entorno ADMIN_TOKEN no está configurada en el servidor.")

@app.get("/")
def home():
    return {"status": "API de Hapag-Lloyd funcionando correctamente"}

@app.post("/save-tracking")
def save_tracking(data: dict, x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Token de autorización inválido.")
    
    container_id = data.get("container_id")
    if not container_id:
        raise HTTPException(status_code=400, detail="Falta el container_id en el payload.")
        
    CONTAINER_DATA_CACHE[container_id] = data
    return {"success": true, "message": f"Datos del contenedor {container_id} actualizados."}

@app.get("/track/{container_id}")
def get_container(container_id: str):
    if container_id in CONTAINER_DATA_CACHE:
        return CONTAINER_DATA_CACHE[container_id]
    raise HTTPException(
        status_code=404, 
        detail="No hay datos recientes para este contenedor. Ejecute el scraper para actualizar."
    )