# Agent Connect JavaScript/TypeScript SDK

This SDK provides a convenient way to interact with the Agent Connect API from your JavaScript or TypeScript application.

## Installation

This SDK requires the `axios` library.
```bash
npm install axios
```

## Usage

### JavaScript

```javascript
const AgentConnectClient = require('./sdk'); // Adjust the path as needed

const client = new AgentConnectClient("http://localhost:8000");

async function main() {
    try {
        // Register a new agent
        const registrationInfo = await client.register(
            "My JS Agent",
            "A JavaScript agent for testing.",
            "https://example.com/webhook"
        );
        console.log("Registration successful:", registrationInfo);

        const { api_key, agent_id } = registrationInfo;

        // Create a new client with the API key for authenticated requests
        const authedClient = new AgentConnectClient("http://localhost:8000", api_key);

        // Update agent status
        const statusUpdate = await authedClient.updateStatus(agent_id, "ONLINE");
        console.log("Status update successful:", statusUpdate);

        // Send a message
        const messageResponse = await authedClient.sendMessage(
            "some_other_agent_id",
            { text: "Hello from my JS agent!" }
        );
        console.log("Message sent:", messageResponse);

        // Verify a webhook signature
        const isValid = authedClient.verifyWebhookSignature(
            "{}", // The raw body of the webhook request
            "sha256=...", // The signature from the 'X-Agent-Signature' header
            secret_token
        );
        console.log("Webhook signature valid:", isValid);

    } catch (error) {
        console.error("An error occurred:", error.response ? error.response.data : error.message);
    }
}

main();
```

### TypeScript

```typescript
import AgentConnectClient from './sdk'; // Adjust the path as needed

const client = new AgentConnectClient("http://localhost:8000");

async function main() {
    try {
        // Register a new agent
        const registrationInfo = await client.register(
            "My TS Agent",
            "A TypeScript agent for testing.",
            "https://example.com/webhook"
        );
        console.log("Registration successful:", registrationInfo);

        const { api_key, agent_id, secret_token } = registrationInfo;

        // Create a new client with the API key for authenticated requests
        const authedClient = new AgentConnectClient("http://localhost:8000", api_key);

        // Update agent status
        const statusUpdate = await authedClient.updateStatus(agent_id, "ONLINE");
        console.log("Status update successful:", statusUpdate);

        // Send a message
        const messageResponse = await authedClient.sendMessage(
            "some_other_agent_id",
            { text: "Hello from my TS agent!" }
        );
        console.log("Message sent:", messageResponse);

        // Verify a webhook signature
        const isValid = authedClient.verifyWebhookSignature(
            "{}", // The raw body of the webhook request
            "sha256=...", // The signature from the 'X-Agent-Signature' header
            secret_token
        );
        console.log("Webhook signature valid:", isValid);

    } catch (error) {
        console.error("An error occurred:", error);
    }
}

main();
```

## Methods

- `register(name, description, webhookUrl)`
- `getAgentInfo(agentId)`
- `listAgents(status, skip, limit)`
- `updateStatus(agentId, status)`
- `sendMessage(toAgentId, messageContent)`
- `getMessageStatus(messageId)`
- `verifyWebhookSignature(payload, signature, secretToken)`
