import os
import requests
from bs4 import BeautifulSoup

RENDER_API_URL = "https://scrapping-hapag.onrender.com/save-tracking"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
BL_NUMBER = "HLCUNG12607EKZE0"

def get_zenrows_soup(target_url):
    zenrows_api = "https://api.zenrows.com/v1/"
    params = {
        "apikey": ZENROWS_API_KEY,
        "url": target_url,
        "js_render": "true",
        "antibot": "true",
        "premium_proxy": "true"
    }
    response = requests.get(zenrows_api, params=params)
    if response.status_code != 200:
        print(f"Error en ZenRows para {target_url}: Código {response.status_code}")
        return None
    return BeautifulSoup(response.text, "html.parser")

def scrape_container_movements(container_no):
    print(f"Extrayendo movimientos para el contenedor: {container_no}...")
    target_url = f"https://www.hapag-lloyd.com/en/online-business/track/track-by-container-solution.html?container={container_no}"
    soup = get_zenrows_soup(target_url)
    if not soup:
        return []

    movements = []
    rows = soup.find_all("tr")
    for row in rows:
        cols = row.find_all(["td", "th"])
        if len(cols) >= 6:
            col_texts = [col.get_text(strip=True) for col in cols]
            joined = " ".join(col_texts)
            if "Status" in joined or "Place of Activity" in joined or "Please enter" in joined:
                continue
            movements.append({
                "status": col_texts[0],
                "place_of_activity": col_texts[1],
                "date": col_texts[2],
                "time": col_texts[3],
                "transport": col_texts[4],
                "voyage_no": col_texts[5]
            })
    return movements

def scrape_with_zenrows():
    print(f"Rastreando el BL principal: {BL_NUMBER}...")
    target_url = f"https://www.hapag-lloyd.com/en/online-business/track/track-by-booking-solution.html?blno={BL_NUMBER}"

    soup = get_zenrows_soup(target_url)
    if not soup:
        return None

    containers_data = []
    rows = soup.find_all("tr")

    seen_containers = set()

    for row in rows:
        cols = row.find_all(["td", "th"])
        if len(cols) >= 5:
            col_texts = [col.get_text(strip=True) for col in cols]
            joined_text = " ".join(col_texts)

            # Ignoramos la cabecera y textos de ayuda del formulario
            if "Please enter" in joined_text or "Booking No." in joined_text or "Container No." in joined_text or "Type" in joined_text:
                continue

            # Limpiamos el número de contenedor (columna 1 típicamente)
            container_no = " ".join(col_texts[1].split())

            # Validamos que tenga un formato de contenedor válido (ej. letras y números, longitud >= 6)
            if container_no and len(container_no) >= 6 and container_no not in seen_containers:
                seen_containers.add(container_no)

                # Obtenemos los movimientos detallados de este contenedor
                movements = scrape_container_movements(container_no)

                containers_data.append({
                    "type": col_texts[0],
                    "container_no": container_no,
                    "status_summary": col_texts[2],
                    "date_summary": col_texts[3],
                    "place_summary": col_texts[4],
                    "detailed_movements": movements
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

    print("Enviando estructura completa a Render...")
    response = requests.post(RENDER_API_URL, json=data, headers=headers)
    print(f"Código de respuesta de Render: {response.status_code}")
    response.raise_for_status()
    print("¡Datos sincronizados con Render con éxito!")

if __name__ == "__main__":
    extracted_data = scrape_with_zenrows()
    if extracted_data:
        send_to_render(extracted_data)