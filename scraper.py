import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")


class MissingZenRowsKey(Exception):
    pass


class ZenRowsError(Exception):
    pass


def get_zenrows_soup(target_url, api_key=None):
    zenrows_api = "https://api.zenrows.com/v1/"
    params = {
        "apikey": api_key or ZENROWS_API_KEY,
        "url": target_url,
        "js_render": "true",
        "antibot": "true",
        "premium_proxy": "true"
    }
    try:
        response = requests.get(zenrows_api, params=params, timeout=60)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ZenRowsError(f"ZenRows request failed: {exc}") from exc
    return BeautifulSoup(response.text, "html.parser")

def scrape_container_details(container_no, api_key=None):
    print(f"Extrayendo detalles para el contenedor: {container_no}...")
    query = f"view=S8510&container={quote_plus(container_no).replace('+', '++')}"
    target_url = f"https://www.hapag-lloyd.com/en/online-business/track/track-by-booking-solution.html?{query}"
    soup = get_zenrows_soup(target_url, api_key)

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

def scrape_bl(bl_number, zenrows_api_key=None):
    api_key = zenrows_api_key or ZENROWS_API_KEY
    if not api_key:
        raise MissingZenRowsKey("ZENROWS_API_KEY is not configured in the Render service environment")

    target_url = f"https://www.hapag-lloyd.com/en/online-business/track/track-by-booking-solution.html?blno={quote_plus(bl_number)}"
    soup = get_zenrows_soup(target_url, api_key)
    if not soup:
        raise ZenRowsError("ZenRows returned no HTML for the BL lookup")

    if not soup.select_one("form.olbForm") or not soup.select_one("table.single-select"):
        raise ZenRowsError("Hapag-Lloyd returned an unrecognized BL results page")

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
        details = scrape_container_details(container_no, api_key)
        containers_data.append({
            "type": container_type,
            "container_no": container_no,
            "status_summary": status,
            "date_summary": date,
            "place_summary": place,
            **details
        })

    payload = {
        "bl_number": bl_number,
        "total_containers": len(containers_data),
        "containers": containers_data,
        "location": "Consultado en vivo vía ZenRows"
    }

    return payload
