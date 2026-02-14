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
    """
    expires_at = int(time.time()) + 600  # 10 minutes
    
    payload = {
        'user_id': user_id,
        'module_id': module_id,
        'expires_at': expires_at
    }
    
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_bytes = payload_json.encode('utf-8')
    
    signature = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    token_data = {
        'payload': base64.urlsafe_b64encode(payload_bytes).decode('utf-8').rstrip('='),
        'signature': signature
    }
    
    return base64.urlsafe_b64encode(
        json.dumps(token_data).encode('utf-8')
    ).decode('utf-8').rstrip('=')
