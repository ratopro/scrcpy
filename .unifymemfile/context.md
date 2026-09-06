# Project Context

## Session 2026-09-06-13:00

### Summary

Creación e implementación completa de Actualizador Scrcpy (Python + CustomTkinter) con soporte multiplataforma (Linux/Windows/macOS), empaquetado .deb para Linux y compilación automática de .exe para Windows en GitHub Actions.

### Current State

Versión v1.0.2 publicada en GitHub (ratopro/scrcpy). Binarios disponibles: .deb para Linux (45.99MB) y .exe para Windows (20.01MB). Repositorio sincronizado con README, CI workflow de GitHub Actions, versionado automático por compilación y atajos de zoom (Ctrl +/-).

### Recent Changes

1. Implementación de app.py, main.py, config.py, installer.py, github_client.py, scrcpy_detector.py. 2. Empaquetado Debian con build_deb.sh y versionado automático via VERSION. 3. Ajuste de fuentes grandes y zoom Ctrl +/- en app.py. 4. Soporte nativo para Windows (build_windows.bat y rutas %LOCALAPPDATA%). 5. Repositorio GitHub creado y subido a https://github.com/ratopro/scrcpy. 6. Flujo GitHub Actions (.github/workflows/build.yml) que compila .exe en Windows y lo adjunta a la release.

### Decisions

Stack seleccionado: Python 3.12 + CustomTkinter por consistencia multiplataforma. Distribución en Linux vía .deb con PyInstaller (--onefile). Distribución en Windows vía .exe standalone compilado en runner windows-latest de GitHub Actions. Versionado semántico autoincremental en cada compilación.

