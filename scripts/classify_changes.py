"""Distingue cambios sin interpolar nombres de archivos en comandos shell."""
import os
import subprocess
base = os.environ.get("BASE_SHA", "")
if not base or set(base) == {"0"}:
    names = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
else:
    names = subprocess.check_output(["git", "diff", "--name-only", "-z", base, "HEAD"]).decode().split("\0")
infra = any(n.startswith(("infra/", "config/")) for n in names)
app = infra or any(n.startswith(("app/", "scripts/package.py", "scripts/smoke.py", ".github/workflows/")) for n in names)
with open(os.environ["GITHUB_OUTPUT"], "a") as out:
    out.write(f"infra={str(infra).lower()}\napp={str(app).lower()}\n")
print(f"infra={infra}, app={app}")
