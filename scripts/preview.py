"""Adaptador local de vista previa; no sustituye Azure Functions Core Tools ni Azure."""
import sys
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server
import azure.functions as func

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import function_app as api


def application(env, start_response):
    path = env["PATH_INFO"]
    method = env["REQUEST_METHOD"]
    route = {}
    handler = {"/": api.home, "/api/health": api.health, "/api/equipo": api.team, "/api/saludo": api.greet}.get(path)
    if path.startswith("/assets/"):
        handler, route = api.assets, {"name": path[len("/assets/"):]}
    if not handler or (method != "GET" and not (method == "POST" and handler == api.greet)):
        result = api.response({"error": "Ruta o método no disponible"}, 404)
    else:
        size = min(int(env.get("CONTENT_LENGTH") or 0), 4097)
        req = func.HttpRequest(method, "http://127.0.0.1:8765" + path,
            params={k: v[0] for k, v in parse_qs(env.get("QUERY_STRING", ""), keep_blank_values=True).items()},
            body=env["wsgi.input"].read(size), headers={"content-type": env.get("CONTENT_TYPE", "")}, route_params=route)
        result = handler(req)
    from http import HTTPStatus
    headers = list(result.headers.items())
    headers.append(("Content-Type", result.mimetype + "; charset=utf-8"))
    start_response(f"{result.status_code} {HTTPStatus(result.status_code).phrase}", headers)
    return [result.get_body()]


if __name__ == "__main__":
    print("Vista previa local: http://127.0.0.1:8765 (sin host de Azure)", flush=True)
    make_server("127.0.0.1", 8765, application).serve_forever()
