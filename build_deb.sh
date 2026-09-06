#!/usr/bin/env bash
# ============================================================
#  build_deb.sh — Construye el paquete .deb de scrcpy_update
# ============================================================
#
#  Uso:
#    ./build_deb.sh           Construye el .deb (amd64 por defecto)
#    ./build_deb.sh --clean   Limpia los artefactos de build previos
#
#  Requisitos:
#    - python3 + pip3
#    - pyinstaller  (se instala automáticamente si no está)
#    - dpkg-deb
# ============================================================

set -euo pipefail

# ── Configuración y Versionado automático ───────────────────
PKG_NAME="scrcpy-update"
ARCH="amd64"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="${SCRIPT_DIR}/VERSION"

# Leer y auto-incrementar la versión (patch version: X.Y.Z -> X.Y.Z+1)
if [[ ! -f "${VERSION_FILE}" ]]; then
    echo "1.0.0" > "${VERSION_FILE}"
fi

CURRENT_VERSION=$(tr -d '[:space:]' < "${VERSION_FILE}")
IFS='.' read -r V_MAJOR V_MINOR V_PATCH <<< "${CURRENT_VERSION}"
V_PATCH=$((V_PATCH + 1))
NEW_VERSION="${V_MAJOR}.${V_MINOR}.${V_PATCH}"
echo "${NEW_VERSION}" > "${VERSION_FILE}"
PKG_VERSION="${NEW_VERSION}"

# Sincronizar versión en main.py
sed -i "s/^APP_VERSION = .*/APP_VERSION = \"${PKG_VERSION}\"/" "${SCRIPT_DIR}/main.py"

BUILD_DIR="${SCRIPT_DIR}/build"
DEB_ROOT="${BUILD_DIR}/${PKG_NAME}_${PKG_VERSION}_${ARCH}"
DEB_OUT="${SCRIPT_DIR}/dist"
BINARY_NAME="scrcpy_update"

# ── Colores ──────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }
step()    { echo -e "\n${BOLD}━━━  $* ${NC}"; }

