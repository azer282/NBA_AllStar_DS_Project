"""Reproducible download of the raw NBA data (Module 1 - owner: Augustin Nilsson).

Usage (from the project root):
    .venv\\Scripts\\python.exe -m src.data.download

What it does:
1. Downloads the pinned version of the Kaggle dataset (see src/config.py) into data/raw/.
2. Checks the SHA-256 of the zip against the expected value. Stops if it differs.
3. Extracts the CSV files (with a path-safety check) into data/raw/<dataset>_v<version>/.
4. Writes data/raw_manifest.json: source, version, URL, date, zip checksum and one
   checksum per extracted file. The manifest is committed to git; the data are not.

Raw files are never modified after download: cleaning happens in a separate step.
No Kaggle API key is needed: on 2026-11-25 the public download endpoint answered
without credentials. If that changes, the script stops with a clear message.
"""
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

from src.config import (
    DATA_RAW_DIR,
    KAGGLE_DATASET,
    KAGGLE_VERSION,
    KAGGLE_ZIP_SHA256,
    PROJECT_ROOT,
    RAW_FILES_DIR,
    RAW_MANIFEST_PATH,
    RAW_ZIP_PATH,
    ensure_dirs,
)

DOWNLOAD_URL = (
    f"https://www.kaggle.com/api/v1/datasets/download/{KAGGLE_DATASET}"
    f"?datasetVersionNumber={KAGGLE_VERSION}"
)
TIMEOUT_SECONDS = 180  # generous: the zip is about 11 MB
# Honest, descriptive User-Agent (project name, no personal data). We never disguise the
# client as a browser. Observed 2026-11-25: Kaggle answers 404 to the default
# "python-requests/x" User-Agent but serves the file to this one. If Kaggle blocks it,
# the script stops (see download_zip) and we switch to a personal kaggle.json API key.
HTTP_HEADERS = {
    "User-Agent": "NBA-AllStar-DS-Project/0.1 (student course project; reproducible dataset download)"
}
CHUNK_BYTES = 1 << 20  # read files 1 MB at a time when hashing / downloading


def sha256_of(path: Path) -> str:
    """Return the hex SHA-256 of a file, read in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_zip(url: str, destination: Path) -> None:
    """Stream the zip to disk. Raise a clear error if Kaggle refuses anonymous access."""
    response = requests.get(url, headers=HTTP_HEADERS, stream=True, timeout=TIMEOUT_SECONDS)
    if response.status_code in (401, 403, 404):
        raise PermissionError(
            "Kaggle refused the anonymous download. Create an API token on kaggle.com "
            "(Settings > API), save it as %USERPROFILE%\\.kaggle\\kaggle.json (never commit it), "
            "and tell the team: the download method must then be updated."
        )
    response.raise_for_status()
    with open(destination, "wb") as handle:
        for chunk in response.iter_content(chunk_size=CHUNK_BYTES):
            handle.write(chunk)


def safe_extract(zip_path: Path, target_dir: Path) -> list[str]:
    """Extract the zip, refusing any member that would land outside target_dir."""
    target_dir.mkdir(parents=True, exist_ok=True)
    root = target_dir.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        for name in names:
            if not (root / name).resolve().is_relative_to(root):
                raise ValueError(f"Unsafe path in zip, extraction aborted: {name}")
        archive.extractall(root)
    return sorted(names)


def main() -> None:
    """Download, verify, extract and write the manifest."""
    ensure_dirs()
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    if RAW_ZIP_PATH.exists() and sha256_of(RAW_ZIP_PATH) == KAGGLE_ZIP_SHA256:
        print(f"Zip already present and verified: {RAW_ZIP_PATH.name}")
    else:
        print(f"Downloading {KAGGLE_DATASET} v{KAGGLE_VERSION} ...")
        download_zip(DOWNLOAD_URL, RAW_ZIP_PATH)

    zip_sha = sha256_of(RAW_ZIP_PATH)
    if zip_sha != KAGGLE_ZIP_SHA256:
        raise ValueError(
            f"Checksum mismatch: got {zip_sha}, expected {KAGGLE_ZIP_SHA256}. "
            "The source changed: do not use these data before the team reviews it."
        )
    print("Zip checksum OK.")

    members = safe_extract(RAW_ZIP_PATH, RAW_FILES_DIR)
    files = {
        name: {
            "bytes": (RAW_FILES_DIR / name).stat().st_size,
            "sha256": sha256_of(RAW_FILES_DIR / name),
        }
        for name in members
    }
    manifest = {
        "source": "Kaggle",
        "dataset": KAGGLE_DATASET,
        "dataset_url": f"https://www.kaggle.com/datasets/{KAGGLE_DATASET}",
        "version": KAGGLE_VERSION,
        "download_url": DOWNLOAD_URL,
        "license": "CC0: Public Domain (Kaggle metadata; data scraped from Basketball-Reference)",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "zip_file": RAW_ZIP_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "zip_sha256": zip_sha,
        "extracted_dir": RAW_FILES_DIR.relative_to(PROJECT_ROOT).as_posix(),
        "files": files,
    }
    RAW_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Extracted {len(files)} files. Manifest written to {RAW_MANIFEST_PATH.name}.")


if __name__ == "__main__":
    main()
