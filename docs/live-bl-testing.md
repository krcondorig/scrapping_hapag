# Consulta de BL en vivo

## Configuración de Render

En **Render → servicio API → Environment**, configura `ZENROWS_API_KEY` con tu clave de ZenRows. La API también requiere `ADMIN_TOKEN` para el endpoint existente `POST /save-tracking`.

## Consultar desde Bruno

Crea una petición `GET` a:

```text
https://scrapping-hapag.onrender.com/track/HLCUNG12608BMJY0
```

Sustituye el último segmento por cualquier booking number o BL válido. No requiere body ni token de administrador. La respuesta incluye `bl_number`, `total_containers` y cada contenedor con su `container_information` e `detailed_movements`.

Cada llamada consulta ZenRows en vivo: una solicitud para el BL y una solicitud adicional por cada contenedor encontrado. Las llamadas consumen el saldo de ZenRows.

## Errores esperados

- `400`: identificador vacío o con formato inválido.
- `502`: ZenRows rechazó la solicitud o no estuvo disponible.
- `503`: Render no tiene configurada `ZENROWS_API_KEY`.

El workflow de GitHub Actions existente se conserva para actualizar periódicamente el BL configurado allí; el endpoint de Bruno ya no depende de los datos almacenados por ese workflow.
