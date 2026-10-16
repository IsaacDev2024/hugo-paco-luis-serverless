"""Guarda solo atributos públicos de seguridad/costo; nunca claves ni app settings completos."""
import datetime
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
group = "rg-hpl-parcial-dev"
def az(*args):
    return json.loads(subprocess.check_output(["az", *args, "-o", "json"]))
app = az("functionapp", "list", "--resource-group", group, "--query", "[0].{id:id,name:name,defaultHostName:defaultHostName,httpsOnly:httpsOnly}")
if not app:
    raise SystemExit("No existe una Function App en el grupo del taller")
config = az("resource", "show", "--ids", app["id"], "--api-version", "2024-04-01", "--query", "{https_only:properties.httpsOnly,scale:properties.functionAppConfig.scaleAndConcurrency,runtime:properties.functionAppConfig.runtime,storage_auth:properties.functionAppConfig.deployment.storage.authentication.type,tags:tags}")
storage = az("storage", "account", "list", "--resource-group", group, "--query", "[].{name:name,allow_shared_key:allowSharedKeyAccess,allow_public_blobs:allowBlobPublicAccess,tls:minimumTlsVersion,https_only:enableHttpsTrafficOnly,replication:sku.name,tags:tags}")
resource_list = az("resource", "list", "--resource-group", group, "--query", "[].{name:name,type:type,location:location,tags:tags}")
setting_names = az("functionapp", "config", "appsettings", "list", "--resource-group", group, "--name", app["name"], "--query", "[].name")
config["legacy_storage_connection_present"] = "AzureWebJobsStorage" in setting_names
data = {"collected_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "function": app, "configuration": config, "storage": storage, "resources": resource_list}
target = root / "evidence/cloud/resource-posture.json"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print(target)
