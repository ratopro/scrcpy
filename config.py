"""
config.py — Carga la configuración desde .env
"""
import os
import platform
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde el directorio del script
_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path)


def _detect_platform() -> str:
    """Detecta el sufijo del asset de scrcpy según el sistema operativo y arquitectura."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        if machine in ("x86_64", "amd64"):
            return "linux-x86_64"
        elif machine in ("aarch64", "arm64"):
            return "linux-aarch64"
        else:
            return f"linux-{machine}"
    elif system == "windows":
        if machine in ("amd64", "x86_64"):
            return "win64"
        else:
            return "win32"
    elif system == "darwin":
        if machine in ("arm64", "aarch64"):
            return "macos-aarch64"
        else:
            return "macos-x86_64"
    else:
        return "linux-x86_64"


def _default_install_dir() -> Path:
    """Ruta de instalación por defecto adaptada a la plataforma."""
    if platform.system().lower() == "windows":
        local_appdata = os.getenv("LOCALAPPDATA")
        if local_appdata:
            return Path(local_appdata) / "Programs" / "scrcpy"
        return Path.home() / "AppData" / "Local" / "Programs" / "scrcpy"
    return Path(os.path.expanduser(os.getenv("INSTALL_DIR", "~/.local/bin")))


class Config:
    GITHUB_API_URL: str = os.getenv(
        "GITHUB_API_URL",
        "https://api.github.com/repos/Genymobile/scrcpy/releases",
    )
    INSTALL_DIR: Path = (
        Path(os.path.expanduser(os.getenv("INSTALL_DIR")))
        if os.getenv("INSTALL_DIR")
        else _default_install_dir()
    )
    PLATFORM: str = os.getenv("SCRCPY_PLATFORM", _detect_platform())

    # Extensión del archivo según plataforma
    @property
    def asset_extension(self) -> str:
        if self.PLATFORM.startswith("win"):
            return ".zip"
        return ".tar.gz"

    def asset_name_for(self, version_tag: str) -> str:
        """Devuelve el nombre del asset esperado para una versión dada."""
        ext = self.asset_extension
        return f"scrcpy-{self.PLATFORM}-{version_tag}{ext}"


config = Config()
