import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

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

def scrape_container_details(container_no):
    print(f"Extrayendo detalles para el contenedor: {container_no}...")
    query = f"view=S8510&container={quote_plus(container_no).replace('+', '++')}"
    target_url = f"https://www.hapag-lloyd.com/en/online-business/track/track-by-booking-solution.html?{query}"
    soup = get_zenrows_soup(target_url)
    if not soup:
        return {"container_information": {}, "detailed_movements": []}

    container_information = {}
    for row in soup.select("table.groupBorder tr"):
        cells = row.find_all(["td", "th"], recursive=False)
        if len(cells) < 2:
            continue
        label = cells[0].get_text(" ", strip=True)
        value = cells[1].get_text(" ", strip=True)
        if label and value:
            container_information[label] = value

    movements = []
    for table in soup.select("table.hl-tbl"):
        for row in table.select("tbody tr"):
            cols = row.find_all("td", recursive=False)
            if len(cols) >= 6:
                values = [col.get_text(" ", strip=True) for col in cols]
                movements.append({
                    "status": values[0],
                    "place_of_activity": values[1],
                    "date": values[2],
                    "time": values[3],
                    "transport": values[4],
                    "voyage_no": values[5]
                })

    return {"container_information": container_information, "detailed_movements": movements}

def scrape_with_zenrows():
    print(f"Rastreando el BL principal: {BL_NUMBER}...")
    target_url = f"https://www.hapag-lloyd.com/en/online-business/track/track-by-booking-solution.html?blno={BL_NUMBER}"

    soup = get_zenrows_soup(target_url)
    if not soup:
        return None

    containers_data = []
    rows = soup.select("table.single-select tbody tr") or soup.find_all("tr")

    seen_containers = set()

    for row in rows:
        cols = row.find_all(["td", "th"], recursive=False)
        if len(cols) < 6:
            continue

        # En la tabla del BL la primera celda contiene el radio de selección.
        col_texts = [col.get_text(" ", strip=True) for col in cols]
        if col_texts[1] == "Type" or col_texts[2] == "Container No.":
            continue
        container_type, container_no, status, date, place = col_texts[1:6]
        container_no = " ".join(container_no.split())
        if not container_no or container_no in seen_containers or len(container_no) < 6:
            continue

        seen_containers.add(container_no)
        details = scrape_container_details(container_no)
        containers_data.append({
            "type": container_type,
            "container_no": container_no,
            "status_summary": status,
            "date_summary": date,
            "place_summary": place,
            **details
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