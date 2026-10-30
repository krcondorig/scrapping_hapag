import os
import requests
from bs4 import BeautifulSoup

RENDER_API_URL = "https://scrapping-hapag.onrender.com/save-tracking"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
CONTAINER_ID = "HLCUNG12607EKZE0"

def scrape_with_zenrows():
    print(f"Rastreando la guía {CONTAINER_ID} a través de ZenRows...")

    # URL exacta proporcionada con el parámetro blno
    target_url = f"https://www.hapag-lloyd.com/en/online-business/track/track-by-booking-solution.html?blno={CONTAINER_ID}"

    zenrows_url = "https://api.zenrows.com/v1/"
    params = {
        "apikey": ZENROWS_API_KEY,
        "url": target_url,
        "js_render": "true",       # Renderiza la SPA con JavaScript
        "antibot": "true",         # Salta Cloudflare
        "premium_proxy": "true"    # Proxy prémium requerido por seguridad
    }

    response = requests.get(zenrows_url, params=params)

    if response.status_code != 200:
        print(f"Error en la API de ZenRows: Código {response.status_code} - {response.text}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Intentamos extraer el estado o un resumen de la página cargada
    status_node = soup.select_one(".status-value") or soup.find("span", {"id": "container-status"})
    status_text = status_node.get_text(strip=True) if status_node else "Información de rastreo obtenida vía ZenRows"

    return {
        "container_id": CONTAINER_ID,
        "status": status_text,
        "location": "Actualizado vía GitHub Actions + ZenRows Prémium"
    }

def send_to_render(data):
    if not data or not ADMIN_TOKEN:
        print("Faltan datos para enviar o el token no está configurado.")
        return

    headers = {
        "x-admin-token": ADMIN_TOKEN,
        "Content-Type": "application/json"
    }

    response = requests.post(RENDER_API_URL, json=data, headers=headers)
    if response.status_code == 200:
        print("¡Datos enviados y sincronizados con Render con éxito!")
    else:
        print(f"Error al enviar a Render: {response.status_code} - {response.text}")

if __name__ == "__main__":
    extracted_data = scrape_with_zenrows()
    if extracted_data:
        send_to_render(extracted_data)