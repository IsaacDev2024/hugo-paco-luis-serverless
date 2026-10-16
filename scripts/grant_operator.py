"""Concede al operador acceso Blob a la carga para operar Terraform localmente."""
import json
import subprocess

def az(*args):
    return subprocess.check_output(["az", *args, "-o", "json"])
operator = json.loads(az("ad", "signed-in-user", "show"))["id"]
group = json.loads(az("group", "show", "--name", "rg-hpl-parcial-dev"))["id"]
subprocess.run(["az", "role", "assignment", "create", "--assignee-object-id", operator, "--assignee-principal-type", "User", "--role", "Storage Blob Data Contributor", "--scope", group, "-o", "none"], check=True)
print("Operador con acceso Blob en el grupo del laboratorio")
