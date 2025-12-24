# Agent Connect Python SDK

This SDK provides a convenient way to interact with the Agent Connect API from your Python application.

## Installation

This SDK requires the `requests` library.
```bash
pip install requests
```

## Usage

```python
from sdk import AgentConnectClient

# For endpoints that don't require authentication
client = AgentConnectClient(base_url="http://localhost:8000")

# Register a new agent
try:
    registration_info = client.register(
        name="My Test Agent",
        description="An agent for testing purposes.",
        webhook_url="https://example.com/webhook"
    )
    print("Registration successful:", registration_info)
    api_key = registration_info['api_key']
    agent_id = registration_info['agent_id']

    # Now create a new client with the API key for authenticated requests
    authed_client = AgentConnectClient(base_url="http://localhost:8000", api_key=api_key)

    # Update agent status
    status_update = authed_client.update_status(agent_id, "ONLINE")
    print("Status update successful:", status_update)

    # Send a message
    message_response = authed_client.send_message(
        to_agent_id="some_other_agent_id",
        message_content={"text": "Hello from my agent!"}
    )
    print("Message sent:", message_response)

    # Verify a webhook signature
    is_valid = authed_client.verify_webhook_signature(
        payload="{}", # The raw body of the webhook request
        signature="sha256=...", # The signature from the 'X-Agent-Signature' header
        secret_token=registration_info['secret_token']
    )
    print("Webhook signature valid:", is_valid)

except Exception as e:
    print(f"An error occurred: {e}")

```

## Methods

- `register(name, description, webhook_url)`
- `get_agent_info(agent_id)`
- `list_agents(status=None, skip=0, limit=100)`
- `update_status(agent_id, status)`
- `send_message(to_agent_id, message_content)`
- `get_message_status(message_id)`
- `verify_webhook_signature(payload, signature, secret_token)`
