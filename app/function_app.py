"""API HTTP del taller 4. Sin base de datos ni datos persistidos de visitantes."""
import json
import logging
import os
from pathlib import Path
import re
import uuid

import azure.functions as func

ROOT = Path(__file__).parent
RELEASE = json.loads((ROOT / "release.json").read_text(encoding="utf-8"))
TEAM = "Hugo, Paco y Luis"
MEMBERS = [
    "Isaac David Sánchez Sánchez",
    "Santiago Andrés Orejuela Cueter",
    "Luis Mario Díaz Martínez",
    "Eli Weiman Amaya",
]
CHARACTERS = {"hugo": "Hugo", "paco": "Paco", "luis": "Luis"}
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def response(body, status=200, mimetype="application/json"):
    if mimetype == "application/json":
        body = json.dumps(body, ensure_ascii=False)
    return func.HttpResponse(body, status_code=status, mimetype=mimetype, charset="utf-8", headers={
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store",
        "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
    })


@app.route(route="/", methods=["GET"])
def home(req: func.HttpRequest) -> func.HttpResponse:
    return response((ROOT / "static/index.html").read_text(encoding="utf-8"), mimetype="text/html")


@app.route(route="assets/{name}", methods=["GET"])
def assets(req: func.HttpRequest) -> func.HttpResponse:
    # Allowlist: nunca se interpreta una ruta suministrada por el visitante.
    files = {"app.js": "text/javascript", "style.css": "text/css"}
    name = req.route_params.get("name")
    if name not in files:
        return response({"error": "Recurso no encontrado"}, 404)
    return response((ROOT / "static" / name).read_text(encoding="utf-8"), mimetype=files[name])


@app.route(route="api/health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return response({"status": "ok", "team": TEAM, "version": RELEASE["version"],
                     "commit": RELEASE["commit"], "environment": os.getenv("APP_ENVIRONMENT", "local")})


@app.route(route="api/equipo", methods=["GET"])
def team(req: func.HttpRequest) -> func.HttpResponse:
    return response({"team": TEAM, "members": MEMBERS, "workshop": 4,
                     "platform": "Azure Functions", "version": RELEASE["version"]})


@app.route(route="api/saludo", methods=["GET", "POST"])
def greet(req: func.HttpRequest) -> func.HttpResponse:
    request_id = str(uuid.uuid4())
    if len(req.get_body()) > 4096:
        return response({"error": "La solicitud excede 4096 bytes", "request_id": request_id}, 413)
    data = dict(req.params)
    if req.method == "POST":
        if req.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
            return response({"error": "Usa Content-Type: application/json", "request_id": request_id}, 415)
        try:
            data = req.get_json()
        except ValueError:
            return response({"error": "JSON inválido", "request_id": request_id}, 400)
        if not isinstance(data, dict):
            return response({"error": "El cuerpo debe ser un objeto JSON", "request_id": request_id}, 400)
    name, character, output = data.get("nombre", "Visitante"), data.get("personaje", "hugo"), data.get("formato", "json")
    if not isinstance(name, str) or not re.fullmatch(r"[^\x00-\x1f\x7f]{1,60}", name.strip()):
        return response({"error": "nombre debe contener entre 1 y 60 caracteres sin controles", "request_id": request_id}, 400)
    if not isinstance(character, str) or character.lower() not in CHARACTERS:
        return response({"error": "personaje debe ser hugo, paco o luis", "request_id": request_id}, 400)
    if output not in ("json", "texto"):
        return response({"error": "formato debe ser json o texto", "request_id": request_id}, 400)
    character = CHARACTERS[character.lower()]
    message = f"¡Hola, {name.strip()}! Soy {character}. {RELEASE['message']}"
    # Solo identificador y resultado; nunca nombre, cuerpo ni credenciales.
    logging.info("greeting_success request_id=%s version=%s", request_id, RELEASE["version"])
    if output == "texto":
        return response(message, mimetype="text/plain")
    return response({"message": message, "character": character, "team": TEAM,
                     "version": RELEASE["version"], "commit": RELEASE["commit"], "request_id": request_id})
