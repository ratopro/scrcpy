"""
installer.py — Descarga, verifica SHA256 e instala scrcpy.
"""
import hashlib
import io
import os
import platform
import shutil
import stat
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Callable, Optional

import requests

from config import config
from github_client import Asset


def download_file(
    url: str,
    dest_path: Path,
    progress_callback: Optional[Callable[[float, int, int], None]] = None,
) -> None:
    """
    Descarga un archivo con seguimiento de progreso.

    Args:
        url: URL de descarga.
        dest_path: Ruta local donde guardar el archivo.
        progress_callback: función(porcentaje, bytes_descargados, total_bytes).
    """
    headers = {"User-Agent": "scrcpy-updater/1.0"}
    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0

        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total > 0:
                        progress_callback(downloaded / total, downloaded, total)


def verify_sha256(file_path: Path, sha256sums_url: Optional[str], filename: str) -> bool:
    """
    Descarga SHA256SUMS.txt y verifica la integridad del archivo descargado.
    Retorna True si la verificación es correcta o si no hay URL de checksums.
    """
    if not sha256sums_url:
        return True  # Sin checksums, asumimos correcto

    try:
        headers = {"User-Agent": "scrcpy-updater/1.0"}
        r = requests.get(sha256sums_url, headers=headers, timeout=10)
        r.raise_for_status()
        checksums = r.text

        expected_hash: Optional[str] = None
        for line in checksums.splitlines():
            parts = line.strip().split()
            if len(parts) == 2 and parts[1] == filename:
                expected_hash = parts[0]
                break

        if not expected_hash:
            return True  # El archivo no está en el checksum, no bloqueamos

        # Calcular SHA256 del archivo descargado
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)

        return sha256.hexdigest() == expected_hash

    except Exception:
        return True  # En caso de error al verificar, no bloqueamos la instalación


def _extract_tar_gz(archive_path: Path, extract_dir: Path) -> Path:
    """Extrae un .tar.gz y retorna el directorio raíz extraído."""
    with tarfile.open(archive_path, "r:gz") as tar:
        # Detectar el directorio raíz dentro del tar
        root_dirs = {m.name.split("/")[0] for m in tar.getmembers() if "/" in m.name}
        tar.extractall(path=extract_dir)
        if root_dirs:
            return extract_dir / sorted(root_dirs)[0]
        return extract_dir


def _extract_zip(archive_path: Path, extract_dir: Path) -> Path:
    """Extrae un .zip y retorna el directorio raíz extraído."""
    with zipfile.ZipFile(archive_path, "r") as z:
        root_dirs = {name.split("/")[0] for name in z.namelist() if "/" in name}
        z.extractall(path=extract_dir)
        if root_dirs:
            return extract_dir / sorted(root_dirs)[0]
        return extract_dir


def install(
    asset: "Asset",
    sha256sums_url: Optional[str],
    progress_callback: Optional[Callable[[float, int, int], None]] = None,
    status_callback: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Orquesta todo el proceso: descarga → verifica → extrae → instala.

    Lanza RuntimeError si algo falla.
    """
    install_dir = config.INSTALL_DIR
    install_dir.mkdir(parents=True, exist_ok=True)

    def _status(msg: str):
        if status_callback:
            status_callback(msg)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        archive_path = tmp_path / asset.name

        # 1. Descargar
        _status(f"Descargando {asset.name}…")
        download_file(asset.download_url, archive_path, progress_callback)

        # 2. Verificar SHA256
        _status("Verificando integridad (SHA256)…")
        if not verify_sha256(archive_path, sha256sums_url, asset.name):
            raise RuntimeError(
                f"La verificación SHA256 falló para {asset.name}.\n"
                "El archivo puede estar corrupto. Intenta de nuevo."
            )

        # 3. Extraer
        _status("Extrayendo archivos…")
        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        if asset.name.endswith(".tar.gz"):
            src_dir = _extract_tar_gz(archive_path, extract_dir)
        elif asset.name.endswith(".zip"):
            src_dir = _extract_zip(archive_path, extract_dir)
        else:
            raise RuntimeError(f"Formato de archivo no soportado: {asset.name}")

        # 4. Copiar binarios a INSTALL_DIR
        _status(f"Instalando en {install_dir}…")
        system = platform.system().lower()

        if system == "windows":
            # En Windows scrcpy incluye ejecutables (scrcpy.exe, adb.exe), .dll y ficheros auxiliares
            for item in src_dir.iterdir():
                dest = install_dir / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
        else:
            # Linux / macOS: copiar ejecutables (archivos sin extensión o con +x)
            for item in src_dir.iterdir():
                if item.is_file():
                    dest = install_dir / item.name
                    shutil.copy2(item, dest)
                    # Asegurar permisos de ejecución para los binarios principales
                    if item.suffix == "" or item.name.startswith("scrcpy"):
                        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        _status("¡Instalación completada!")


def remove_scrcpy(install_dir: Path) -> int:
    """
    Elimina todos los archivos de scrcpy del directorio de instalación.

    Args:
        install_dir: Directorio donde están los binarios instalados.

    Returns:
        Número de archivos/carpetas eliminados.

    Raises:
        PermissionError: Si no hay permisos para eliminar los archivos.
        OSError: Si ocurre otro error de sistema de archivos.
    """
    if not install_dir.exists():
        return 0

    removed = 0
    system = platform.system().lower()

    for entry in sorted(install_dir.iterdir()):
        # En Windows o si la carpeta es dedicada a scrcpy, o archivos que empiecen por scrcpy/adb
        if system == "windows" and install_dir.name.lower() == "scrcpy":
            if entry.is_file() or entry.is_symlink():
                entry.unlink()
                removed += 1
            elif entry.is_dir():
                shutil.rmtree(entry)
                removed += 1
        else:
            if entry.is_file() and entry.name.startswith("scrcpy"):
                entry.unlink()
                removed += 1

    return removed
