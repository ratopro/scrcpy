"""
app.py — Interfaz gráfica principal con CustomTkinter.
"""
import threading
from typing import List, Optional

import customtkinter as ctk
from PIL import Image, ImageDraw

from config import config
from github_client import Release, fetch_releases
from installer import install
from scrcpy_detector import get_installed_version, is_newer

# ── Tema ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("system")   # Respeta el tema del sistema (dark/light)
ctk.set_default_color_theme("blue")


# ── Colores badge ─────────────────────────────────────────────────────────────
COLOR_LATEST      = ("#1E88E5", "#1565C0")
COLOR_INSTALLED   = ("#43A047", "#2E7D32")
COLOR_AVAILABLE   = ("#757575", "#424242")
COLOR_UPDATE      = ("#FB8C00", "#E65100")

FONT_TITLE  = ("Helvetica", 24, "bold")
FONT_LABEL  = ("Helvetica", 16)
FONT_ROW    = ("Helvetica", 18, "bold")
FONT_SMALL  = ("Helvetica", 14)
FONT_BADGE  = ("Helvetica", 13, "bold")
FONT_BUTTON = ("Helvetica", 16, "bold")


class ScrcpyUpdaterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Actualizador Scrcpy")
        self.geometry("960x740")
        self.minsize(800, 600)
        self.resizable(True, True)

        # Estado
        self._releases: List[Release] = []
        self._installed_version: Optional[str] = None
        self._selected_release: Optional[Release] = None
        self._installing = False
        self._current_scaling = 1.0

        self._build_ui()
        self._start_loading()

        # Atajos de teclado: Ctrl + "más" y Ctrl + "menos" para ajustar escala progresivamente
        self.bind_all("<Control-plus>", self._zoom_in)
        self.bind_all("<Control-KP_Add>", self._zoom_in)
        self.bind_all("<Control-equal>", self._zoom_in)
        self.bind_all("<Control-minus>", self._zoom_out)
        self.bind_all("<Control-KP_Subtract>", self._zoom_out)
        self.bind_all("<Control-0>", self._zoom_reset)

    def _zoom_in(self, event=None):
        """Aumenta la escala de la interfaz progresivamente."""
        new_scale = round(self._current_scaling + 0.1, 2)
        if new_scale <= 2.2:
            self._current_scaling = new_scale
            ctk.set_widget_scaling(self._current_scaling)
            self._set_status(f"Escala: {int(self._current_scaling * 100)}% (Ctrl + / Ctrl -)")

    def _zoom_out(self, event=None):
        """Reduce la escala de la interfaz progresivamente."""
        new_scale = round(self._current_scaling - 0.1, 2)
        if new_scale >= 0.7:
            self._current_scaling = new_scale
            ctk.set_widget_scaling(self._current_scaling)
            self._set_status(f"Escala: {int(self._current_scaling * 100)}% (Ctrl + / Ctrl -)")

    def _zoom_reset(self, event=None):
        """Restablece la escala al 100%."""
        self._current_scaling = 1.0
        ctk.set_widget_scaling(1.0)
        self._set_status("Escala restablecida al 100%")

    # ─────────────────────────────────────────────────────────── BUILD UI ─────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "gray15"))
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="📱  Actualizador Scrcpy", font=FONT_TITLE
        ).grid(row=0, column=0, padx=20, pady=14, sticky="w")

        self.lbl_installed = ctk.CTkLabel(
            header, text="Detectando versión instalada…", font=FONT_LABEL,
            text_color=("gray40", "gray70")
        )
        self.lbl_installed.grid(row=0, column=1, padx=20, pady=14, sticky="e")

        # ── Info plataforma y atajos ───────────────────────────────────────────
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(8, 0))
        ctk.CTkLabel(
            info_frame,
            text=f"Plataforma: {config.PLATFORM}  |  "
                 f"Destino: {config.INSTALL_DIR}  |  "
                 f"Zoom: Ctrl + / Ctrl - (Ctrl 0 restablece)",
            font=FONT_SMALL,
            text_color=("gray50", "gray60"),
        ).pack(side="left")

        # ── Lista de releases ──────────────────────────────────────────────────
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=12)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(list_frame, text="Versiones disponibles", font=FONT_LABEL).grid(
            row=0, column=0, padx=14, pady=(10, 4), sticky="w"
        )

        self.scroll_frame = ctk.CTkScrollableFrame(list_frame, label_text="")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.lbl_loading = ctk.CTkLabel(
            self.scroll_frame, text="⏳  Cargando lista de versiones…", font=FONT_LABEL
        )
        self.lbl_loading.grid(row=0, column=0, padx=20, pady=40)

        # ── Panel inferior ─────────────────────────────────────────────────────
        bottom = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "gray15"))
        bottom.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        bottom.grid_columnconfigure(0, weight=1)

        self.lbl_asset = ctk.CTkLabel(
            bottom, text="", font=FONT_SMALL, text_color=("gray50", "gray60")
        )
        self.lbl_asset.grid(row=0, column=0, padx=20, pady=(10, 2), sticky="w")

        self.progress_bar = ctk.CTkProgressBar(bottom)
        self.progress_bar.grid(row=1, column=0, padx=20, pady=(0, 4), sticky="ew")
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()  # Oculto hasta descarga

        self.lbl_status = ctk.CTkLabel(
            bottom, text="", font=FONT_SMALL, text_color=("gray50", "gray60")
        )
        self.lbl_status.grid(row=2, column=0, padx=20, pady=(0, 4), sticky="w")

        self.btn_install = ctk.CTkButton(
            bottom,
            text="Selecciona una versión",
            state="disabled",
            command=self._on_install_click,
            height=42,
            font=FONT_BUTTON,
        )
        self.btn_install.grid(row=3, column=0, padx=20, pady=(4, 14), sticky="e")

    # ─────────────────────────────────────────────────────── LOADING DATA ─────

    def _start_loading(self):
        """Inicia la carga de versión local y releases en hilos separados."""
        threading.Thread(target=self._load_data, daemon=True).start()

    def _load_data(self):
        # Detectar versión local
        installed = get_installed_version()
        self._installed_version = installed
        self.after(0, self._update_installed_label, installed)

        # Cargar releases de GitHub
        try:
            releases = fetch_releases(config.GITHUB_API_URL)
            self._releases = releases
            self.after(0, self._populate_releases, releases)
        except Exception as e:
            self.after(0, self._show_error, f"Error al cargar releases:\n{e}")

    def _update_installed_label(self, version: Optional[str]):
        if version:
            self.lbl_installed.configure(
                text=f"✅  Instalada: v{version}",
                text_color=("#2E7D32", "#66BB6A"),
            )
        else:
            self.lbl_installed.configure(
                text="⚠️  scrcpy no detectado",
                text_color=("#E65100", "#FFA726"),
            )

    # ───────────────────────────────────────────────────── POPULATE LIST ──────

    def _populate_releases(self, releases: List[Release]):
        """Renderiza la lista de releases en el scroll frame."""
        # Limpiar contenido previo
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not releases:
            ctk.CTkLabel(
                self.scroll_frame, text="No se encontraron releases.", font=FONT_LABEL
            ).grid(row=0, column=0, pady=40)
            return

        self._release_rows: list = []

        for idx, release in enumerate(releases):
            self._add_release_row(idx, release)

    def _add_release_row(self, idx: int, release: Release):
        """Crea una fila para un release en el scroll frame."""
        installed_v = self._installed_version
        is_first = idx == 0

        # Determinar estado
        asset = release.find_asset(config.PLATFORM)
        tag_clean = release.version  # "4.1"

        if installed_v and tag_clean == installed_v:
            badge_text = "INSTALADA"
            badge_colors = COLOR_INSTALLED
        elif is_first:
            badge_text = "LATEST"
            badge_colors = COLOR_LATEST
        else:
            badge_text = None
            badge_colors = None

        # Si hay update disponible
        update_available = is_newer(tag_clean, installed_v)

        # ── Fila ──────────────────────────────────────────────────────────────
        row_frame = ctk.CTkFrame(
            self.scroll_frame,
            corner_radius=8,
            fg_color=("gray95", "gray20"),
            cursor="hand2",
        )
        row_frame.grid(row=idx, column=0, sticky="ew", padx=4, pady=3)
        row_frame.grid_columnconfigure(1, weight=1)

        # Botón de selección (radio)
        radio_var = ctk.StringVar(value="")
        radio = ctk.CTkRadioButton(
            row_frame,
            text="",
            variable=radio_var,
            value=release.tag,
            width=20,
            command=lambda r=release: self._on_select_release(r),
        )
        radio.grid(row=0, column=0, padx=(12, 4), pady=10)
        self._release_rows.append((radio, radio_var))

        # Versión y fecha
        text_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        text_frame.grid(row=0, column=1, sticky="ew", padx=4)

        ver_label = ctk.CTkLabel(
            text_frame,
            text=f"v{tag_clean}",
            font=FONT_ROW,
            anchor="w",
        )
        ver_label.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            text_frame,
            text=release.date_short,
            font=FONT_SMALL,
            text_color=("gray50", "gray60"),
            anchor="w",
        ).pack(side="left")

        if is_first and update_available and installed_v:
            ctk.CTkLabel(
                text_frame,
                text="▲ ACTUALIZACIÓN",
                font=FONT_BADGE,
                text_color=("#FB8C00", "#FFA726"),
            ).pack(side="left", padx=8)

        # Badge de estado (derecha)
        if badge_text:
            badge = ctk.CTkLabel(
                row_frame,
                text=f" {badge_text} ",
                font=FONT_BADGE,
                corner_radius=4,
                fg_color=badge_colors,
                text_color="white",
            )
            badge.grid(row=0, column=2, padx=8)

        # Asset disponible o no
        asset_info = ctk.CTkLabel(
            row_frame,
            text=f"{'✓' if asset else '✗'} {config.PLATFORM}",
            font=FONT_SMALL,
            text_color=("gray50", "gray60") if not asset else ("gray40", "gray70"),
        )
        asset_info.grid(row=0, column=3, padx=(0, 14))

        # Click en toda la fila selecciona el release
        for widget in [row_frame, text_frame, ver_label, asset_info]:
            widget.bind("<Button-1>", lambda e, r=release: self._on_select_release(r))

    # ──────────────────────────────────────────────────── SELECTION ───────────

    def _on_select_release(self, release: Release):
        if self._installing:
            return

        self._selected_release = release
        asset = release.find_asset(config.PLATFORM)

        # Actualizar UI del asset seleccionado
        if asset:
            self.lbl_asset.configure(
                text=f"📦  {asset.name}   ({asset.size_mb:.1f} MB)"
            )
        else:
            self.lbl_asset.configure(
                text=f"⚠️  No hay asset disponible para {config.PLATFORM} en esta versión."
            )

        # Determinar texto del botón
        installed_v = self._installed_version
        ver = release.version

        if not asset:
            self.btn_install.configure(
                text="Sin asset para esta plataforma", state="disabled"
            )
        elif installed_v and ver == installed_v:
            self.btn_install.configure(
                text="✓  Ya instalada — Reinstalar", state="normal"
            )
        elif installed_v and not is_newer(ver, installed_v):
            self.btn_install.configure(
                text=f"⬇  Bajar a v{ver}", state="normal"
            )
        elif installed_v:
            self.btn_install.configure(
                text=f"⬆  Actualizar a v{ver}", state="normal"
            )
        else:
            self.btn_install.configure(
                text=f"⬇  Instalar v{ver}", state="normal"
            )

        self._set_status("")

    # ─────────────────────────────────────────────────── INSTALL ─────────────

    def _on_install_click(self):
        if not self._selected_release or self._installing:
            return

        asset = self._selected_release.find_asset(config.PLATFORM)
        if not asset:
            return

        self._installing = True
        self.btn_install.configure(state="disabled", text="Instalando…")
        self.progress_bar.grid()
        self.progress_bar.set(0)

        threading.Thread(
            target=self._run_install,
            args=(self._selected_release, asset),
            daemon=True,
        ).start()

    def _run_install(self, release: Release, asset):
        def on_progress(fraction: float, downloaded: int, total: int):
            mb_down = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.after(0, self.progress_bar.set, fraction)
            self.after(
                0,
                self.lbl_status.configure,
                {"text": f"Descargando… {mb_down:.1f} / {mb_total:.1f} MB"},
            )

        def on_status(msg: str):
            self.after(0, self._set_status, msg)

        try:
            install(
                asset=asset,
                sha256sums_url=release.sha256_url,
                progress_callback=on_progress,
                status_callback=on_status,
            )
            self.after(0, self._on_install_success, release.version)
        except Exception as e:
            self.after(0, self._on_install_error, str(e))

    def _on_install_success(self, version: str):
        self._installing = False
        self._installed_version = version
        self.progress_bar.set(1)
        self._set_status(f"✅  scrcpy v{version} instalado correctamente.")
        self.btn_install.configure(state="disabled", text="✓  Instalado")
        self._update_installed_label(version)
        # Refrescar la lista para actualizar badges
        self._populate_releases(self._releases)

    def _on_install_error(self, error: str):
        self._installing = False
        self.progress_bar.grid_remove()
        self.progress_bar.set(0)
        self._set_status(f"❌  Error: {error}")
        self.btn_install.configure(state="normal", text="Reintentar")

    # ──────────────────────────────────────────────────── HELPERS ────────────

    def _set_status(self, msg: str):
        self.lbl_status.configure(text=msg)

    def _show_error(self, msg: str):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self.scroll_frame,
            text=f"❌  {msg}",
            font=FONT_LABEL,
            text_color=("#C62828", "#EF5350"),
            wraplength=500,
        ).grid(row=0, column=0, padx=20, pady=40)
