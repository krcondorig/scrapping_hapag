from fastapi import FastAPI, HTTPException, Header, Request
import os
import scraper

app = FastAPI()

# Caché en memoria para almacenar los datos del tracking
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

    # Identificamos el BL o contenedor principal enviado desde GitHub Actions
    identifier = data.get("bl_number") or data.get("container_id")
    if not identifier:
        raise HTTPException(status_code=400, detail="Falta el campo bl_number o container_id en el payload.")

    # Guardamos en caché en memoria
    CONTAINER_DATA_CACHE[identifier] = data
    return {"success": True, "message": f"Datos del registro {identifier} actualizados correctamente."}

@app.get("/track/{identifier}")
def get_container(identifier: str):
    identifier = identifier.strip()
    if not identifier or len(identifier) > 35 or not identifier.replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="El BL o booking number tiene un formato inválido.")

    try:
        return scraper.scrape_bl(identifier)
    except scraper.MissingZenRowsKey as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except scraper.ZenRowsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc