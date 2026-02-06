# Azure Docs Creator 🚀

Azure Docs Creator es una aplicación de escritorio nativa para Linux diseñada para automatizar la generación de documentación y la publicación de comentarios en **Azure DevOps** (Pull Requests y Work Items). Construida con **Python 3**, **GTK 4** y **Libadwaita**, ofrece una experiencia moderna, rápida y profesional.



## ✨ Características Principales

* **Interfaz Moderna:** Basada en GNOME 45 con soporte para temas Claro/Oscuro y del sistema.
* **Gestión de Hilos:** Creación y actualización de carpetas de documentación local.
* **Integración con Azure DevOps:** Publicación asíncrona de contenido Markdown directamente en PRs y Tareas (Work Items).
* **Seguridad:** Manejo de Personal Access Tokens (PAT) y validación de conexión en tiempo real.
* **Robustez:** Feedback visual mediante Spinners y Logs detallados para soporte técnico.
* **Empaquetado Profesional:** Distribución mediante **Flatpak** para máxima compatibilidad entre distribuciones.

---

## 🛠️ Requisitos del Sistema

Antes de comenzar, asegúrate de tener instalado:

* **Linux** con soporte para Flatpak.
* `flatpak-builder` instalado en el sistema operativo.
* `make` para utilizar los comandos de automatización.

---

## 🚀 Instalación y Desarrollo con Makefile

Hemos automatizado todo el proceso de empaquetado. Ya no necesitas preocuparte por las dependencias manuales de Python o los SDKs de GNOME.



### Comandos Rápidos:

# Dependencies
- Flathub
- requirements-parser


| Comando | Descripción |
| :--- | :--- |
| `make build` | Prepara las herramientas de construcción y compila el Flatpak. |
| `make install` | Compila e instala la aplicación en tu sistema (usuario). |
| `make run` | Ejecuta la aplicación instalada. |
| `make logs` | Visualiza los logs de la aplicación en tiempo real (útil para debug). |
| `make refresh` | Limpia, reinstala y ejecuta la aplicación (ideal para desarrollo). |
| `make clean` | Elimina archivos temporales, binarios `.whl` y cachés de construcción. |

---

## ⚙️ Configuración Inicial

Al abrir la aplicación por primera vez, deberás configurar los ajustes globales:

1.  **Organización:** Tu nombre de organización en Azure (`dev.azure.com/nombre-org`).
2.  **Proyecto:** El nombre del proyecto dentro de Azure DevOps.
3.  **PAT (Personal Access Token):** Token con permisos de lectura/escritura en *Code* y *Work Items*.
4.  **Ruta de Documentación:** Carpeta local donde se guardarán tus archivos `.md`.
5.  **Tema:** Selecciona entre Claro, Oscuro o seguimiento automático del Sistema.

> 💡 **Tip:** Usa el botón **"Probar Conexión"** para validar que tu PAT y Organización sean correctos antes de guardar.

---

## 📦 Estructura del Proyecto

* `src/`: Código fuente de la aplicación (Lógica Core y UI).
* `icon/`: Iconografía oficial de la aplicación.
* `com.vmgabriel.azure_poster.yaml`: Manifiesto de Flatpak que define el sandbox y permisos.
* `pyproject.toml`: Configuración de empaquetado de Python (Hatchling).
* `Makefile`: Automatización de tareas de compilación y despliegue.

---

## 📜 Logs y Soporte

Si experimentas problemas, puedes consultar los logs detallados que genera la aplicación. Estos incluyen información sobre la respuesta de las APIs de Azure y errores de escritura en disco.

Para ver los logs mientras usas la app, ejecuta:
```bash
make logs

```

Los archivos físicos se encuentran en:
`~/.var/app/com.vmgabriel.azure_poster/config/com.vmgabriel.azure_poster/app.log`

---

Desarrollado con ❤️ por **Gabriel Vargas** (2026).
