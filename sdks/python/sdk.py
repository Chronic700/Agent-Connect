import requests
import hashlib
import hmac
from typing import Optional, Dict, Any

class AgentConnectClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key

    def _get_headers(self) -> Dict[str, str]:
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    def register(self, name: str, description: str, webhook_url: str) -> Dict[str, Any]:
        """Registers a new agent."""
        url = f"{self.base_url}/api/agents/register"
        data = {"name": name, "description": description, "webhook_url": webhook_url}
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """Retrieves public information about an agent."""
        url = f"{self.base_url}/api/agents/{agent_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def list_agents(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Lists all agents, with optional filtering by status."""
        url = f"{self.base_url}/api/agents"
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def update_status(self, agent_id: str, status: str) -> Dict[str, Any]:
        """Updates an agent's status."""
        url = f"{self.base_url}/api/agents/{agent_id}/status"
        headers = self._get_headers()
        data = {"status": status}
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def send_message(self, to_agent_id: str, message_content: Dict[str, Any]) -> Dict[str, Any]:
        """Sends a message from the current agent to another agent."""
        url = f"{self.base_url}/api/messages/send"
        headers = self._get_headers()
        data = {"to_agent_id": to_agent_id, "message_content": message_content}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Retrievels the status of a sent message."""
        url = f"{self.base_url}/api/messages/{message_id}"
        headers = self._get_headers()
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def verify_webhook_signature(self, payload: str, signature: str, secret_token: str) -> bool:
        """Verifies the HMAC-SHA256 signature of a webhook payload."""
        if signature.startswith("sha256="):
            signature = signature[len("sha256="):]

        expected_signature = hmac.new(
            secret_token.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)
