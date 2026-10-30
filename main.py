from fastapi import FastAPI, HTTPException, Header, Request
import os

app = FastAPI()

CONTAINER_DATA_CACHE = {}

ADMIN_SECRET_TOKEN = os.getenv("ADMIN_TOKEN")
if not ADMIN_SECRET_TOKEN:
    raise RuntimeError("La variable de entorno ADMIN_TOKEN no está configurada en el servidor.")

@app.get("/")
def home():
    return {"status": "API de Hapag-Lloyd funcionando correctamente"}

@app.post("/save-tracking")
async def save_tracking(request: Request, x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Token de autorización inválido.")

    try:
        data = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON inválido: {str(e)}")

    container_id = data.get("container_id")
    if not container_id:
        raise HTTPException(status_code=400, detail="Falta el campo container_id en el payload.")

    # Guardamos los datos recibidos en la caché en memoria
    CONTAINER_DATA_CACHE[container_id] = data
    return {"success": True, "message": f"Datos del contenedor {container_id} actualizados correctamente."}

@app.get("/track/{container_id}")
def get_container(container_id: str):
    if container_id in CONTAINER_DATA_CACHE:
        return CONTAINER_DATA_CACHE[container_id]
    raise HTTPException(
        status_code=404,
        detail="No hay datos recientes para este contenedor. Ejecute el scraper para actualizar."
    )