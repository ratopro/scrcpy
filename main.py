"""
main.py — Punto de entrada de scrcpy_update.

Uso:
  scrcpy_update              Abre la interfaz gráfica
  scrcpy_update --help       Muestra esta ayuda
  scrcpy_update --remove     Elimina scrcpy del directorio de instalación
  scrcpy_update --version    Muestra la versión de esta aplicación
"""
import sys

APP_VERSION = "1.0.2"

HELP_TEXT = """
╔══════════════════════════════════════════════════════════════════╗
║               scrcpy_update  v{version}                              ║
║        Instalador y actualizador gráfico de scrcpy               ║
╚══════════════════════════════════════════════════════════════════╝

DESCRIPCIÓN:
  Aplicación de escritorio para instalar, actualizar o eliminar scrcpy
  directamente desde las releases oficiales de GitHub.
  Detecta automáticamente la versión instalada y la plataforma del sistema.

USO:
  scrcpy_update              Abre la interfaz gráfica
  scrcpy_update --help       Muestra esta ayuda y sale
  scrcpy_update -h           Igual que --help
  scrcpy_update --remove     Elimina scrcpy del directorio de instalación
  scrcpy_update -remove      Igual que --remove
  scrcpy_update --version    Muestra la versión de esta aplicación
  scrcpy_update -v           Igual que --version

PARÁMETROS:
  (sin parámetros)   Lanza la interfaz gráfica de escritorio.
  --help, -h         Muestra esta pantalla de ayuda y termina.
  --remove, -remove  Elimina los binarios de scrcpy instalados por
                     scrcpy_update del directorio configurado en .env.
                     Solicita confirmación antes de borrar.
  --version, -v      Muestra la versión de scrcpy_update instalada.

CONFIGURACIÓN (.env):
  GITHUB_API_URL     URL de la API de GitHub para obtener las releases.
                     Por defecto: https://api.github.com/repos/Genymobile/scrcpy/releases
  INSTALL_DIR        Directorio donde se instalan los binarios de scrcpy.
                     Por defecto: ~/.local/bin
  SCRCPY_PLATFORM    Plataforma del asset a descargar (auto-detectada).
                     Valores: linux-x86_64 | linux-aarch64 | win64 | win32
                              macos-aarch64 | macos-x86_64

EJEMPLOS:
  # Abrir la interfaz gráfica
  scrcpy_update

  # Ver la versión de la herramienta
  scrcpy_update --version

  # Eliminar scrcpy del sistema
  scrcpy_update --remove

NOTAS:
  - La instalación se realiza en INSTALL_DIR (por defecto ~/.local/bin).
    Asegúrate de que ese directorio esté en tu PATH.
  - Para instalar en /usr/local/bin necesitarás permisos de administrador.
  - Se verifica la integridad SHA256 de cada descarga automáticamente.
  - No se requiere token de GitHub para uso normal (límite: 60 req/hora).

MÁS INFORMACIÓN:
  scrcpy: https://github.com/Genymobile/scrcpy
""".format(version=APP_VERSION)


def cmd_help():
    print(HELP_TEXT)
    sys.exit(0)


def cmd_version():
    print(f"scrcpy_update v{APP_VERSION}")
    sys.exit(0)


def cmd_remove():
    """Elimina scrcpy del directorio de instalación con confirmación."""
    from installer import remove_scrcpy
    from config import config
    from scrcpy_detector import get_installed_version

    installed = get_installed_version()
    install_dir = config.INSTALL_DIR

    print(f"scrcpy_update v{APP_VERSION} — Desinstalador")
    print(f"{'─' * 50}")

    if installed:
        print(f"Versión detectada : scrcpy v{installed}")
    else:
        print("scrcpy no se detectó en PATH.")

    print(f"Directorio        : {install_dir}")
    print()

    # Listar archivos a eliminar
    import platform
    is_windows_dir = platform.system().lower() == "windows" and install_dir.name.lower() == "scrcpy"
    if install_dir.exists():
        if is_windows_dir:
            files_to_remove = list(install_dir.iterdir())
        else:
            files_to_remove = list(install_dir.glob("scrcpy*"))
    else:
        files_to_remove = []

    if not files_to_remove:
        print("⚠  No se encontraron archivos de scrcpy en el directorio de instalación.")
        print(f"   Comprueba manualmente: {install_dir}")
        sys.exit(0)

    print("Archivos que se eliminarán:")
    for f in sorted(files_to_remove):
        size_kb = f.stat().st_size / 1024 if f.is_file() else 0
        print(f"  ✗  {f.name}  ({size_kb:.0f} KB)")

    print()
    answer = input("¿Confirmas la eliminación? [s/N]: ").strip().lower()

    if answer not in ("s", "si", "sí", "y", "yes"):
        print("Operación cancelada.")
        sys.exit(0)

    try:
        removed = remove_scrcpy(install_dir)
        print(f"\n✅  Se eliminaron {removed} archivo(s) de scrcpy correctamente.")
    except Exception as e:
        print(f"\n❌  Error al eliminar: {e}")
        sys.exit(1)


def main():
    args = sys.argv[1:]

    # Parseo manual para soporte de -remove (un guión) y --remove (dos guiones)
    normalized = []
    for a in args:
        # Normalizar -remove → --remove, -h → --help, -v → --version
        if a in ("-remove",):
            normalized.append("--remove")
        elif a in ("-h",):
            normalized.append("--help")
        elif a in ("-v",):
            normalized.append("--version")
        else:
            normalized.append(a)

    if "--help" in normalized:
        cmd_help()
    elif "--version" in normalized:
        cmd_version()
    elif "--remove" in normalized:
        cmd_remove()
    else:
        # Sin argumentos → lanzar GUI
        from app import ScrcpyUpdaterApp
        app = ScrcpyUpdaterApp()
        app.mainloop()


if __name__ == "__main__":
    main()
