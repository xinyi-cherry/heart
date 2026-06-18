import argparse
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
APP_NAME = "HeartRateBandLogger"


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def zip_dir(source: Path, target: Path) -> None:
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in source.rglob("*"):
            archive.write(path, path.relative_to(source.parent))


def build(clean: bool) -> Path:
    if clean:
        shutil.rmtree(ROOT / "build", ignore_errors=True)
        shutil.rmtree(DIST, ignore_errors=True)

    run([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "heart_rate_logger.spec"])

    system = platform.system().lower()
    machine = platform.machine().lower() or "unknown"
    suffix = f"{system}-{machine}"

    if system == "darwin":
        artifact_source = DIST / f"{APP_NAME}.app"
    else:
        artifact_source = DIST / APP_NAME

    if not artifact_source.exists():
        raise FileNotFoundError(f"Build artifact not found: {artifact_source}")

    package = DIST / f"{APP_NAME}-{suffix}.zip"
    zip_dir(artifact_source, package)
    print(f"Package created: {package}")
    return package


def main() -> int:
    parser = argparse.ArgumentParser(description="Build distributable desktop packages.")
    parser.add_argument("--no-clean", action="store_true", help="Keep existing build/dist directories")
    args = parser.parse_args()
    build(clean=not args.no_clean)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
