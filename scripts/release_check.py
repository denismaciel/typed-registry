"""Build, verify installed distributions, and prepare GitHub release assets."""

import hashlib
import html
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:(?:a|b|rc)[0-9]+)?", VERSION):
    raise SystemExit(f"Unsupported release version: {VERSION!r}; use X.Y.Z or X.Y.ZrcN/aN/bN")
TAG = os.environ.get("RELEASE_TAG") or f"v{VERSION}"
if TAG != f"v{VERSION}":
    raise SystemExit(f"Tag {TAG!r} does not match project version v{VERSION}")

SMOKE = """
from importlib.metadata import version
from importlib.resources import files
from typed_registry import MissingServiceError, ServiceRegistry, ServiceToken
assert version('typed-registry') == EXPECTED_VERSION
assert files('typed_registry').joinpath('py.typed').is_file()
registry = ServiceRegistry()
token = ServiceToken[str]('service')
token.register(registry, 'first')
token.register(registry, 'replacement')
assert registry.get(token) == 'replacement'
try:
    registry.get(ServiceToken[str]('service'))
except MissingServiceError as error:
    assert error.service_name == 'service'
else:
    raise AssertionError('distinct tokens must not alias')
""".replace("EXPECTED_VERSION", repr(VERSION))


def run(*args: str, cwd: Path = ROOT) -> None:
    subprocess.run(args, cwd=cwd, check=True)


with tempfile.TemporaryDirectory(prefix="typed-registry-release-") as temporary:
    work = Path(temporary)
    built = work / "artifacts"
    run("uv", "build", "--no-sources", "--out-dir", str(built))
    wheels = list(built.glob("*.whl"))
    sdists = list(built.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit("Expected exactly one wheel and one sdist")
    for index, artifact in enumerate(wheels + sdists):
        environment = work / f"install-{index}"
        run("uv", "venv", "--python", sys.executable, str(environment), cwd=work)
        python = str(environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))
        run("uv", "pip", "install", "--python", python, "--no-deps", str(artifact), cwd=work)
        run(python, "-I", "-c", SMOKE, cwd=work)

    checksums = []
    links = []
    for artifact in sorted(wheels + sdists):
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        checksums.append(f"{digest}  {artifact.name}\n")
        url = f"https://github.com/denismaciel/typed-registry/releases/download/{TAG}/{artifact.name}"
        links.append(f'<a href="{html.escape(url)}#sha256={digest}">{html.escape(artifact.name)}</a><br>')
    (built / "SHA256SUMS").write_text("".join(checksums))
    (built / "index.html").write_text("<!DOCTYPE html>\n<html><body>\n" + "\n".join(links) + "\n</body></html>\n")
    destination = ROOT / "dist" / "release"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(built, destination)
    print(f"Verified release assets: {destination}")
