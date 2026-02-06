from typing import List, Dict, Any

import os
import re
import json
import pathlib
import logging

from src.core import constants


logger = logging.getLogger(__name__)


class ConfigManager:
    """Handles file system operations and JSON configurations."""

    def __init__(self, configs: constants.AppConfig):
        self.configs = configs

    @staticmethod
    def load_json(path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    @staticmethod
    def save_json(path: str, data: Dict[str, Any]) -> None:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def create_doc_folder(self, base_path: str, name: str, data: Dict[str, str]) -> str:
        """Crea la carpeta de documentación en la ruta específica."""
        folder_name = re.sub(r'\s+', '_', name.strip())
        full_path = os.path.join(base_path, folder_name)

        if os.path.exists(full_path):
            logger.error("Current Path File has already exists {folder_name}")
            raise FileExistsError(f"La carpeta '{folder_name}' ya existe en esa ruta.")

        os.makedirs(full_path)
        self.save_json(os.path.join(full_path, self.configs.doc_config_file), data)
        pathlib.Path(os.path.join(full_path, self.configs.md_file)).touch()
        return full_path

    def get_valid_folders(self, base_path: str) -> List[str]:
        """Lista carpetas solo dentro de la ruta configurada."""
        if not base_path or not os.path.exists(base_path):
            return []
        return sorted(
            [
                d for d in os.listdir(base_path)
                if os.path.isdir(os.path.join(base_path, d))
                   and d not in self.configs.ignore_folders
                   and not d.startswith('.')
            ]
        )
