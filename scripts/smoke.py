"""Pruebas HTTP reales. Reintenta solo para el arranque en frío/despliegue."""
import argparse
import json
from pathlib import Path
import time
import urllib.error
import urllib.request
from urllib.parse import urlencode


def call(base, path, body=None):
    req = urllib.request.Request(base.rstrip("/") + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"} if body is not None else {})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status, res.headers.get("Content-Type", ""), res.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read().decode()


def verify(base, commit=None, version=None):
    status, _, body = call(base, "/api/health")
    data = json.loads(body)
    assert status == 200 and data["status"] == "ok", "Health fallido"
    if commit:
        assert data["commit"] == commit, f"Commit publicado distinto: {data.get('commit')}"
    if version:
        assert data["version"] == version, "Versión publicada distinta"
    checks = [{"endpoint": "/api/health", "status": status, "response": data}]
    for character in ["hugo", "paco", "luis"]:
        status, content_type, body = call(base, "/api/saludo?" + urlencode({"nombre": "Equipo UTB", "personaje": character}))
        assert status == 200 and "application/json" in content_type
        assert json.loads(body)["character"].lower() == character
        checks.append({"endpoint": f"/api/saludo?personaje={character}", "status": status})
    status, content_type, body = call(base, "/api/saludo", {"nombre": "Equipo UTB", "formato": "texto"})
    assert status == 200 and "text/plain" in content_type and "Equipo UTB" in body
    checks.append({"endpoint": "POST /api/saludo (texto)", "status": status})
    status, _, body = call(base, "/api/saludo?personaje=desconocido")
    assert status == 400 and "error" in json.loads(body)
    checks.append({"endpoint": "/api/saludo inválido", "status": status})
    status, _, body = call(base, "/api/equipo")
    assert status == 200 and len(json.loads(body)["members"]) == 4
    checks.append({"endpoint": "/api/equipo", "status": status})
    status, content_type, body = call(base, "/")
    assert status == 200 and "text/html" in content_type and "Hugo" in body
    checks.append({"endpoint": "/", "status": status})
    return checks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    parser.add_argument("--commit")
    parser.add_argument("--version")
    parser.add_argument("--output", default="evidence/smoke.json")
    args = parser.parse_args()
    last_error = None
    for attempt in range(12):
        try:
            checks = verify(args.base_url, args.commit, args.version)
            break
        except (AssertionError, ValueError, KeyError, OSError) as exc:
            last_error = exc
            if attempt == 11:
                raise
            print(f"Esperando despliegue ({attempt + 1}/12): {exc}", flush=True)
            time.sleep(10)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"tested_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                  "base_url": args.base_url, "passed": True, "checks": checks}, indent=2, ensure_ascii=False) + "\n")
    print(f"OK: {len(checks)} pruebas HTTP. Evidencia: {target}")
