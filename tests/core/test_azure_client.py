import pytest
from unittest.mock import patch, MagicMock
from src.core.azure_client import AzureClient


@pytest.fixture
def client():
    """Retorna una instancia del cliente de Azure."""
    return AzureClient()


@pytest.fixture
def global_config():
    """Configuración global de prueba."""
    return {
        "organization": "my_org",
        "project": "my_project",
        "pat": "my_secret_token"
    }

# --- TESTS ---


def test_get_auth_header(client):
    """Verifica la codificación correcta del PAT en Base64."""
    token = "test_token"
    header = client.get_auth_header(token)

    # El valor esperado para ':test_token' es 'OnRlc3RfdG9rZW4='
    assert header["Authorization"] == "Basic OnRlc3RfdG9rZW4="
    assert "Authorization" in header


@patch("requests.post")
def test_post_to_pr_payload(mock_post, client, global_config):
    """Verifica que el POST al Pull Request envíe la URL y el JSON correctos."""
    # Configuración del mock
    mock_post.return_value.status_code = 201

    doc_config = {
        "repository_id": "repo_123",
        "pull_request_id": "99"
    }
    content = "Comentario de prueba"

    client.post_to_pr(global_config, doc_config, content)

    # Extraer argumentos de la llamada capturada
    args, kwargs = mock_post.call_args
    url = args[0]
    json_body = kwargs["json"]

    # Verificaciones
    assert "dev.azure.com/my_org/my_project" in url
    assert "repositories/repo_123/pullRequests/99" in url
    assert json_body["comments"][0]["content"] == content
    assert json_body["status"] == "active"


@patch("requests.patch")
def test_post_to_wi_markdown_conversion(mock_patch, client, global_config):
    """Verifica la conversión de Markdown a HTML al enviar a Work Items."""
    mock_patch.return_value.status_code = 200

    doc_config = {"work_item_id": "1000"}
    content = "Texto con **negrita**" # Markdown

    client.post_to_wi(global_config, doc_config, content)

    # Extraer el body enviado en el PATCH
    kwargs = mock_patch.call_args[1]
    patch_body = kwargs["json"]

    # Verificaciones
    assert patch_body[0]["op"] == "add"
    assert patch_body[0]["path"] == "/fields/System.History"
    # Comprobar que el Markdown se convirtió a HTML
    assert "<strong>negrita</strong>" in patch_body[0]["value"]
    assert "https://dev.azure.com/my_org/my_project/_apis/wit/workitems/1000" in mock_patch.call_args[0][0]


def test_post_to_pr_auth_headers(client, global_config):
    """Verifica que se inyecten los headers de autenticación en la petición."""
    with patch("requests.post") as mock_post:
        doc_config = {"repository_id": "r", "pull_request_id": "1"}
        client.post_to_pr(global_config, doc_config, "...")

        headers = mock_post.call_args[1]["headers"]
        assert "Authorization" in headers
        assert "Basic" in headers["Authorization"]
        assert headers["Content-Type"] == "application/json"
