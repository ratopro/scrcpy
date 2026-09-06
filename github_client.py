"""
github_client.py — Consulta la API de GitHub para obtener releases de scrcpy.
"""
import requests
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Asset:
    name: str
    download_url: str
    size: int  # bytes

    @property
    def size_mb(self) -> float:
        return self.size / (1024 * 1024)


@dataclass
class Release:
    tag: str          # "v4.1"
    name: str         # "scrcpy 4.1"
    published_at: str # "2026-07-12T18:15:37Z"
    assets: List[Asset] = field(default_factory=list)
    sha256_url: Optional[str] = None  # URL del SHA256SUMS.txt

    @property
    def version(self) -> str:
        """Retorna la versión sin la 'v' (ej: '4.1')."""
        return self.tag.lstrip("v")

    @property
    def date_short(self) -> str:
        """Fecha en formato legible (ej: '2026-07-12')."""
        return self.published_at[:10]

    def find_asset(self, platform: str) -> Optional[Asset]:
        """Busca el asset que corresponde a la plataforma dada."""
        for asset in self.assets:
            if platform in asset.name and asset.name not in (
                "SHA256SUMS.txt",
                "SHA256SUMS.txt.asc",
            ):
                return asset
        return None


def fetch_releases(api_url: str, per_page: int = 20) -> List[Release]:
    """
    Descarga la lista de releases desde la API de GitHub.
    Lanza requests.RequestException si hay problemas de red.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "scrcpy-updater/1.0",
    }
    params = {"per_page": per_page}

    response = requests.get(api_url, headers=headers, params=params, timeout=15)
    response.raise_for_status()

    releases: List[Release] = []
    for item in response.json():
        if item.get("draft") or item.get("prerelease"):
            continue  # Omitir borradores y pre-releases

        assets: List[Asset] = []
        sha256_url: Optional[str] = None

        for a in item.get("assets", []):
            if a["name"] == "SHA256SUMS.txt":
                sha256_url = a["browser_download_url"]
            elif not a["name"].endswith(".asc") and a["name"] != "scrcpy-server":
                # Filtrar solo assets de plataforma (excluir server y .asc)
                name_lower = a["name"].lower()
                if any(
                    ext in name_lower
                    for ext in [".tar.gz", ".zip"]
                ):
                    assets.append(
                        Asset(
                            name=a["name"],
                            download_url=a["browser_download_url"],
                            size=a["size"],
                        )
                    )

        releases.append(
            Release(
                tag=item["tag_name"],
                name=item["name"],
                published_at=item.get("published_at", ""),
                assets=assets,
                sha256_url=sha256_url,
            )
        )

    return releases
