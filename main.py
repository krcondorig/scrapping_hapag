import os
from bs4 import BeautifulSoup
from curl_cffi import requests
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

app = FastAPI()

# 1. Variables globales en memoria (inicializadas con las de entorno de Render)
CURRENT_CF_CLEARANCE = os.getenv("CF_CLEARANCE", "")
CURRENT_USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
)

# Token secreto para que nadie más pueda actualizar tus cookies (cámbialo por uno tuyo)
ADMIN_SECRET_TOKEN = os.getenv("ADMIN_SECRET_TOKEN", "mi_token_secreto_123")

class CookieUpdate(BaseModel):
    cf_clearance: str
    user_agent: str = None


@app.get("/")
def home():
    return {"status": "API de Hapag-Lloyd con actualización dinámica activa"}


@app.post("/update-cookie")
def update_cookie(data: CookieUpdate, x_admin_token: str = Header(None)):
    global CURRENT_CF_CLEARANCE, CURRENT_USER_AGENT
    
    # Validar token de seguridad por seguridad
    if x_admin_token != ADMIN_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Token de autorización inválido.")
    
    # Actualizar en memoria
    CURRENT_CF_CLEARANCE = data.cf_clearance
    if data.user_agent:
        CURRENT_USER_AGENT = data.user_agent
        
    return {
        "success": True,
        "message": "¡Cookie cf_clearance actualizada dinámicamente en memoria con éxito!"
    }


@app.get("/track/{container_id}")
def track_container(container_id: str):
    headers = {
        "User-Agent": CURRENT_USER_AGENT,
        "Referer": "https://www.hapag-lloyd.com/es/online-business/tracing.html",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    cookies = {"cf_clearance": CURRENT_CF_CLEARANCE}

    try:
        url = f"https://www.hapag-lloyd.com/es/online-business/tracing.html?searchTerm={container_id}"

        response = requests.get(
            url, headers=headers, cookies=cookies, impersonate="chrome"
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=403,
                detail="Cloudflare bloqueó la petición o la cookie expiró.",
            )

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extracción básica de ejemplo (ajusta según la web real)
        status_node = soup.select_one(".status-value") or soup.find("span", {"id": "container-status"})
        estado = status_node.get_text(strip=True) if status_node else "Información procesada correctamente"

        return {
            "container": container_id,
            "status": estado,
            "success": True,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))