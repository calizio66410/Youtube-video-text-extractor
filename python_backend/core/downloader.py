import asyncio
import yt_dlp

def extract_video_info(url: str):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info.get('duration', 0) > 600:
                raise Exception("La vidéo dépasse la limite de 10 minutes.")
            return {
                "title": info.get('title', 'Unknown'),
                "duration": info.get('duration', 0),
                "thumbnail": info.get('thumbnail', '')
            }
    except Exception as e:
        raise Exception(f"Erreur d'extraction info: {str(e)}")

async def download_video(url: str, output_path: str, progress_callback=None):
    def progress_hook(d):
        if d['status'] == 'downloading' and progress_callback:
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            percent = (downloaded / total) * 100 if total > 1 else 0
            
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    progress_callback({"status": "downloading", "progress": percent, "message": f"Téléchargement... {percent:.1f}%"}), 
                    loop
                )

    ydl_opts = {
        'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [progress_hook],
        'socket_timeout': 300
    }
    
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, _run_ytdlp, ydl_opts, url)
    except Exception as e:
        raise Exception(f"Erreur lors du téléchargement: {str(e)}")
        
def _run_ytdlp(ydl_opts, url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
