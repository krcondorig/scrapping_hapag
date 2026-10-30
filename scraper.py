import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

RENDER_API_URL = "https://scrapping-hapag.onrender.com/save-tracking"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
BL_NUMBER = "HLCUNG12607EKZE0"  # Tu número de BL / Guía

def scrape_with_zenrows():
    print(f"Rastreando el BL {BL_NUMBER} y su tabla de contenedores a través de ZenRows...")

    raw_target_url = f"https://www.hapag-lloyd.com/en/online-business/track/track-by-booking-solution.html?blno={BL_NUMBER}"
    encoded_target_url = quote(raw_target_url, safe="")

    zenrows_url = f"https://api.zenrows.com/v1/?apikey={ZENROWS_API_KEY}&url={encoded_target_url}&js_render=true&antibot=true&premium_proxy=true"

    response = requests.get(zenrows_url)

    if response.status_code != 200:
        print(f"Error en la API de ZenRows: Código {response.status_code} - {response.text}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Buscamos las filas de la tabla de contenedores que se muestran en el portal
    containers_data = []

    # Hapag-Lloyd utiliza filas o elementos de lista para esta tabla.
    # Buscamos filas de tabla genéricas o contenedores de elementos de la lista de resultados
    rows = soup.find_all("tr") or soup.select(".table-row, .result-row")

    for row in rows:
        cols = row.find_all(["td", "th"])
        if len(cols) >= 5:  # Verificamos que tenga las columnas esperadas (Type, Container No., Status, etc.)
            col_texts = [col.get_text(strip=True) for col in cols]
            # Filtramos para asegurarnos de que parece una fila de contenedor
            containers_data.append({
                "type": col_texts[0],
                "container_no": col_texts[1],
                "status": col_texts[2],
                "date": col_texts[3],
                "place_of_activity": col_texts[4]
            })

    # Si no encuentra filas mediante <tr> tradicionales, guardamos una estructura basada en el texto general capturado
    payload = {
        "bl_number": BL_NUMBER,
        "total_containers": len(containers_data),
        "containers": containers_data if containers_data else [{"info": "Revisar estructura HTML o selector de tabla"}],
        "location": "Actualizado vía GitHub Actions + ZenRows Prémium"
    }

    return payload

def send_to_render(data):
    if not data or not ADMIN_TOKEN:
        print("Faltan datos o token de administración.")
        return

    headers = {
        "x-admin-token": ADMIN_TOKEN,
        "Content-Type": "application/json"
    }

    # Adaptamos el endpoint para guardar usando el BL como identificador principal
    response = requests.post(RENDER_API_URL, json=data, headers=headers)
    if response.status_code == 200:
        print("¡Tabla de contenedores detallada enviada y sincronizada con Render con éxito!")
    else:
        print(f"Error al enviar a Render: {response.status_code} - {response.text}")

if __name__ == "__main__":
    extracted_data = scrape_with_zenrows()
    if extracted_data:
        send_to_render(extracted_data)