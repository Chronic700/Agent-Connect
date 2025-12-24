let currentAgentId = null;

function checkLogin() {
    if (!api.hasApiKey()) {
        document.getElementById('loginPrompt').style.display = 'block';
        document.getElementById('dashboardContent').style.display = 'none';
    } else {
        document.getElementById('loginPrompt').style.display = 'none';
        document.getElementById('dashboardContent').style.display = 'block';
    }
}

document.getElementById('loginForm')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const apiKey = document.getElementById('apiKeyInput').value.trim();
    api.setApiKey(apiKey);
    location.reload();
});

function logout() {
    api.clearApiKey();
    location.reload();
}

async function updateStatus() {
    const status = document.getElementById('statusSelect').value;
    
    if (!currentAgentId) {
        alert('Agent ID not found');
        return;
    }
    
    try {
        await api.updateStatus(currentAgentId, status);
        document.getElementById('currentStatus').textContent = status;
        document.getElementById('currentStatus').className = `status ${status}`;
        alert('Status updated successfully');
    } catch (error) {
        alert('Failed to update status: ' + error.message);
    }
}

document.getElementById('sendMessageForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const recipientId = document.getElementById('recipientId').value.trim();
    const messageText = document.getElementById('messageText').value.trim();
    const resultDiv = document.getElementById('sendResult');
    
    try {
        const result = await api.sendMessage(recipientId, { text: messageText });
        resultDiv.innerHTML = `
            <div class="alert alert-success">
                Message sent! ID: ${result.message_id}<br>
                Status: ${result.status}
            </div>
        `;
        document.getElementById('messageText').value = '';
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="alert alert-error">
                Failed to send message: ${error.message}
            </div>
        `;
    }
});

checkLogin();