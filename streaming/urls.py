from django.urls import path
from . import views

urlpatterns = [
    # Master HLS playlist
    path('stream/<int:module_id>/', views.stream_video, name='stream_video'),
    
    # Encryption key (protected by token)
    path('stream/key/<int:module_id>/', 
         views.stream_encryption_key, 
         name='stream_encryption_key'),
    
    # HLS variant playlists (360p, 480p, 720p)
    path('stream/<int:module_id>/<str:resolution>.m3u8', 
         views.stream_hls_playlist, 
         name='stream_hls_playlist'),
    
    # HLS segment files
    path('stream/<int:module_id>/<str:filename>.ts', 
         views.stream_hls_segment, 
         name='stream_hls_segment'),
]
