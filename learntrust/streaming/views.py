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
        # Split token into payload and signature
        parts = token.split('.')
        if len(parts) != 2:
            return False
        
        payload_b64, signature = parts
        
        # Add padding to payload if necessary
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        
        # Decode payload
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        
        # Verify signature
        expected_signature = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return False
        
        # Parse payload
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        # Check expiry not passed
        if payload['expiry'] < time.time():
            return False
        
        # Check user_id matches
        if payload['user_id'] != expected_user_id:
            return False
        
        # Check module_id matches
        if payload['module_id'] != expected_module_id:
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
    
    # Check if HLS files exist
    hls_dir = settings.MEDIA_ROOT / 'hls' / str(module_id)
    master_playlist = hls_dir / 'master.m3u8'
    
    if master_playlist.exists():
        # Serve HLS master playlist
        return FileResponse(
            open(master_playlist, 'rb'),
            content_type='application/vnd.apple.mpegurl'
        )
    else:
        # Fallback to regular video file
        video_path = settings.MEDIA_ROOT / 'sample.mp4'
        return FileResponse(open(video_path, 'rb'), content_type='video/mp4')


def stream_hls_segment(request, module_id, filename):
    """
    Serve HLS segment files (.ts) with token validation
    """
    token = request.GET.get('token')
    
    if not token:
        return HttpResponseForbidden("Missing authentication token")
    
    if not validate_token(token, request.user.id, module_id):
        return HttpResponseForbidden("Invalid or expired token")
    
    # Serve segment file
    segment_path = settings.MEDIA_ROOT / 'hls' / str(module_id) / filename
    
    if not segment_path.exists():
        return HttpResponseForbidden("Segment not found")
    
    return FileResponse(
        open(segment_path, 'rb'),
        content_type='video/mp2t'
    )


def stream_hls_playlist(request, module_id, resolution):
    """
    Serve HLS variant playlist files with token validation
    """
    token = request.GET.get('token')
    
    if not token:
        return HttpResponseForbidden("Missing authentication token")
    
    if not validate_token(token, request.user.id, module_id):
        return HttpResponseForbidden("Invalid or expired token")
    
    playlist_path = settings.MEDIA_ROOT / 'hls' / str(module_id) / f'{resolution}.m3u8'
    
    if not playlist_path.exists():
        return HttpResponseForbidden("Playlist not found")
    
    return FileResponse(
        open(playlist_path, 'rb'),
        content_type='application/vnd.apple.mpegurl'
    )


def stream_encryption_key(request, module_id):
    """
    Serve AES-128 encryption key with token authentication
    This endpoint is called by hls.js/player to decrypt segments
    """
    token = request.GET.get('token')
    
    if not token:
        return HttpResponseForbidden("Missing authentication token")
    
    if not validate_token(token, request.user.id, module_id):
        return HttpResponseForbidden("Invalid or expired token")
    
    # Serve the encryption key
    key_path = settings.MEDIA_ROOT / 'hls' / str(module_id) / 'encryption.key'
    
    if not key_path.exists():
        return HttpResponseForbidden("Encryption key not found")
    
    response = FileResponse(
        open(key_path, 'rb'),
        content_type='application/octet-stream'
    )
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    
    return response
