"""
HLS Streaming Utilities with AES-128 Encryption
"""

import os
import subprocess
import secrets
from django.conf import settings


def generate_encryption_key(module_id):
    """
    Generate a random 128-bit (16 bytes) AES encryption key for HLS
    """
    hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(module_id))
    os.makedirs(hls_dir, exist_ok=True)
    
    key_path = os.path.join(hls_dir, 'encryption.key')
    
    # Generate 16 random bytes (128 bits) for AES-128
    key = secrets.token_bytes(16)
    
    # Write key to file
    with open(key_path, 'wb') as f:
        f.write(key)
    
    # Generate IV (Initialization Vector)
    iv = secrets.token_hex(16)  # 32 hex characters = 16 bytes
    
    # Save IV to file
    iv_path = os.path.join(hls_dir, 'encryption.iv')
    with open(iv_path, 'w') as f:
        f.write(iv)
    
    return {
        'key_path': key_path,
        'iv': iv,
        'key_url': f'/stream/key/{module_id}/'
    }


def generate_hls_files(video_path, module_id):
    """
    Generate HLS adaptive streaming files with AES-128 encryption
    """
    # Create output directory
    hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(module_id))
    os.makedirs(hls_dir, exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # Generate encryption key
    encryption = generate_encryption_key(module_id)
    key_path = encryption['key_path']
    key_iv = encryption['iv']
    
    # Generate key info file for FFmpeg
    key_info_path = os.path.join(hls_dir, 'key_info.txt')
    with open(key_info_path, 'w') as f:
        # Format: key URI, key file path, IV (optional)
        f.write(f"{encryption['key_url']}\n")
        f.write(f"{key_path}\n")
        f.write(f"{key_iv}\n")
    
    # FFmpeg command with AES-128 encryption
    cmd = [
        'ffmpeg',
        '-i', video_path,
        # 360p variant with encryption
        '-vf', 'scale=-2:360',
        '-c:v', 'libx264',
        '-b:v', '800k',
        '-c:a', 'aac',
        '-b:a', '96k',
        '-hls_time', '6',
        '-hls_playlist_type', 'vod',
        '-hls_segment_filename', f'{hls_dir}/360p_%03d.ts',
        '-hls_key_info_file', key_info_path,
        '-f', 'hls',
        f'{hls_dir}/360p.m3u8',
        # 480p variant with encryption
        '-vf', 'scale=-2:480',
        '-c:v', 'libx264',
        '-b:v', '1400k',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-hls_time', '6',
        '-hls_playlist_type', 'vod',
        '-hls_segment_filename', f'{hls_dir}/480p_%03d.ts',
        '-hls_key_info_file', key_info_path,
        '-f', 'hls',
        f'{hls_dir}/480p.m3u8',
        # 720p variant with encryption
        '-vf', 'scale=-2:720',
        '-c:v', 'libx264',
        '-b:v', '2800k',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-hls_time', '6',
        '-hls_playlist_type', 'vod',
        '-hls_segment_filename', f'{hls_dir}/720p_%03d.ts',
        '-hls_key_info_file', key_info_path,
        '-f', 'hls',
        f'{hls_dir}/720p.m3u8',
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Generate master playlist
        master_playlist = generate_master_playlist(hls_dir, base_name)
        
        return {
            'master_playlist': master_playlist,
            '360p': f'{hls_dir}/360p.m3u8',
            '480p': f'{hls_dir}/480p.m3u8',
            '720p': f'{hls_dir}/720p.m3u8',
            'directory': hls_dir,
            'encryption': encryption
        }
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr}")
        return None


def generate_master_playlist(hls_dir, base_name):
    """Generate master.m3u8 playlist for adaptive streaming"""
    master_path = os.path.join(hls_dir, 'master.m3u8')
    
    playlist_content = """#EXTM3U
#EXT-X-VERSION:3

#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
360p.m3u8

#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=854x480
480p.m3u8

#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720
720p.m3u8
"""
    
    with open(master_path, 'w') as f:
        f.write(playlist_content)
    
    return master_path


def check_hls_exists(module_id):
    """Check if HLS files already exist for a module"""
    hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(module_id))
    master_file = os.path.join(hls_dir, 'master.m3u8')
    return os.path.exists(master_file)