# ── Limpieza ─────────────────────────────────────────────────
if [[ "${1:-}" == "--clean" ]]; then
    info "Limpiando artefactos de build anteriores…"
    rm -rf "${BUILD_DIR}" "${SCRIPT_DIR}/dist" "${SCRIPT_DIR}"/*.spec
    success "Limpieza completada."
    exit 0
fi

echo -e "${BOLD}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║        Build: ${PKG_NAME} v${PKG_VERSION} (${ARCH})          ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Paso 1: Verificar herramientas ───────────────────────────
step "1/6  Verificando dependencias de build"

command -v python3 &>/dev/null || error "python3 no encontrado."
command -v dpkg-deb &>/dev/null || error "dpkg-deb no encontrado. Instala: sudo apt install dpkg-dev"
command -v pyinstaller &>/dev/null || error "pyinstaller no encontrado. Instala con: pip3 install pyinstaller --break-system-packages"

python3 -c "import customtkinter" &>/dev/null || error "customtkinter no encontrado. Instala con: pip3 install customtkinter --break-system-packages"
python3 -c "import requests"      &>/dev/null || error "requests no encontrado. Instala con: pip3 install requests --break-system-packages"
python3 -c "import dotenv"        &>/dev/null || error "python-dotenv no encontrado. Instala con: pip3 install python-dotenv --break-system-packages"
python3 -c "import PIL"           &>/dev/null || error "Pillow no encontrado. Instala con: pip3 install Pillow --break-system-packages"

success "Todas las dependencias listas."

# ── Paso 2: Compilar con PyInstaller ─────────────────────────
step "2/6  Compilando con PyInstaller (puede tardar ~1-2 min)"

cd "${SCRIPT_DIR}"

# Obtener ruta de customtkinter para incluir sus assets (temas, fuentes)
CTK_PATH=$(python3 -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))")

pyinstaller \
    --onefile \
    --name "${BINARY_NAME}" \
    --add-data "${CTK_PATH}:customtkinter" \
    --add-data "${SCRIPT_DIR}/.env:." \
    --hidden-import "PIL._tkinter_finder" \
    --hidden-import "customtkinter" \
    --collect-all "customtkinter" \
    --distpath "${BUILD_DIR}/bin" \
    --workpath "${BUILD_DIR}/pyinstaller_work" \
    --specpath "${BUILD_DIR}" \
    --noconfirm \
    --clean \
    "${SCRIPT_DIR}/main.py" 2>&1 | tail -5

BINARY_PATH="${BUILD_DIR}/bin/${BINARY_NAME}"
[[ -f "${BINARY_PATH}" ]] || error "PyInstaller no generó el binario en ${BINARY_PATH}"
success "Binario generado: ${BINARY_PATH} ($(du -sh "${BINARY_PATH}" | cut -f1))"

# ── Paso 3: Crear estructura del paquete .deb ─────────────────
step "3/6  Creando estructura del paquete .deb"

# Directorios
mkdir -p "${DEB_ROOT}/DEBIAN"
mkdir -p "${DEB_ROOT}/usr/bin"
mkdir -p "${DEB_ROOT}/usr/share/applications"
mkdir -p "${DEB_ROOT}/usr/share/doc/${PKG_NAME}"
mkdir -p "${DEB_ROOT}/usr/share/pixmaps"

# Copiar binario
cp "${BINARY_PATH}" "${DEB_ROOT}/usr/bin/${BINARY_NAME}"
chmod 755 "${DEB_ROOT}/usr/bin/${BINARY_NAME}"

# Copiar desktop entry
cp "${SCRIPT_DIR}/debian/scrcpy-update.desktop" \
   "${DEB_ROOT}/usr/share/applications/scrcpy-update.desktop"

# Crear icono SVG básico (se puede reemplazar por uno real)
cat > "${DEB_ROOT}/usr/share/pixmaps/scrcpy-update.svg" <<'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <rect width="48" height="48" rx="8" fill="#1565C0"/>
  <rect x="12" y="8" width="18" height="30" rx="3" fill="white" opacity="0.9"/>
  <rect x="14" y="10" width="14" height="24" rx="2" fill="#1565C0"/>
  <circle cx="21" cy="36" r="2" fill="#1565C0"/>
  <path d="M32 20 L42 20 M38 16 L42 20 L38 24" stroke="white" stroke-width="2.5" stroke-linecap="round" fill="none"/>
</svg>
SVGEOF

# Copyright
cat > "${DEB_ROOT}/usr/share/doc/${PKG_NAME}/copyright" <<'EOF'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/

Files: *
License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction.
EOF

# changelog comprimido
cat > "${BUILD_DIR}/changelog" <<EOF
${PKG_NAME} (${PKG_VERSION}) stable; urgency=low

  * Versión inicial.
  * Interfaz gráfica con CustomTkinter.
  * Soporte para todas las plataformas de scrcpy.
  * Verificación SHA256 de descargas.
  * Parámetros CLI: --help, --remove, --version.

 -- scrcpy-update <noreply@scrcpy-update>  $(date -R)
EOF
gzip -9 -n -f "${BUILD_DIR}/changelog"
cp "${BUILD_DIR}/changelog.gz" "${DEB_ROOT}/usr/share/doc/${PKG_NAME}/"

success "Estructura del paquete creada."

# ── Paso 4: Scripts DEBIAN ────────────────────────────────────
step "4/6  Configurando scripts de mantenedor"

cp "${SCRIPT_DIR}/debian/postinst" "${DEB_ROOT}/DEBIAN/postinst"
cp "${SCRIPT_DIR}/debian/prerm"    "${DEB_ROOT}/DEBIAN/prerm"
chmod 755 "${DEB_ROOT}/DEBIAN/postinst" "${DEB_ROOT}/DEBIAN/prerm"

success "Scripts de mantenedor configurados."

# ── Paso 5: Generar DEBIAN/control ────────────────────────────
step "5/6  Generando DEBIAN/control"

# Calcular tamaño instalado en KB
INSTALLED_SIZE=$(du -sk "${DEB_ROOT}" | cut -f1)

sed -e "s/INSTALLED_SIZE_PLACEHOLDER/${INSTALLED_SIZE}/" \
    -e "s/VERSION_PLACEHOLDER/${PKG_VERSION}/" \
    "${SCRIPT_DIR}/debian/control" > "${DEB_ROOT}/DEBIAN/control"

success "control generado (tamaño instalado: ~${INSTALLED_SIZE} KB)."

# ── Paso 6: Construir el .deb ─────────────────────────────────
step "6/6  Construyendo el paquete .deb"

mkdir -p "${DEB_OUT}"
DEB_FILE="${DEB_OUT}/${PKG_NAME}_${PKG_VERSION}_${ARCH}.deb"

dpkg-deb --build --root-owner-group "${DEB_ROOT}" "${DEB_FILE}"

[[ -f "${DEB_FILE}" ]] || error "dpkg-deb no generó el archivo."

# ── Resumen ───────────────────────────────────────────────────
echo
echo -e "${BOLD}${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║              ✅  Build completado                    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  Paquete : ${CYAN}${DEB_FILE}${NC}"
echo -e "  Tamaño  : $(du -sh "${DEB_FILE}" | cut -f1)"
echo
echo -e "  Para instalar:"
echo -e "    ${BOLD}sudo dpkg -i ${DEB_FILE}${NC}"
echo
echo -e "  Para desinstalar:"
echo -e "    ${BOLD}sudo dpkg -r ${PKG_NAME}${NC}"
echo
echo -e "  Verificar paquete:"
echo -e "    ${BOLD}dpkg-deb --info ${DEB_FILE}${NC}"
echo
