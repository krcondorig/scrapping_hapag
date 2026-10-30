import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

RENDER_API_URL = "https://scrapping-hapag.onrender.com/save-tracking"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
BL_NUMBER = "HLCUNG12607EKZE0"

def scrape_with_zenrows():
    print(f"Rastreando el BL {BL_NUMBER} y extrayendo detalles de contenedores...")

    raw_target_url = f"https://www.hapag-lloyd.com/en/online-business/track/track-by-booking-solution.html?blno={BL_NUMBER}"
    encoded_target_url = quote(raw_target_url, safe="")

    zenrows_url = f"https://api.zenrows.com/v1/?apikey={ZENROWS_API_KEY}&url={encoded_target_url}&js_render=true&antibot=true&premium_proxy=true"

    response = requests.get(zenrows_url)

    if response.status_code != 200:
        print(f"Error en ZenRows: Código {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    containers_data = []

    # Filtramos y limpiamos las filas reales de la tabla de contenedores
    rows = soup.find_all("tr")
    for row in rows:
        cols = row.find_all(["td", "th"])
        if len(cols) >= 5:
            col_texts = [col.get_text(strip=True) for col in cols]

            # Evitamos capturar la cabecera de la tabla
            if "Container No." in col_texts[1] or "Type" in col_texts[0]:
                continue

            container_no = col_texts[1]
            status = col_texts[2]
            date = col_texts[3]
            place = col_texts[4]

            # Limpiamos espacios duplicados en el número de contenedor
            container_no = " ".join(container_no.split())

            if container_no and len(container_no) > 4:
                containers_data.append({
                    "type": col_texts[0],
                    "container_no": container_no,
                    "status": status,
                    "date": date,
                    "place_of_activity": place,
                    # Aquí simulamos/dejamos listo el espacio para los detalles profundos
                    "details_url": f"https://www.hapag-lloyd.com/... (Contenedor {container_no})"
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
        return

    headers = {
        "x-admin-token": ADMIN_TOKEN,
        "Content-Type": "application/json"
    }

    response = requests.post(RENDER_API_URL, json=data, headers=headers)
    if response.status_code == 200:
        print("¡Datos limpios y detallados de contenedores sincronizados con Render!")

if __name__ == "__main__":
    extracted_data = scrape_with_zenrows()
    if extracted_data:
        send_to_render(extracted_data)