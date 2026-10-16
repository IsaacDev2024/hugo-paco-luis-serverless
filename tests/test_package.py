import importlib.util
import json
from pathlib import Path
import zipfile

path = Path(__file__).resolve().parents[1] / "scripts/package.py"
spec = importlib.util.spec_from_file_location("packager", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_zip_has_host_at_root_and_only_allowlisted_files():
    sha = "a" * 40
    target = module.package(sha)
    with zipfile.ZipFile(target) as archive:
        assert "host.json" in archive.namelist()
        assert len(archive.namelist()) == 7
        assert json.loads(archive.read("release.json"))["commit"] == sha
        assert not any(name.endswith((".tfstate", ".tfplan")) or "local.settings" in name for name in archive.namelist())
    assert json.loads((module.ROOT / "app/release.json").read_text())["commit"] == "local"
