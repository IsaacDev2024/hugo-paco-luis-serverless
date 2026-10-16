"""Descarga los artefactos públicos de un run finalizado, sin estados ni tokens."""
import argparse
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("run_id", type=int)
parser.add_argument("label", choices=["baseline", "app-change", "infra-change", "final-validation", "storage-fix", "infra-initial"])
args = parser.parse_args()
repo = "IsaacDev2024/hugo-paco-luis-serverless"
root = Path(__file__).resolve().parents[1]
run = json.loads(subprocess.check_output(["gh", "run", "view", str(args.run_id), "--repo", repo, "--json", "databaseId,headSha,status,conclusion,url,jobs"]))
if run["status"] != "completed":
    raise SystemExit("El run todavía no ha finalizado")
target = root / "evidence/cloud" / args.label
target.mkdir(parents=True, exist_ok=True)
subprocess.run(["gh", "run", "download", str(args.run_id), "--repo", repo, "--dir", str(target)], check=True)
(target / "run.json").write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n")
print("Evidencia descargada:", target)
