import os
import requests
from bs4 import BeautifulSoup

RENDER_API_URL = "https://scrapping-hapag.onrender.com/save-tracking"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
BL_NUMBER = "HLCUNG12607EKZE0"

def scrape_with_zenrows():
    print(f"Rastreando el BL {BL_NUMBER} a través de ZenRows...")

    target_url = f"https://www.hapag-lloyd.com/en/online-business/track/track-by-booking-solution.html?blno={BL_NUMBER}"

    zenrows_api = "https://api.zenrows.com/v1/"
    params = {
        "apikey": ZENROWS_API_KEY,
        "url": target_url,
        "js_render": "true",
        "antibot": "true",
        "premium_proxy": "true"
    }

    # requests maneja automáticamente la codificación segura de la URL en params
    response = requests.get(zenrows_api, params=params)

    if response.status_code != 200:
        print(f"Error en ZenRows: Código {response.status_code} - {response.text}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    containers_data = []
    rows = soup.find_all("tr")

    for row in rows:
        cols = row.find_all(["td", "th"])
        if len(cols) >= 5:
            col_texts = [col.get_text(strip=True) for col in cols]

            if "Container No." in col_texts[1] or "Type" in col_texts[0]:
                continue

            container_no = " ".join(col_texts[1].split())

            if container_no and len(container_no) > 4:
                containers_data.append({
                    "type": col_texts[0],
                    "container_no": container_no,
                    "status": col_texts[2],
                    "date": col_texts[3],
                    "place_of_activity": col_texts[4]
                })

    payload = {
        "bl_number": BL_NUMBER,
        "total_containers": len(containers_data),
        "containers": containers_data,
        "location": "Actualizado vía GitHub Actions + ZenRows Prémium"
    }

    return payload

def send_to_render(data):
    if not data or not ADMIN_TOKEN:
        print("Faltan datos o token.")
        exit(1)

    headers = {
        "x-admin-token": ADMIN_TOKEN,
        "Content-Type": "application/json"
    }

    print(f"Enviando datos a Render...")
    response = requests.post(RENDER_API_URL, json=data, headers=headers)

    print(f"Código de respuesta de Render: {response.status_code}")
    response.raise_for_status()
    print("¡Datos sincronizados con Render con éxito!")

if __name__ == "__main__":
    extracted_data = scrape_with_zenrows()
    if extracted_data:
        send_to_render(extracted_data)