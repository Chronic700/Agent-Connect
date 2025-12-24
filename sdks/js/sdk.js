// Assumes axios is installed and available.
// You can install it with: npm install axios

const axios = require('axios');
const crypto = require('crypto');

class AgentConnectClient {
    constructor(baseUrl = "http://127.0.0.1:8000", apiKey = null) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }

    _getHeaders() {
        if (this.apiKey) {
            return { "Authorization": `Bearer ${this.apiKey}` };
        }
        return {};
    }

    async register(name, description, webhookUrl) {
        const url = `${this.baseUrl}/api/agents/register`;
        const data = { name, description, webhook_url: webhookUrl };
        const response = await axios.post(url, data);
        return response.data;
    }

    async getAgentInfo(agentId) {
        const url = `${this.baseUrl}/api/agents/${agentId}`;
        const response = await axios.get(url);
        return response.data;
    }

    async listAgents(status = null, skip = 0, limit = 100) {
        const url = `${this.baseUrl}/api/agents`;
        const params = { skip, limit };
        if (status) {
            params.status = status;
        }
        const response = await axios.get(url, { params });
        return response.data;
    }

    async updateStatus(agentId, status) {
        const url = `${this.baseUrl}/api/agents/${agentId}/status`;
        const headers = this._getHeaders();
        const data = { status };
        const response = await axios.put(url, data, { headers });
        return response.data;
    }

    async sendMessage(toAgentId, messageContent) {
        const url = `${this.baseUrl}/api/messages/send`;
        const headers = this._getHeaders();
        const data = { to_agent_id: toAgentId, message_content: messageContent };
        const response = await axios.post(url, data, { headers });
        return response.data;
    }

    async getMessageStatus(messageId) {
        const url = `${this.baseUrl}/api/messages/${messageId}`;
        const headers = this._getHeaders();
        const response = await axios.get(url, { headers });
        return response.data;
    }

    verifyWebhookSignature(payload, signature, secretToken) {
        if (signature.startsWith("sha256=")) {
            signature = signature.substring(7);
        }

        const hmac = crypto.createHmac('sha256', secretToken);
        hmac.update(payload);
        const expectedSignature = hmac.digest('hex');

        // Use a constant time comparison to prevent timing attacks
        return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSignature));
    }
}

module.exports = AgentConnectClient;
