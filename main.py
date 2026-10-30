from fastapi import FastAPI, HTTPException, Header, Request
import os

app = FastAPI()
CONTAINER_DATA_CACHE = {}
ADMIN_SECRET_TOKEN = os.getenv("ADMIN_TOKEN")

@app.post("/save-tracking")
async def save_tracking(request: Request, x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido.")

    data = await request.json()
    container_id = data.get("container_id")
    if not container_id:
        raise HTTPException(status_code=400, detail="Falta container_id.")

    CONTAINER_DATA_CACHE[container_id] = data
    return {"success": True, "data_received": data}

@app.get("/track/{container_id}")
def get_container(container_id: str):
    if container_id in CONTAINER_DATA_CACHE:
        return CONTAINER_DATA_CACHE[container_id]
    raise HTTPException(status_code=404, detail="Contenedor no encontrado.")