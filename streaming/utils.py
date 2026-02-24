import hmac
import hashlib
import base64
import json
import time
from django.conf import settings


def generate_signed_token(user_id, module_id):
    """
    Generate HMAC-signed token for video streaming access.
    Token expires in 10 minutes.
    Format: base64payload.signature
    """
    expiry = int(time.time()) + 600  # 10 minutes from now
    
    payload = {
        'user_id': user_id,
        'module_id': module_id,
        'expiry': expiry
    }
    
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_bytes = payload_json.encode('utf-8')
    
    # Base64 encode payload
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode('utf-8').rstrip('=')
    
    # Generate HMAC SHA256 signature
    signature = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    # Return token as: base64payload.signature
    return f"{payload_b64}.{signature}"
