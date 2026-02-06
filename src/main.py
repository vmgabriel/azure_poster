import os
import sys
import logging
import pathlib

from src.core import constants
from src.ui import app as gnome_app


def setup_logging(config_path: pathlib.Path):
    log_file = config_path.parent / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ]
    )
    logging.info("--- Iniciando Azure Docs Creator ---")


def verify_configuration_path(configs: constants.AppConfig) -> None:
    if not os.path.exists(configs.config_dir):
        os.makedirs(configs.config_dir, exist_ok=True)


def run() -> None:
    configurations = constants.DEFAULT_CONFIG

    verify_configuration_path(configs=configurations)
    setup_logging(configurations.global_config_file)

    app = gnome_app.AzureDevOpsApp(configs=configurations)
    app.run(sys.argv)


if __name__ == "__main__":
    run()
