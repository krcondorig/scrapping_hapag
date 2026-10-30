import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

RENDER_API_URL = "https://scrapping-hapag.onrender.com/save-tracking"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
CONTAINER_ID = "HLCUNG12607EKZE0"

def scrape_with_zenrows():
    print(f"Rastreando la guía {CONTAINER_ID} a través de ZenRows...")

    # 1. Construimos la URL objetivo de Hapag-Lloyd
    raw_target_url = f"https://www.hapag-lloyd.com/en/online-business/track/track-by-booking-solution.html?blno={CONTAINER_ID}"

    # 2. Codificamos la URL para que los caracteres especiales y ?/& no rompan la petición a ZenRows
    encoded_target_url = quote(raw_target_url, safe="")

    zenrows_url = f"https://api.zenrows.com/v1/?apikey={ZENROWS_API_KEY}&url={encoded_target_url}&js_render=true&antibot=true&premium_proxy=true"

    response = requests.get(zenrows_url)

    if response.status_code != 200:
        print(f"Error en la API de ZenRows: Código {response.status_code} - {response.text}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Extraemos el estado o un indicador básico
    status_node = soup.select_one(".status-value") or soup.find("span", class_="highlight")
    status_text = status_node.get_text(strip=True) if status_node else "En tránsito / Rastreado con éxito"

    # Buscamos información de ETA de forma segura
    eta_text = "No disponible"
    for element in soup.find_all(string=True):
        if "ETA" in element or "Estimated" in element or "Arrival" in element:
            eta_text = element.strip()
            break

    return {
        "container_id": CONTAINER_ID,
        "status": status_text,
        "eta": eta_text,
        "location": "Actualizado vía GitHub Actions + ZenRows Prémium"
    }

def send_to_render(data):
    if not data or not ADMIN_TOKEN:
        print("Faltan datos o token.")
        return

    headers = {
        "x-admin-token": ADMIN_TOKEN,
        "Content-Type": "application/json"
    }

    response = requests.post(RENDER_API_URL, json=data, headers=headers)
    if response.status_code == 200:
        print("¡Datos detallados enviados y sincronizados con Render con éxito!")
    else:
        print(f"Error al enviar a Render: {response.status_code} - {response.text}")

if __name__ == "__main__":
    extracted_data = scrape_with_zenrows()
    if extracted_data:
        send_to_render(extracted_data)