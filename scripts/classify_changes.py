"""Distingue cambios, incluso cuando se renombra un commit publicado."""
import os
import re
import subprocess

base = os.environ.get("BASE_SHA", "")
if base and not re.fullmatch(r"[0-9a-f]{40}", base):
    raise SystemExit("BASE_SHA inválido")
if base and set(base) != {"0"}:
    exists = subprocess.run(["git", "cat-file", "-e", base + "^{commit}"], capture_output=True).returncode == 0
    if not exists:
        exists = subprocess.run(["git", "fetch", "--no-tags", "origin", base], capture_output=True).returncode == 0
    if not exists:
        base = ""  # Validar y publicar todo si el SHA previo dejó de estar disponible.
if not base or set(base) == {"0"}:
    names = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
else:
    if subprocess.run(["git", "merge-base", "--is-ancestor", base, "HEAD"], check=False).returncode:
        base = subprocess.check_output(["git", "merge-base", base, "HEAD"]).decode().strip()
    names = subprocess.check_output(["git", "diff", "--name-only", "-z", base, "HEAD"]).decode().split("\0")
infra = any(n.startswith(("infra/", "config/")) for n in names)
app = infra or any(n.startswith(("app/", "scripts/package.py", "scripts/smoke.py", ".github/workflows/")) for n in names)
with open(os.environ["GITHUB_OUTPUT"], "a") as out:
    out.write(f"infra={str(infra).lower()}\napp={str(app).lower()}\n")
print(f"infra={infra}, app={app}")
