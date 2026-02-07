import pytest
import os
import json
from src.core.config_manager import ConfigManager
from src.core.constants import AppConfig


@pytest.fixture
def mock_config(tmp_path):
    """Crea una configuración de prueba con nombres de archivo personalizados."""
    return AppConfig(
        app_id="test_app",
        config_dir=tmp_path,
        global_config_file=tmp_path / "global.json",
        md_file="test_content.md",
        doc_config_file="test_config.json",
        ignore_folders={'venv', 'secret_folder'}
    )


@pytest.fixture
def manager(mock_config):
    """Instancia el manager con la configuración inyectada."""
    return ConfigManager(configs=mock_config)

# --- TESTS DE JSON ---


def test_load_json_returns_empty_dict_if_not_exists(manager, tmp_path):
    """Verifica que devuelva un dict vacío si el archivo no existe."""
    result = manager.load_json(str(tmp_path / "non_existent.json"))
    assert result == {}


def test_save_and_load_json(manager, tmp_path):
    """Prueba el ciclo completo de guardado y lectura de JSON."""
    file_path = str(tmp_path / "data.json")
    data = {"project": "Azure", "version": 1}

    manager.save_json(file_path, data)
    loaded_data = manager.load_json(file_path)

    assert loaded_data == data
    assert loaded_data["project"] == "Azure"

# --- TESTS DE CREACIÓN DE CARPETAS ---


def test_create_doc_folder_success(manager, mock_config, tmp_path):
    """Verifica la creación física de la carpeta y los archivos internos."""
    base_path = str(tmp_path)
    folder_name = " Documentacion  Azure " # Con espacios para probar el regex
    data = {"repo_id": "123"}

    # Ejecución
    full_path = manager.create_doc_folder(base_path, folder_name, data)

    # El nombre debe estar normalizado: espacios -> guiones bajos
    expected_name = "Documentacion_Azure"
    assert full_path.endswith(expected_name)
    assert os.path.exists(full_path)

    # Verificar archivos internos usando los nombres de la config inyectada
    assert os.path.exists(os.path.join(full_path, mock_config.md_file))
    config_file = os.path.join(full_path, mock_config.doc_config_file)
    assert os.path.exists(config_file)

    # Verificar contenido del JSON creado
    with open(config_file, 'r') as f:
        assert json.load(f)["repo_id"] == "123"


def test_create_doc_folder_already_exists_raises_error(manager, tmp_path):
    """Debe lanzar FileExistsError si la carpeta ya existe."""
    base_path = str(tmp_path)
    os.makedirs(os.path.join(base_path, "Existing"))

    with pytest.raises(FileExistsError):
        manager.create_doc_folder(base_path, "Existing", {})

# --- TESTS DE LISTADO Y FILTRADO ---


def test_get_valid_folders_filtering(manager, mock_config, tmp_path):
    """Verifica que ignore carpetas ocultas y las definidas en ignore_folders."""
    base_path = str(tmp_path)

    # Crear escenarios
    os.makedirs(os.path.join(base_path, "valid_one"))
    os.makedirs(os.path.join(base_path, "valid_two"))
    os.makedirs(os.path.join(base_path, "venv"))           # En ignore_folders
    os.makedirs(os.path.join(base_path, "secret_folder")) # En ignore_folders
    os.makedirs(os.path.join(base_path, ".git"))          # Empieza con punto
    with open(os.path.join(base_path, "file.txt"), "w") as f: f.write("") # Es un archivo

    folders = manager.get_valid_folders(base_path)

    assert len(folders) == 2
    assert "valid_one" in folders
    assert "valid_two" in folders
    assert "venv" not in folders
    assert ".git" not in folders
    assert "file.txt" not in folders
