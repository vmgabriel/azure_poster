import pytest
from unittest.mock import MagicMock, patch
from src.ui.app import AzureDevOpsApp
from src.core.constants import AppConfig
from pathlib import Path


@pytest.fixture
def mock_config(tmp_path):
    """Configuración inyectada para los tests."""
    return AppConfig(
        app_id="com.test.app",
        config_dir=tmp_path,
        global_config_file=tmp_path / "global.json",
        md_file="content.md",
        doc_config_file="config.json",
        ignore_folders=set()
    )


@pytest.fixture
def app(mock_config):
    """Instancia la aplicación mockeando la inicialización de GTK."""
    # Patching para evitar que GTK intente conectar con el servidor X/Wayland
    with patch("gi.repository.Adw.Application.__init__", return_value=None), \
            patch("gi.repository.Gio.Application.register", return_value=True):
        app = AzureDevOpsApp(mock_config)
        # Mockeamos los componentes de UI que se crean en do_activate
        app.window = MagicMock()
        app.stack = MagicMock()
        app.toast_overlay = MagicMock()
        return app


def test_app_initialization(app, mock_config):
    """Verifica que la app reciba la config e instancie sus servicios."""
    assert app.configurations == mock_config
    assert app.azure is not None
    assert app.storage is not None
    assert app.config == {}


def test_do_activate_loads_config(app, mock_config): # Quitamos el decorador @patch de arriba
    """Verifica que al activar se cargue el JSON global."""

    # Parcheamos la instancia que vive dentro de app
    with patch.object(app.storage, 'load_json') as mock_load:
        mock_load.return_value = {"pat": "12345", "organization": "vmgabriel"}

        with patch("gi.repository.GLib.set_prgname"), \
                patch("gi.repository.Adw.ApplicationWindow"), \
                patch("gi.repository.Gtk.IconTheme.get_for_display"), \
                patch.object(app, 'init_ui_components'), \
                patch.object(app, 'refresh_folder_list'):

            app.do_activate()

            # Ahora sí detectará la llamada
            mock_load.assert_called_once_with(mock_config.global_config_file)
            assert app.config["pat"] == "12345"


def test_ui_save_global_config_updates_state(app, mock_config):
    """Verifica que al guardar la config global se actualice el diccionario interno."""
    # Mockeamos los EntryRows de la UI
    app.org_entry = MagicMock()
    app.org_entry.get_text.return_value = "org_test"
    app.proj_entry = MagicMock()
    app.proj_entry.get_text.return_value = "proj_test"
    app.pat_entry = MagicMock()
    app.pat_entry.get_text.return_value = "pat_test"
    app.path_entry = MagicMock()
    app.path_entry.get_text.return_value = "/tmp/docs"
    app.theme_row = MagicMock()
    app.theme_row.get_selected.return_value = 0

    with patch.object(app.storage, "save_json") as mock_save, \
            patch.object(app, "refresh_folder_list"), \
            patch("os.path.exists", return_value=True):

        app.ui_save_global_config(None)

        # Verificar que el diccionario interno se actualizó
        assert app.config["organization"] == "org_test"
        assert app.config["base_path"] == "/tmp/docs"
        # Verificar que se llamó al almacenamiento
        mock_save.assert_called_once()


def test_ui_run_azure_calls_both_services(app):
    """Verifica que el botón 'Ejecutar' dispare ambas peticiones a Azure."""
    app.current_folder = "FolderA"
    app.config = {"pat": "token"}

    app.spinner = MagicMock()
    app.header = MagicMock()

    # Parcheamos las instancias internas
    with patch.object(app.azure, 'post_to_pr') as mock_pr, \
            patch.object(app.azure, 'post_to_wi') as mock_wi:

        mock_response = MagicMock()
        mock_response.ok = True
        mock_pr.return_value = mock_response
        mock_wi.return_value = mock_response

        app.text_view = MagicMock()
        buffer = app.text_view.get_buffer()
        buffer.get_text.return_value = "Markdown content"

        # También parcheamos el storage del app para el load_json de la config del folder
        with patch.object(app, "ui_save_markdown"), \
                patch.object(app.storage, "load_json", return_value={}):

            app.ui_run_azure(None)

            assert mock_pr.called
            assert mock_wi.called
