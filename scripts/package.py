"""Crea un ZIP reproducible con host.json en la raíz, sin estados ni secretos."""
import argparse
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def package(commit="local"):
    if not re.fullmatch(r"[a-f0-9]{40}|local", commit):
        raise ValueError("Usa un SHA de Git de 40 caracteres o local")
    files = ["function_app.py", "requirements.txt", "host.json", "release.json",
             "static/index.html", "static/app.js", "static/style.css"]
    target = ROOT / "dist/function.zip"
    target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            data = (ROOT / "app" / name).read_bytes()
            if name == "release.json":
                release = json.loads(data)
                release["commit"] = commit
                data = json.dumps(release, ensure_ascii=False).encode()
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    print(target)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", default="local")
    package(parser.parse_args().commit)
