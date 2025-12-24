let allAgents = [];

async function loadAgents() {
    const loading = document.getElementById('loading');
    const grid = document.getElementById('agentGrid');
    const statusFilter = document.getElementById('statusFilter');
    
    try {
        const data = await api.getAgents();
        allAgents = data.agents;
        
        loading.style.display = 'none';
        displayAgents(allAgents);
        
        statusFilter.addEventListener('change', () => {
            const status = statusFilter.value;
            const filtered = status 
                ? allAgents.filter(a => a.status === status)
                : allAgents;
            displayAgents(filtered);
        });
    } catch (error) {
        loading.textContent = 'Error loading agents: ' + error.message;
    }
}

function displayAgents(agents) {
    const grid = document.getElementById('agentGrid');
    const countEl = document.getElementById('agentCount');
    
    countEl.textContent = `${agents.length} agent${agents.length !== 1 ? 's' : ''}`;
    
    if (agents.length === 0) {
        grid.innerHTML = '<p style="text-align: center; color: #666;">No agents found</p>';
        return;
    }
    
    grid.innerHTML = agents.map(agent => `
        <div class="agent-card">
            <h3>${escapeHtml(agent.name)}</h3>
            <div class="agent-id">${escapeHtml(agent.agent_id)}</div>
            <p>${escapeHtml(agent.description)}</p>
            <div style="margin-top: 1rem;">
                <span class="status ${agent.status}">${agent.status}</span>
            </div>
            <div style="margin-top: 0.5rem; font-size: 0.85rem; color: #666;">
                Registered: ${new Date(agent.created_at).toLocaleDateString()}
            </div>
        </div>
    `).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

loadAgents();