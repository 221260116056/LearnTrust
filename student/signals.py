from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Module
import os
import subprocess
from django.conf import settings


@receiver(post_save, sender=Module)
def transcode_video(sender, instance, created, **kwargs):
    """
    Trigger video transcoding when teacher uploads a video file.
    Generates 360p, 480p, 720p HLS variants with .ts segments.
    """
    if instance.video_file and not instance.hls_path:
        hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(instance.id))
        os.makedirs(hls_dir, exist_ok=True)
        
        input_path = instance.video_file.path
        
        cmd = [
            'ffmpeg', '-i', input_path,
            '-filter_complex',
            '[0:v]split=3[v360][v480][v720]; [v360]scale=-2:360[360p]; [v480]scale=-2:480[480p]; [v720]scale=-2:720[720p]',
            '-map', '[360p]', '-map', '0:a',
            '-map', '[480p]', '-map', '0:a', 
            '-map', '[720p]', '-map', '0:a',
            '-c:v', 'libx264', '-c:a', 'aac',
            '-b:v:0', '800k', '-b:a:0', '96k',
            '-b:v:1', '1400k', '-b:a:1', '128k',
            '-b:v:2', '2800k', '-b:a:2', '128k',
            '-hls_time', '6',
            '-hls_playlist_type', 'vod',
            '-hls_segment_filename', f'{hls_dir}/%v/segment_%03d.ts',
            '-master_pl_name', 'master.m3u8',
            '-var_stream_map', 'v:0,a:0,name:360p v:1,a:1,name:480p v:2,a:2,name:720p',
            '-f', 'hls',
            f'{hls_dir}/playlist.m3u8'
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            instance.hls_path = f'hls/{instance.id}/master.m3u8'
            instance.save(update_fields=['hls_path'])
        except subprocess.CalledProcessError as e:
            print(f"Transcoding failed for module {instance.id}: {e.stderr}")
