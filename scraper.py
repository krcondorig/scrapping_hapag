import os
import requests
from bs4 import BeautifulSoup

RENDER_API_URL = "https://scrapping-hapag.onrender.com/save-tracking"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
CONTAINER_ID = "HLCUNG12607EKZE0"

def scrape_with_zenrows():
    print(f"Rastreando la guía {CONTAINER_ID} a través de ZenRows...")

    target_url = f"https://www.hapag-lloyd.com/en/online-business/track/track-by-booking-solution.html?blno={CONTAINER_ID}"

    zenrows_url = "https://api.zenrows.com/v1/"
    params = {
        "apikey": ZENROWS_API_KEY,
        "url": target_url,
        "js_render": "true",
        "antibot": "true",
        "premium_proxy": "true"
    }

    response = requests.get(zenrows_url, params=params)

    if response.status_code != 200:
        print(f"Error en la API de ZenRows: Código {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Buscamos elementos comunes donde Hapag-Lloyd suele alojar detalles del tracking
    # (Puedes ajustar estos selectores inspeccionando el HTML si el sitio cambia)
    status_node = soup.select_one(".status-value") or soup.find("span", class_="highlight")
    status_text = status_node.get_text(strip=True) if status_node else "En tránsito"

    # Intentamos buscar bloques de texto o etiquetas que contengan información de fechas/ETA
    eta_text = "No disponible"
    for element in soup.find_all(text=True):
        if "ETA" in element or "Estimated" in element or "Arrival" in element:
            eta_text = element.strip()
            break

    # Estructuramos un JSON más completo
    return {
        "container_id": CONTAINER_ID,
        "status": status_text,
        "eta": eta_text,
        "location": "Actualizado vía GitHub Actions + ZenRows Prémium"
    }

def send_to_render(data):
    if not data or not ADMIN_TOKEN:
        return

    headers = {
        "x-admin-token": ADMIN_TOKEN,
        "Content-Type": "application/json"
    }

    response = requests.post(RENDER_API_URL, json=data, headers=headers)
    if response.status_code == 200:
        print("¡Datos detallados enviados y sincronizados con Render con éxito!")

if __name__ == "__main__":
    extracted_data = scrape_with_zenrows()
    if extracted_data:
        send_to_render(extracted_data)