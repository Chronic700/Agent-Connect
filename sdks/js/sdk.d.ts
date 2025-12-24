declare module "agent-connect-client" {
    export = AgentConnectClient;

    class AgentConnectClient {
        constructor(baseUrl?: string, apiKey?: string);

        register(name: string, description: string, webhookUrl: string): Promise<any>;
        getAgentInfo(agentId: string): Promise<any>;
        listAgents(status?: string, skip?: number, limit?: number): Promise<any>;
        updateStatus(agentId: string, status: string): Promise<any>;
        sendMessage(toAgentId: string, messageContent: any): Promise<any>;
        getMessageStatus(messageId: string): Promise<any>;
        verifyWebhookSignature(payload: string, signature: string, secretToken: string): boolean;
    }
}
