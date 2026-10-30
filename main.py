import os
from bs4 import BeautifulSoup
from curl_cffi import requests
from fastapi import FastAPI, HTTPException

app = FastAPI()

CF_CLEARANCE = os.getenv("CF_CLEARANCE", "")
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
)


@app.get("/")
def home():
  return {"status": "API de Hapag-Lloyd con BeautifulSoup Activa"}


@app.get("/track/{container_id}")
def track_container(container_id: str):
  headers = {
      "User-Agent": USER_AGENT,
      "Referer": "https://www.hapag-lloyd.com/es/online-business/tracing.html",
      "Accept": (
          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
      ),
  }

  cookies = {"cf_clearance": CF_CLEARANCE}

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

    # Inicializar BeautifulSoup para parsear el HTML recibido
    soup = BeautifulSoup(response.text, "html.parser")

    # =========================================================================
    # 🔍 ZONA DE EXTRACCIÓN (Ajusta estos selectores según el HTML de Hapag-Lloyd)
    # =========================================================================
    
    # Ejemplo: Buscando un contenedor por clase o ID típico de su frontend
    status_node = soup.select_one(".status-value") or soup.find(
        "span", {"id": "container-status"}
    )
    location_node = soup.select_one(".location-value") or soup.find(
        "div", {"class": "current-location"}
    )

    # Extraer el texto de manera segura (si el nodo existe)
    estado = status_node.get_text(strip=True) if status_node else "No disponible"
    ubicacion = (
        location_node.get_text(strip=True)
        if location_node
        else "No disponible"
    )

    # Si quieres hacer una comprobación general por si no encontró nada
    if not status_node and not location_node:
      # Como plan B, podemos buscar si aparece algún mensaje de error de Cloudflare o de la naviera
      error_msg = soup.select_one(".error-message")
      if error_msg:
        estado = f"Error en la web de la naviera: {error_msg.get_text(strip=True)}"
      else:
        estado = "Estructura HTML modificada o contenedor no encontrado."

    return {
        "container": container_id,
        "status": estado,
        "location": ubicacion,
        "success": True,
    }

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))