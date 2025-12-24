const API_BASE_URL = 'http://localhost:8000/api';

class AgentConnectAPI {
    constructor() {
        this.apiKey = localStorage.getItem('agent_api_key');
    }

    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.apiKey && !options.skipAuth) {
            headers['Authorization'] = `Bearer ${this.apiKey}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }

            return data;
        } catch (error) {
            throw error;
        }
    }

    async registerAgent(name, description, webhookUrl) {
        return this.request('/agents/register', {
            method: 'POST',
            body: JSON.stringify({
                name,
                description,
                webhook_url: webhookUrl
            }),
            skipAuth: true
        });
    }

    async getAgents(status = null) {
        const params = status ? `?status=${status}` : '';
        return this.request(`/agents${params}`, { skipAuth: true });
    }

    async getAgent(agentId) {
        return this.request(`/agents/${agentId}`, { skipAuth: true });
    }

    async updateStatus(agentId, status) {
        return this.request(`/agents/${agentId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
    }

    async sendMessage(toAgentId, messageContent) {
        return this.request('/messages/send', {
            method: 'POST',
            body: JSON.stringify({
                to_agent_id: toAgentId,
                message_content: messageContent
            })
        });
    }

    async getMessageStatus(messageId) {
        return this.request(`/messages/${messageId}`);
    }

    setApiKey(apiKey) {
        this.apiKey = apiKey;
        localStorage.setItem('agent_api_key', apiKey);
    }

    clearApiKey() {
        this.apiKey = null;
        localStorage.removeItem('agent_api_key');
    }

    hasApiKey() {
        return !!this.apiKey;
    }
}

const api = new AgentConnectAPI();