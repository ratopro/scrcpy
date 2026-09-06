"""
scrcpy_detector.py — Detecta si scrcpy está instalado y cuál es su versión.
"""
import re
import shutil
import subprocess
from typing import Optional


def get_installed_version() -> Optional[str]:
    """
    Ejecuta `scrcpy --version` y extrae la versión instalada.
    Retorna la versión como string (ej: "3.3.4") o None si no está instalado.
    """
    from config import config

    # 1. Buscar en PATH
    scrcpy_bin = shutil.which("scrcpy")

    # 2. Si no está en PATH, verificar en el directorio de instalación configurado
    if not scrcpy_bin and config.INSTALL_DIR.exists():
        candidate_exe = config.INSTALL_DIR / "scrcpy.exe"
        candidate_bin = config.INSTALL_DIR / "scrcpy"
        if candidate_exe.is_file():
            scrcpy_bin = str(candidate_exe)
        elif candidate_bin.is_file():
            scrcpy_bin = str(candidate_bin)

    if not scrcpy_bin:
        return None

    try:
        result = subprocess.run(
            [scrcpy_bin, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout + result.stderr
        # Buscar patrón: "scrcpy X.Y.Z" o "scrcpy vX.Y.Z"
        match = re.search(r"scrcpy\s+v?(\d+\.\d+(?:\.\d+)?)", output)
        if match:
            return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None


def version_tuple(version_str: str) -> tuple:
    """Convierte '3.3.4' en (3, 3, 4) para comparación."""
    parts = version_str.lstrip("v").split(".")
    return tuple(int(p) for p in parts if p.isdigit())


def is_newer(remote_version: str, local_version: Optional[str]) -> bool:
    """
    Retorna True si la versión remota es más nueva que la local.
    Si no hay versión local, siempre es True.
    """
    if local_version is None:
        return True
    try:
        return version_tuple(remote_version) > version_tuple(local_version)
    except (ValueError, TypeError):
        return False
