from typing import Any, Optional, Dict, List, Callable

import gi
import os
import logging

from src.core import azure_client, config_manager, constants

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, Gdk, GLib


logger = logging.getLogger(__name__)


class AzureDevOpsApp(Adw.Application):
    def __init__(self, configs: constants.AppConfig) -> None:
        super().__init__(application_id=configs.app_id, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.configurations = configs
        self.azure: azure_client.AzureClient = azure_client.AzureClient()
        self.storage: config_manager.ConfigManager = config_manager.ConfigManager(configs=self.configurations)
        self.config: Dict[str, Any] = {}
        self.current_folder: Optional[str] = None

        # UI Widgets typing
        self.app_logo_texture: Optional[Gdk.Texture] = None
        self.window: Any = None
        self.stack: Any = None
        self.text_view: Any = None
        self.folders_list: Any = None

        # Entry rows for settings
        self.org_entry: Any = None
        self.proj_entry: Any = None
        self.pat_entry: Any = None
        self.theme_row: Any = None # Nuevo widget para el tema

        # Entry rows for documentation
        self.name_entry: Any = None
        self.repo_entry: Any = None
        self.pr_entry: Any = None
        self.wi_entry: Any = None

    def do_activate(self) -> None:
        logger.info("Activando aplicación...")
        self.config = self.storage.load_json(self.configurations.global_config_file)

        self.apply_stored_theme()

        GLib.set_prgname(self.configurations.app_id)

        self.window = Adw.ApplicationWindow(application=self)
        self.window.set_title("Azure Docs Creator")
        self.window.set_default_size(500, 600)

        icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon")

        if os.path.exists(icon_path):
            icon_theme.add_search_path(icon_path)
            self.window.set_icon_name(self.application_id)

        self.stack = Adw.ViewStack()
        self.init_ui_components()

        self.stack.connect("notify::visible-child-name", self.on_stack_changed)

        if not self.config.get("pat"):
            self.stack.set_visible_child_name("config_view")
        else:
            self.refresh_folder_list()

        self.window.present()

    def apply_stored_theme(self) -> None:
        """Aplica el esquema de color basado en la configuración guardada."""
        theme_pref = self.config.get("theme", "Sistema")
        style_manager = Adw.StyleManager.get_default()

        mapping = {
            "Sistema": Adw.ColorScheme.DEFAULT,
            "Claro": Adw.ColorScheme.PREFER_LIGHT,
            "Oscuro": Adw.ColorScheme.PREFER_DARK
        }
        style_manager.set_color_scheme(mapping.get(theme_pref, Adw.ColorScheme.DEFAULT))

    def init_ui_components(self) -> None:
        self.view: Any = Adw.ToolbarView()
        self.header: Any = Adw.HeaderBar()
        self.view.add_top_bar(self.header)

        self.back_btn: Any = Gtk.Button(icon_name="go-previous-symbolic", visible=False)
        self.back_btn.connect("clicked", lambda x: self.refresh_folder_list())

        self.add_btn: Any = Gtk.Button(icon_name="list-add-symbolic")
        self.add_btn.connect("clicked", self.ui_open_creation_mode)

        self.spinner = Gtk.Spinner()
        self.header.pack_end(self.spinner)

        menu: Any = Gio.Menu()
        menu.append("Ayuda", "app.help")
        menu.append("Acerca de", "app.about")

        self.menu_btn: Any = Gtk.MenuButton(icon_name="view-more-symbolic", menu_model=menu)

        self.settings_btn: Any = Gtk.Button(icon_name="emblem-system-symbolic")
        self.settings_btn.connect("clicked", lambda x: self.stack.set_visible_child_name("config_view"))

        help_action: Any = Gio.SimpleAction.new("help", None)
        help_action.connect("activate", self.ui_show_help)
        self.add_action(help_action)

        about_action: Any = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.ui_show_about)
        self.add_action(about_action)

        self.header.pack_start(self.back_btn)
        self.header.pack_start(self.add_btn)
        self.header.pack_end(self.menu_btn)
        self.header.pack_end(self.settings_btn)

        self.setup_config_view()
        self.setup_main_view()
        self.setup_list_view()
        self.setup_editor_view()

        self.toast_overlay: Any = Adw.ToastOverlay(child=self.stack)
        self.view.set_content(self.toast_overlay)
        self.window.set_content(self.view)

    def create_margin_box(self) -> Any:
        box: Any = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(20); box.set_margin_bottom(20)
        box.set_margin_start(20); box.set_margin_end(20)
        return box

    def setup_config_view(self) -> None:
        box: Any = self.create_margin_box()
        group: Any = Adw.PreferencesGroup(title="Ajustes Globales")

        self.org_entry = Adw.EntryRow(title="Organización", text=self.config.get("organization", ""))
        self.proj_entry = Adw.EntryRow(title="Proyecto", text=self.config.get("project", ""))
        self.pat_entry = Adw.PasswordEntryRow(title="PAT", text=self.config.get("pat", ""))

        self.path_entry = Adw.EntryRow(
            title="Ruta de Documentación",
            text=self.config.get("base_path", os.getcwd())
        )

        # --- SECCIÓN DE TEMA ---
        themes = ["Sistema", "Claro", "Oscuro"]
        self.theme_row = Adw.ComboRow(
            title="Tema de la Aplicación",
            model=Gtk.StringList.new(themes)
        )

        # Seleccionar el tema actual en el combo
        current_theme = self.config.get("theme", "Sistema")
        if current_theme in themes:
            self.theme_row.set_selected(themes.index(current_theme))

        # Crear el botón de "Examinar"
        browse_btn = Gtk.Button(icon_name="folder-open-symbolic")
        browse_btn.set_valign(Gtk.Align.CENTER)
        browse_btn.set_tooltip_text("Seleccionar carpeta")
        browse_btn.add_css_class("flat")
        browse_btn.connect("clicked", self.ui_on_browse_clicked)
        self.path_entry.add_suffix(browse_btn)

        self.check_btn = Gtk.Button(label="Probar Conexión")
        self.check_btn.add_css_class("flat")
        self.check_btn.connect("clicked", self.ui_on_verify_pat)
        self.pat_entry.add_suffix(self.check_btn)

        items = [self.org_entry, self.proj_entry, self.pat_entry, self.path_entry, self.theme_row]

        for e in items: group.add(e)
        box.append(group)

        btn: Any = Gtk.Button(label="Guardar Configuración", css_classes=["suggested-action"])
        btn.connect("clicked", self.ui_save_global_config)
        box.append(btn)
        self.stack.add_named(box, "config_view")

    def set_busy(self, busy: bool) -> None:
        """Controla el estado visual de carga de la aplicación."""
        if busy:
            self.spinner.start()
            self.header.set_sensitive(False) # Bloquea navegación
            self.stack.set_sensitive(False)  # Bloquea edición
        else:
            self.spinner.stop()
            self.header.set_sensitive(True)
            self.stack.set_sensitive(True)

    def setup_main_view(self) -> None:
        box: Any = self.create_margin_box()
        self.doc_group: Any = Adw.PreferencesGroup(title="Documentación")

        self.name_entry = Adw.EntryRow(title="Nombre de Carpeta")
        self.repo_entry = Adw.EntryRow(title="Repository ID")
        self.pr_entry = Adw.EntryRow(title="PR ID")
        self.wi_entry = Adw.EntryRow(title="Work Item ID")

        for e in [self.name_entry, self.repo_entry, self.pr_entry, self.wi_entry]: self.doc_group.add(e)
        box.append(self.doc_group)

        self.doc_action_btn: Any = Gtk.Button(label="Acción", css_classes=["accent"])
        box.append(self.doc_action_btn)
        self.stack.add_named(box, "main_view")

    def setup_list_view(self) -> None:
        scroll: Any = Gtk.ScrolledWindow()
        box: Any = self.create_margin_box()
        self.folders_group: Any = Adw.PreferencesGroup(title="Documentaciones Existentes")
        self.folders_list = Gtk.ListBox(css_classes=["boxed-list"], selection_mode=Gtk.SelectionMode.NONE)
        self.folders_group.add(self.folders_list)

        self.empty_label: Any = Gtk.Label(label="Aún no hay documentaciones", css_classes=["dim-label"])
        box.append(self.folders_group)
        box.append(self.empty_label)
        scroll.set_child(box)
        self.stack.add_named(scroll, "list_view")

    def setup_editor_view(self) -> None:
        box: Any = self.create_margin_box()
        bar: Any = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        btns: List[Any] = [
            ("media-playback-start-symbolic", "success", self.ui_run_azure, "Ejecutar"),
            ("settings-symbolic", "", self.ui_edit_folder_config, "Configurar"),
            ("document-save-symbolic", "suggested-action", self.ui_save_markdown, "Guardar")
        ]
        for icon, cls, call, tip in btns:
            b: Any = Gtk.Button(icon_name=icon, tooltip_text=tip)
            if cls: b.add_css_class(cls)
            b.connect("clicked", call)
            bar.append(b)

        box.append(bar)

        scrolled: Any = Gtk.ScrolledWindow(vexpand=True, has_frame=True)
        # IMPORTANTE: Añadimos 'view' a ScrolledWindow para asegurar fondo correcto en dark mode
        scrolled.add_css_class("view")

        self.text_view = Gtk.TextView(monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.text_view.add_css_class("view")
        self.text_view.set_pixels_above_lines(4)
        self.text_view.set_pixels_below_lines(4)
        self.text_view.set_margin_top(20)
        self.text_view.set_margin_bottom(20)
        self.text_view.set_margin_start(20)
        self.text_view.set_margin_end(20)
        scrolled.set_child(self.text_view)
        box.append(scrolled)

        self.stack.add_named(box, "editor_view")

    # ... [ on_stack_changed, show_toast, refresh_folder_list, ui_show_about, ui_show_help, ui_on_browse_clicked, ui_open_editor, ui_open_creation_mode, ui_edit_folder_config, ui_save_folder_config, ui_save_markdown, ui_run_azure, ui_create_documentation permanecen iguales ] ...

    def on_stack_changed(self, stack: Any, pspec: Any) -> None:
        current: str = stack.get_visible_child_name()
        is_list: bool = current == "list_view"
        self.back_btn.set_visible(not is_list)
        self.add_btn.set_visible(is_list)
        self.settings_btn.set_visible(is_list)

    def show_toast(self, message: str) -> None:
        self.toast_overlay.add_toast(Adw.Toast.new(message))

    def refresh_folder_list(self) -> None:
        # Limpiar la lista actual
        while child := self.folders_list.get_first_child():
            self.folders_list.remove(child)

        # Obtener la ruta base de la configuración global
        # Si no existe, usamos el directorio actual como respaldo seguro
        base_path = self.config.get("base_path", os.getcwd())

        # PASAMOS el base_path al servicio
        folders: List[str] = self.storage.get_valid_folders(base_path)

        self.empty_label.set_visible(not folders)
        self.folders_group.set_visible(bool(folders))

        for f in folders:
            row: Any = Adw.ActionRow(title=f)
            btn: Any = Gtk.Button(
                icon_name="go-next-symbolic",
                valign=Gtk.Align.CENTER,
                css_classes=["flat"]
            )
            # Asegúrate de que el editor abra la ruta completa después
            btn.connect("clicked", lambda x, folder=f: self.ui_open_editor(folder))
            row.add_suffix(btn)
            self.folders_list.append(row)

        self.stack.set_visible_child_name("list_view")

    def ui_on_verify_pat(self, btn):
        org = self.org_entry.get_text()
        proj = self.proj_entry.get_text()
        pat = self.pat_entry.get_text()

        self.check_btn.set_sensitive(False)
        self.spinner.start()

        def check():
            is_valid = self.azure.verify_connection(org, proj, pat)
            GLib.idle_add(self.on_verify_finished, is_valid)

        import threading
        threading.Thread(target=check, daemon=True).start()

    def on_verify_finished(self, is_valid):
        self.check_btn.set_sensitive(True)
        self.spinner.stop()
        if is_valid:
            self.show_toast("✅ Conexión exitosa")
        else:
            self.show_toast("❌ Error: Datos de Azure inválidos")

    def ui_show_about(self, action: Any, param: Any) -> None:
        """Muestra la ventana de Acerca de usando el ID de la aplicación."""
        # En lugar de pasar la textura, usamos el ID que registraremos en el sistema
        about = Adw.AboutWindow(
            transient_for=self.window,
            application_name="Azure Docs Creator",
            application_icon="com.vmgabriel.azure_poster",
            developer_name="Gabriel Vargas",
            version="0.0.1",
            copyright="© 2026 Gabriel Vargas",
            website="https://vmgabriel.com"
        )
        about.present()

    def ui_show_help(self, action: Any, param: Any) -> None:
        """Versión compacta manual: elimina el scroll excesivo controlando cada píxel."""
        help_window = Adw.Window(
            transient_for=self.window,
            default_width=520,
            default_height=580,
            modal=True,
            title="Centro de Ayuda"
        )

        view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        view.add_top_bar(header)

        scrolled = Gtk.ScrolledWindow()
        clamp = Adw.Clamp(maximum_size=460)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(24); box.set_margin_bottom(24)
        box.set_margin_start(24); box.set_margin_end(24)

        def add_section_header(title: str, icon_name: str) -> None:
            """Crea un encabezado de sección pequeño y elegante con icono."""
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            header_box.set_margin_top(10)

            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.set_pixel_size(32)  # Tamaño pequeño y controlado
            icon.add_css_class("accent") # Color azulado de sistema

            label = Gtk.Label(xalign=0)
            label.set_markup(f"<span size='x-large' weight='vmgabriel'>{title}</span>")

            header_box.append(icon)
            header_box.append(label)
            box.append(header_box)

        # --- SECCIÓN 1: AJUSTES GLOBALES ---
        add_section_header("Ajustes Globales", "preferences-system-network-symbolic")

        desc_global = Gtk.Label(use_markup=True, xalign=0, wrap=True)
        desc_global.set_markup(
            "Configuración base para conectar con tu instancia de Azure:\n\n\n"
            "• <b>Organización:</b> Nombre de la organizacion.\nSe puede encontrar en la ruta: \ndev.azure.com/<b>{{org}}</b>\n\n"
            "• <b>Proyecto:</b> Nombre exacto del proyecto\nTambien se puede encontrar en la ruta: \ndev.azure.com/<b>{{org}}</b>/<b>{{project}}</b>\n\n"
            "• <b>PAT:</b> Token con permisos de lectura/escritura.\n - Code -> Requiere lectura y escritura.\n - Work Items -> Requiere lectura y escritura.\n\n"
        )
        box.append(desc_global)

        # Fila de acción para el PAT (Compacta)
        group_pat = Adw.PreferencesGroup()
        pat_row = Adw.ActionRow(title="¿Cómo obtener el PAT?", subtitle="Click para abrir guía")
        pat_row.add_prefix(Gtk.Image(icon_name="dialog-password-symbolic"))
        pat_row.add_suffix(Gtk.Image(icon_name="external-link-symbolic"))
        pat_row.set_activatable(True)
        pat_row.connect("activated", lambda x: Gtk.show_uri(help_window, "https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate", 0))
        group_pat.add(pat_row)
        box.append(group_pat)

        # Separador sutil
        box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, margin_top=10, margin_bottom=10))

        # --- SECCIÓN 2: NUEVA DOCUMENTACIÓN ---
        add_section_header("Nueva Documentación", "folder-new-symbolic")

        desc_doc = Gtk.Label(use_markup=True, xalign=0, wrap=True)
        desc_doc.set_markup(
            "Identificadores necesarios para cada carpeta de hilo:\n\n\n"
            "• <b>Repository ID:</b> Nombre o ID del repositorio.\n Lo puedes conseguir tambien en la URL\n dev.azure.com/<b>{{org}}</b>/vmgabriel/_git/<b>{{repository_id}}</b>\n\n"
            "• <b>Pull Request ID:</b> Número del PR para los comentarios.\n\n"
            "• <b>Work Item ID:</b> ID de la tarea para el historial."
        )
        box.append(desc_doc)

        # Ensamblaje
        clamp.set_child(box)
        scrolled.set_child(clamp)
        view.set_content(scrolled)
        help_window.set_content(view)
        help_window.present()

    def ui_on_browse_clicked(self, btn: Gtk.Button) -> None:
        """Abre el nuevo Gtk.FileDialog para seleccionar carpetas sin errores de critical."""
        # 1. Creamos el objeto de diálogo
        dialog = Gtk.FileDialog(title="Seleccionar carpeta de documentación")

        # 2. Definimos qué pasa cuando el usuario elige la carpeta
        def on_open_finish(source_object, result):
            try:
                # Intentamos obtener el archivo seleccionado
                file = source_object.select_folder_finish(result)
                if file:
                    # Actualizamos el campo de texto con la ruta
                    self.path_entry.set_text(file.get_path())
            except GLib.Error as e:
                # Si el usuario cancela, entrará por aquí; podemos ignorarlo
                logger.error(f"Selección cancelada o error: {e.message}")

        # 3. Lanzamos el diálogo de selección de carpeta
        dialog.select_folder(self.window, None, on_open_finish)

    def ui_open_editor(self, folder: str) -> None:
        self.current_folder = folder
        base_path = self.config.get("base_path", os.getcwd())

        # Unimos la ruta base con la carpeta seleccionada
        full_path = os.path.join(base_path, folder)
        md_path: str = os.path.join(full_path, self.configurations.md_file)

        content: str = ""
        if os.path.exists(md_path):
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()

        self.text_view.get_buffer().set_text(content)
        self.stack.set_visible_child_name("editor_view")

    def ui_open_creation_mode(self, btn: Optional[Any] = None) -> None:
        self.current_folder = None
        for e in [self.name_entry, self.repo_entry, self.pr_entry, self.wi_entry]:
            e.set_text("")

        self.name_entry.set_sensitive(True)
        self.doc_group.set_title("Nueva Documentación")
        self.doc_action_btn.set_label("Crear Carpeta")

        self.reconnect_action_btn(self.ui_create_documentation)
        self.stack.set_visible_child_name("main_view")

    def ui_edit_folder_config(self, btn: Any) -> None:
        if not self.current_folder: return
        data: Dict[str, Any] = self.storage.load_json(os.path.join(self.current_folder, self.configurations.doc_config_file))
        self.name_entry.set_text(self.current_folder)
        self.name_entry.set_sensitive(False)
        self.repo_entry.set_text(data.get("repository_id", ""))
        self.pr_entry.set_text(data.get("pull_request_id", ""))
        self.wi_entry.set_text(data.get("work_item_id", ""))

        self.doc_group.set_title(f"Configurando: {self.current_folder}")
        self.doc_action_btn.set_label("Actualizar")
        self.reconnect_action_btn(self.ui_save_folder_config)
        self.stack.set_visible_child_name("main_view")

    def ui_save_folder_config(self, btn: Any) -> None:
        if not self.current_folder: return
        data: Dict[str, str] = {
            "repository_id": self.repo_entry.get_text(),
            "pull_request_id": self.pr_entry.get_text(),
            "work_item_id": self.wi_entry.get_text()
        }
        self.storage.save_json(os.path.join(self.current_folder, self.configurations.doc_config_file), data)
        self.show_toast("✅ Configuración de carpeta actualizada")
        self.stack.set_visible_child_name("editor_view")

    def ui_save_markdown(self, btn: Optional[Any]) -> None:
        if not self.current_folder: return

        # Obtener ruta completa
        base_path = self.config.get("base_path", os.getcwd())
        full_path = os.path.join(base_path, self.current_folder, self.configurations.md_file)

        buffer: Any = self.text_view.get_buffer()
        text: str = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.info(f"Contenido Markdown guardado en: {full_path}")
            self.show_toast("💾 Guardado")
        except Exception as exc:
            logger.error(f"No se pudo guardar el archivo MD: {exc}")
            self.show_toast("❌ Error al guardar archivo")


    def ui_run_azure(self, btn: Any) -> None:
        if not self.current_folder: return
        self.ui_save_markdown(None)

        doc_conf = self.storage.load_json(os.path.join(self.current_folder, self.configurations.doc_config_file))
        buffer = self.text_view.get_buffer()
        md_content = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)

        # 1. Feedback visual de inicio
        self.set_busy(True)

        # 2. Ejecutar en un hilo para no congelar la ventana
        import threading

        def thread_target():
            try:
                r1 = self.azure.post_to_pr(self.config, doc_conf, md_content)
                r2 = self.azure.post_to_wi(self.config, doc_conf, md_content)

                # Volvemos al hilo principal para tocar la UI
                GLib.idle_add(self.on_azure_response, r1, r2)
            except Exception as e:
                GLib.idle_add(self.on_azure_error, str(e))

        threading.Thread(target=thread_target, daemon=True).start()

    def on_azure_response(self, r1, r2):
        self.set_busy(False)
        if r1.ok and r2.ok:
            logger.info(f"Publicación exitosa en Azure para la carpeta: {self.current_folder}")
            self.show_toast("🚀 Publicado con éxito")
        else:
            # Capturamos el detalle del error para el log
            msg = f"Error en Azure. PR: {r1.status_code}, WI: {r2.status_code}. Respuestas: {r1.text[:100]} | {r2.text[:100]}"
            logger.warning(msg)
            self.show_toast("⚠️ Error de Azure")

    def on_azure_error(self, error_msg):
        self.set_busy(False)
        logger.error(f"Fallo en la comunicación con Azure: {error_msg}")
        self.show_toast(f"❌ Error de red: {error_msg}")

    def ui_create_documentation(self, btn: Any) -> None:
        try:
            name: str = self.name_entry.get_text().strip()
            if not name:
                self.show_toast("❌ El nombre es requerido")
                return

            # Obtenemos la ruta base actual
            base_path = self.config.get("base_path", os.getcwd())

            data: Dict[str, str] = {
                "repository_id": self.repo_entry.get_text(),
                "pull_request_id": self.pr_entry.get_text(),
                "work_item_id": self.wi_entry.get_text()
            }

            # PASAMOS los 3 argumentos
            self.storage.create_doc_folder(base_path, name, data)
            self.show_toast(f"✅ Carpeta '{name}' creada")
            self.refresh_folder_list()

        except FileExistsError as e:
            self.show_toast(str(e))
        except Exception as e:
            self.show_toast(f"❌ Error inesperado: {e}")

    def ui_save_global_config(self, btn: Any) -> None:
        new_path = self.path_entry.get_text()

        if not os.path.exists(new_path):
            try:
                os.makedirs(new_path)
            except Exception as e:
                self.show_toast(f"Error con la ruta: {e}")
                return

        # OBTENER EL TEMA SELECCIONADO
        # Mapeamos el índice del combo al nombre del string
        themes = ["Sistema", "Claro", "Oscuro"]
        selected_theme = themes[self.theme_row.get_selected()]

        self.config = {
            "organization": self.org_entry.get_text(),
            "project": self.proj_entry.get_text(),
            "pat": self.pat_entry.get_text(),
            "base_path": new_path,
            "theme": selected_theme # GUARDAR EN EL DICCIONARIO
        }

        self.storage.save_json(self.configurations.global_config_file, self.config)

        # APLICAR EL TEMA INMEDIATAMENTE SIN REINICIAR
        self.apply_stored_theme()

        self.show_toast("💾 Configuración guardada")
        self.refresh_folder_list()

    def reconnect_action_btn(self, callback: Callable[[Any], None]) -> None:
        try: self.doc_action_btn.disconnect_by_func(self.ui_create_documentation)
        except Exception: pass
        try: self.doc_action_btn.disconnect_by_func(self.ui_save_folder_config)
        except Exception: pass
        self.doc_action_btn.connect("clicked", callback)
