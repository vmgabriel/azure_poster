from typing import List, Dict, Any

import base64
import requests
import markdown
import logging


logger = logging.getLogger(__name__)


class AzureClient:
    """Handles all API communication with Azure DevOps."""

    @staticmethod
    def get_auth_header(token: str) -> Dict[str, str]:
        auth_bytes = base64.b64encode(bytes(f':{token}', 'ascii'))
        return {'Authorization': f'Basic {auth_bytes.decode("ascii")}'}

    def post_to_pr(self, global_config: Dict[str, str], doc_config: Dict[str, str], content: str) -> requests.Response:
        url: str = (f"https://dev.azure.com/{global_config['organization']}/{global_config['project']}/"
                    f"_apis/git/repositories/{doc_config['repository_id']}/pullRequests/"
                    f"{doc_config['pull_request_id']}/threads?api-version=7.1-preview.1")

        headers: Dict[str, str] = {
            **self.get_auth_header(global_config['pat']),
            'Content-Type': 'application/json'
        }
        body: Dict[str, Any] = {
            "comments": [{"content": content, "commentType": "text"}],
            "status": "active"
        }
        return requests.post(url, json=body, headers=headers)

    def post_to_wi(self, global_config: Dict[str, str], doc_config: Dict[str, str], content: str) -> requests.Response:
        url: str = (f"https://dev.azure.com/{global_config['organization']}/{global_config['project']}/"
                    f"_apis/wit/workitems/{doc_config['work_item_id']}?api-version=7.1-preview.3")

        headers: Dict[str, str] = {
            **self.get_auth_header(global_config['pat']),
            'Content-Type': 'application/json-patch+json'
        }
        html_content: str = markdown.markdown(content)
        body: List[Dict[str, Any]] = [
            {"op": "add", "path": "/fields/System.History", "value": html_content}
        ]
        return requests.patch(url, json=body, headers=headers)

    def verify_connection(self, organization: str, project: str, pat: str) -> bool:
        """Intenta conectar con la API de Azure para validar el PAT."""
        url = f"https://dev.azure.com/{organization}/_apis/projects/{project}?api-version=7.0"
        logger.info(f"Intentando validar contra: {url}")
        try:
            response = requests.get(url, headers=self.get_auth_header(pat), timeout=10)
            return response.ok
        except Exception as exc:
            logger.error(f"Fallo en la comunicación con Azure: {str(exc)}")
            return False
