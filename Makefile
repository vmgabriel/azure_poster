# Variables
APP_ID = com.vmgabriel.azure_poster
MANIFEST = $(APP_ID).yaml
BUILD_DIR = build-dir
PIP_GEN = flatpak-pip-generator.py
PIP_GEN_URL = https://raw.githubusercontent.com/flatpak/flatpak-builder-tools/master/pip/flatpak-pip-generator.py

# Ruta del log dentro del sandbox de Flatpak
LOG_PATH = $(HOME)/.var/app/$(APP_ID)/config/$(APP_ID)/app.log

# Versiones de GNOME
GNOME_VER = 45

# Dependencias
BUILD_DEPS = packaging==24.2 hatchling==1.28.0 pathspec==0.12.1 pluggy==1.5.0 trove-classifiers==2024.10.16
APP_DEPS = requests markdown

.PHONY: all clean build install run refresh check-tools check-gnome-sdk logs

all: build

check-tools:
	@command -v flatpak-builder >/dev/null 2>&1 || { echo "❌ Error: flatpak-builder no instalado."; exit 1; }
	@command -v wget >/dev/null 2>&1 || { echo "❌ Error: wget no instalado."; exit 1; }

check-gnome-sdk:
	@echo "🔍 Verificando SDK de GNOME $(GNOME_VER)..."
	@flatpak info org.gnome.Sdk//$(GNOME_VER) >/dev/null 2>&1 || \
		(echo "📥 Instalando SDK..." && flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo && flatpak install -y flathub org.gnome.Sdk//$(GNOME_VER))
	@flatpak info org.gnome.Platform//$(GNOME_VER) >/dev/null 2>&1 || \
		(echo "📥 Instalando Plataforma..." && flatpak install -y flathub org.gnome.Platform//$(GNOME_VER))

$(PIP_GEN):
	@echo "📥 Descargando $(PIP_GEN)..."
	@wget $(PIP_GEN_URL) -O $(PIP_GEN)
	@chmod +x $(PIP_GEN)

download-build-tools:
	@echo "📥 Descargando herramientas (.whl)..."
	@pip download --only-binary=:all: --no-deps $(BUILD_DEPS)

python3-modules.json: $(PIP_GEN)
	@echo "🧬 Generando dependencias..."
	@python3 $(PIP_GEN) $(APP_DEPS)

build: check-tools check-gnome-sdk download-build-tools python3-modules.json
	@echo "🛠️ Construyendo Flatpak..."
	flatpak-builder --force-clean $(BUILD_DIR) $(MANIFEST)

install: build
	@echo "🚀 Instalando..."
	flatpak-builder --user --install --force-clean $(BUILD_DIR) $(MANIFEST)

run:
	@echo "🏃 Ejecutando $(APP_ID)..."
	@flatpak run $(APP_ID)

# --- COMANDO DE LOGS ---
logs:
	@echo "📜 Abriendo logs de la aplicación..."
	@if [ -f $(LOG_PATH) ]; then \
		tail -f $(LOG_PATH); \
	else \
		echo "⚠️ El archivo de log aún no existe. ¿Ya ejecutaste la app?"; \
	fi

clean:
	@echo "🧹 Limpiando..."
	rm -rf $(BUILD_DIR) .flatpak-builder
	rm -f *.whl python3-modules.json $(PIP_GEN)
	@echo "Limpieza completada."

refresh: clean install run
