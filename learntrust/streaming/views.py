import hmac
import hashlib
import base64
import json
import time
from django.http import HttpResponseForbidden, FileResponse
from django.conf import settings
from django.shortcuts import get_object_or_404
from student.models import Module


def validate_token(token, expected_user_id, expected_module_id):
    """Validate signed token and check expiration."""
    try:
        # Add padding if necessary
        padding = 4 - len(token) % 4
        if padding != 4:
            token += '=' * padding
        
        token_data = json.loads(base64.urlsafe_b64decode(token).decode('utf-8'))
        
        # Verify signature
        payload_b64 = token_data['payload']
        signature = token_data['signature']
        
        # Add padding to payload if necessary
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        
        expected_signature = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return False
        
        # Parse payload
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        # Check expiration
        if payload['expires_at'] < time.time():
            return False
        
        # Check user_id and module_id match
        if payload['user_id'] != expected_user_id or payload['module_id'] != expected_module_id:
            return False
        
        return True
    except Exception:
        return False


def stream_video(request, module_id):
    """
    Stream video with signed token validation.
    Requires 'token' in query parameters.
    """
    token = request.GET.get('token')
    
    if not token:
        return HttpResponseForbidden("Missing authentication token")
    
    module = get_object_or_404(Module, id=module_id)
    
    if not validate_token(token, request.user.id, module_id):
        return HttpResponseForbidden("Invalid or expired token")
    
    # Serve video file (adjust path as needed)
    video_path = settings.MEDIA_ROOT / 'sample.mp4'
    
    return FileResponse(open(video_path, 'rb'), content_type='video/mp4')
