# 📱 Actualizador Scrcpy (scrcpy_update)

Aplicación gráfica de escritorio y herramienta CLI para instalar, actualizar y gestionar [scrcpy](https://github.com/Genymobile/scrcpy) de forma rápida y sencilla directamente desde las versiones oficiales publicadas en GitHub.

---

## ✨ Características

- 🖥️ **Interfaz gráfica moderna:** Desarrollada con CustomTkinter, adaptable a tema oscuro/claro del sistema.
- 🔍 **Detección automática:** Identifica al instante si tienes una versión de `scrcpy` instalada en tu sistema y cuál es.
- 🌐 **Catálogo oficial de GitHub:** Consulta en tiempo real las versiones publicadas con indicadores visuales (`LATEST`, `INSTALADA`, `▲ ACTUALIZACIÓN`).
- ⚡ **Multiplataforma:** Detección de arquitectura y sistema operativo:
  - **Linux** (`linux-x86_64`, `linux-aarch64`)
  - **Windows** (`win64`, `win32`)
  - **macOS** (`macos-x86_64`, `macos-aarch64`)
- 🔒 **Verificación de integridad:** Valida automáticamente el hash SHA256 contra los archivos oficiales `SHA256SUMS.txt`.
- 🔎 **Control de Zoom y Escala:**
  - `Ctrl` + `+` : Aumenta la escala de la interfaz progresivamente (+10%).
  - `Ctrl` + `-` : Reduce la escala de la interfaz progresivamente (-10%).
  - `Ctrl` + `0` : Restablece la escala al 100%.
- 💻 **Modo consola / CLI completo:**
  - `scrcpy_update --help`
  - `scrcpy_update --version`
  - `scrcpy_update --remove`

---

## 📦 Descargas (Releases)

Puedes descargar los instaladores y paquetes precompilados en la sección de **Releases** de GitHub:

- **Linux (Debian / Ubuntu / Mint):** Descarga el paquete `.deb` (`scrcpy-update_1.0.2_amd64.deb`).
  ```bash
  sudo dpkg -i scrcpy-update_1.0.2_amd64.deb
  ```
- **Windows (10 / 11):** Descarga el ejecutable standalone portátil (`scrcpy_update.exe`), sin necesidad de instalar Python ni dependencias. Haz doble clic y listo.

---

## 🚀 Uso desde Terminal

Una vez instalado en el sistema, dispones de los siguientes comandos:

```bash
# Abrir la interfaz gráfica
scrcpy_update

# Ver ayuda y parámetros disponibles
scrcpy_update --help

# Comprobar la versión instalada de la herramienta
scrcpy_update --version

# Desinstalar scrcpy del sistema (pide confirmación)
scrcpy_update --remove
```

---

## 🛠️ Ejecución y Desarrollo desde Código Fuente

### Requisitos previos
- Python 3.10 o superior
- Tkinter instalado en el sistema (`sudo apt install python3-tk` en Linux)

### Instalación de dependencias
```bash
git clone https://github.com/ratopro/scrcpy.git
cd scrcpy
pip install -r requirements.txt
```

### Ejecutar la aplicación
```bash
python3 main.py
```

---

## 🏗️ Compilación de Paquetes

### En Linux (Generar paquete `.deb`):
El script incrementa automáticamente la versión y genera el paquete standalone en `dist/`:
```bash
chmod +x build_deb.sh
./build_deb.sh
```

### En Windows (Generar `.exe`):
Ejecuta el archivo por lotes en una consola de comandos de Windows:
```cmd
build_windows.bat
```

---

## 📄 Licencia

Distribuido bajo licencia MIT. Consulta el archivo `LICENSE` para más detalles.
