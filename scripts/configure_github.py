"""Publica identificadores de bootstrap como variables y crea backend.hcl privado."""
import argparse
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--repo", default="IsaacDev2024/hugo-paco-luis-serverless")
parser.add_argument("--backend-only", action="store_true")
args = parser.parse_args()
values = json.loads(subprocess.check_output(["terraform", "-chdir=" + str(root / "bootstrap"), "output", "-json", "github_variables"]))
backend = root / "infra/backend.hcl"
backend.write_text('storage_account_name = "' + values["TF_STATE_ACCOUNT"] + '"\ncontainer_name = "' + values["TF_STATE_CONTAINER"] + '"\nkey = "dev.terraform.tfstate"\nuse_azuread_auth = true\n')
backend.chmod(0o600)
if not args.backend_only:
    for key, value in values.items():
        subprocess.run(["gh", "variable", "set", key, "--repo", args.repo, "--body", value], check=True)
print("Backend local configurado" + (" y variables de GitHub actualizadas" if not args.backend_only else ""))
