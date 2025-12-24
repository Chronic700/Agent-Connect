from flask import Flask, request
from app.core.security import verify_webhook_signature

app = Flask(__name__)

SECRET_TOKEN = "dAOyrBx4e0TmJOF5YJPF6FYAUDg4P4xKh3MqZPR6tI8"  # Replace with actual token

@app.route('/webhook', methods=['POST'])
def webhook():
    # Verify signature
    signature = request.headers.get('X-Signature', '')
    payload = request.data.decode('utf-8')
    
    if not verify_webhook_signature(payload, signature, SECRET_TOKEN):
        print("Invalid signature!")
        return "Invalid signature", 401
    
    data = request.json
    print(f"Received message from {data['from_agent_id']}")
    print(f"   Content: {data['message_content']}")
    return "OK", 200

@app.route('/webhook', methods=['GET'])
def webhook_info():
    return "Webhook endpoint is working. Send POST requests here.", 200

if __name__ == '__main__':
    print("Test webhook server running on http://localhost:5001/webhook")
    app.run(port=5001)