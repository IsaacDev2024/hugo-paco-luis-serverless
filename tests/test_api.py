import importlib.util
import json
from pathlib import Path
import sys

import azure.functions as func
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "app"))
import function_app as api


def req(params=None, body=b"", method="GET", headers=None, route=None):
    return func.HttpRequest(method, "https://localhost/api/saludo", params=params or {},
                            body=body, headers=headers or {}, route_params=route or {})


def payload(result):
    return json.loads(result.get_body())


def test_health_contains_release_and_environment(monkeypatch):
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    result = api.health(req())
    assert result.status_code == 200
    assert payload(result)["status"] == "ok"
    assert payload(result)["environment"] == "test"
    assert payload(result)["version"] == api.RELEASE["version"]


@pytest.mark.parametrize("character", ["hugo", "paco", "luis", "HUGO"])
def test_json_greeting(character):
    result = api.greet(req({"nombre": "Isaac", "personaje": character}))
    assert result.status_code == 200
    assert "Isaac" in payload(result)["message"]
    assert payload(result)["character"].lower() == character.lower()


def test_plain_text_is_a_second_content_type():
    result = api.greet(req({"formato": "texto"}))
    assert result.status_code == 200 and result.mimetype == "text/plain"
    assert "Visitante" in result.get_body().decode()


def test_post_unicode():
    result = api.greet(req(method="POST", body=json.dumps({"nombre": "María", "personaje": "luis"}).encode(), headers={"content-type": "application/json"}))
    assert result.status_code == 200
    assert "María" in payload(result)["message"]


@pytest.mark.parametrize("params", [{"nombre": ""}, {"nombre": "a" * 61}, {"nombre": "a\nb"}, {"personaje": "donald"}, {"formato": "html"}])
def test_invalid_query_returns_400(params):
    assert api.greet(req(params)).status_code == 400


@pytest.mark.parametrize("body", [b"bad", b"[]", b"null", b'{"nombre":42}', b'{"personaje": []}'])
def test_invalid_json_or_types_returns_400(body):
    assert api.greet(req(method="POST", body=body, headers={"content-type": "application/json"})).status_code == 400


def test_body_size_and_media_type():
    assert api.greet(req(method="POST", body=b"x" * 4097)).status_code == 413
    assert api.greet(req(method="POST", body=b"{}")).status_code == 415


def test_team_and_security_headers():
    result = api.team(req())
    assert len(payload(result)["members"]) == 4
    assert result.headers["X-Content-Type-Options"] == "nosniff"
    assert "script-src 'self'" in result.headers["Content-Security-Policy"]


def test_assets_do_not_allow_path_traversal():
    assert api.assets(req(route={"name": "../function_app.py"})).status_code == 404
    assert api.assets(req(route={"name": "app.js"})).status_code == 200
    assert api.home(req()).status_code == 200
