import requests
import base64

def validate_connection(organization, project, pat):
    try:
        auth_bytes = f":{pat}".encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')

        headers = {
            'Authorization': f'Basic {base64_auth}',
            'Content-Type': 'application/json'
        }

        url = f"https://dev.azure.com/{organization}/_apis/projects/{project}?api-version=7.0"

        print(f"Intentando validar contra: {url}")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            print("✅ Conexión exitosa.")
            return True, "Conexión exitosa"
        elif response.status_code == 401:
            print("❌ Error 401: Token no autorizado o formato incorrecto.")
            return False, "Token no autorizado (401)"
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False, f"Error del servidor: {response.status_code}"

    except Exception as e:
        print("Fallo crítico en la validación")
        return False, str(e)

variables = {
    "organization": "",
    "project": "",
    "pat": "",
    "base_path": "",
    "theme": ""
}

validate_connection(variables.get("organization"), variables.get("project"), variables.get("pat"))
