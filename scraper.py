import os
import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

RENDER_API_URL = "https://scrapping-hapag.onrender.com/save-tracking"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
CONTAINER_ID = "HLCUNG12607EKZE0"

def scrape_hapag():
    print(f"Rastreando el contenedor {CONTAINER_ID}...")
    url = f"https://www.hapag-lloyd.com/es/online-business/tracing.html?searchTerm={CONTAINER_ID}"
    
    response = cffi_requests.get(url, impersonate="chrome")
    if response.status_code != 200:
        print(f"Error al raspar: Código {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    status_node = soup.select_one(".status-value") or soup.find("span", {"id": "container-status"})
    status_text = status_node.get_text(strip=True) if status_node else "En tránsito / Actualizado"
    
    return {
        "container_id": CONTAINER_ID,
        "status": status_text,
        "location": "Actualizado vía GitHub Actions"
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
    extracted_data = scrape_hapag()
    if extracted_data:
        send_to_render(extracted_data)