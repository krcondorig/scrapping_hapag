from fastapi import FastAPI, HTTPException
import scraper

app = FastAPI()

@app.get("/")
def home():
    return {"status": "API de Hapag-Lloyd funcionando correctamente"}

@app.get("/track/{identifier}")
def get_container(identifier: str):
    identifier = identifier.strip()
    if not identifier or len(identifier) > 35 or not identifier.replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="El BL o booking number tiene un formato inválido.")

    try:
        return scraper.scrape_bl(identifier)
    except scraper.MissingZenRowsKey as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except scraper.ZenRowsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc