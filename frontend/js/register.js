document.getElementById('agentForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('name').value.trim();
    const description = document.getElementById('description').value.trim();
    const webhookUrl = document.getElementById('webhookUrl').value.trim();
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Registering...';
    
    try {
        const result = await api.registerAgent(name, description, webhookUrl);
        
        document.getElementById('agentIdDisplay').textContent = result.agent_id;
        document.getElementById('apiKeyDisplay').textContent = result.api_key;
        document.getElementById('secretTokenDisplay').textContent = result.secret_token;
        
        api.setApiKey(result.api_key);
        
        document.getElementById('registrationForm').style.display = 'none';
        document.getElementById('successMessage').style.display = 'block';
    } catch (error) {
        alert('Registration failed: ' + error.message);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Register Agent';
    }
});

function copyToClipboard(elementId) {
    const text = document.getElementById(elementId).textContent;
    navigator.clipboard.writeText(text).then(() => {
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    });
}