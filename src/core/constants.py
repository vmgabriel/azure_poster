from pathlib import Path
from dataclasses import dataclass

from gi.repository import GLib


@dataclass(frozen=True) # Frozen lo hace inmutable (solo lectura)
class AppConfig:
    app_id: str
    config_dir: Path
    global_config_file: Path
    md_file: str
    doc_config_file: str
    ignore_folders: set[str]


APP_ID = "com.vmgabriel.azure_poster"
CONFIG_DIR: Path = Path(GLib.get_user_config_dir()) / APP_ID
IGNORE_FOLDERS: set[str] = {
    'venv',
    '__pycache__',
    '.git',
    '.pytest_cache',
    "icon",
    "tests"
}


DEFAULT_CONFIG = AppConfig(
    app_id=APP_ID,
    config_dir=CONFIG_DIR,
    global_config_file=CONFIG_DIR / "config.json",
    md_file="content.md",
    doc_config_file="config.json",
    ignore_folders=IGNORE_FOLDERS,
)
