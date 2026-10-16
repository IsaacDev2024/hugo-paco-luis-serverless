"""Obtiene el subject OIDC real; admite repositorios con IDs inmutables y anteriores."""
import argparse
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--repo", default="IsaacDev2024/hugo-paco-luis-serverless")
args = parser.parse_args()
config = json.loads(subprocess.check_output(["gh", "api", "repos/" + args.repo + "/actions/oidc/customization/sub"]))
if not config.get("use_default"):
    raise SystemExit("El repositorio usa un subject personalizado; confirmar su formato exacto antes del bootstrap")
prefix = config.get("sub_claim_prefix")
if not prefix or not prefix.startswith("repo:"):
    raise SystemExit("GitHub no devolvió el prefijo OIDC; actualizar gh o inspeccionar la configuración")
subject = prefix + ":ref:refs/heads/main"
target = Path(__file__).resolve().parents[1] / "bootstrap/github.auto.tfvars.json"
target.write_text(json.dumps({"github_oidc_subject": subject}, indent=2) + "\n")
target.chmod(0o600)
print("Subject de main configurado:", subject)
