import os
import shutil
import asyncio

from core.downloader import extract_video_info, download_video
from core.frame_extractor import extract_frames
from core.ocr_engine import run_ocr_on_frames
from core.text_processor import consolidate_text, format_output

class ExtractionPipeline:
    def __init__(self, job_id, url, lang, interval, fast_mode):
        self.job_id = job_id
        self.url = url
        self.lang = lang
        self.interval = interval if not fast_mode else interval * 2
        self.fast_mode = fast_mode
        self.work_dir = f"tmp/job_{self.job_id}"
        self.video_path = os.path.join(self.work_dir, "video.mp4")
        self.frames_dir = os.path.join(self.work_dir, "frames")
        
    async def run(self, progress_callback):
        try:
            os.makedirs(self.work_dir, exist_ok=True)
            os.makedirs(self.frames_dir, exist_ok=True)
            
            await progress_callback({"status": "downloading", "progress": 0, "message": "Récupération infos vidéo..."})
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, extract_video_info, self.url)
            
            await progress_callback({"status": "downloading", "progress": 5, "message": f"Téléchargement de {info['title'][:30]}..."})
            await download_video(self.url, self.video_path, progress_callback)
            
            await progress_callback({"status": "extracting", "progress": 0, "message": "Démarrage extraction frames..."})
            frames = await loop.run_in_executor(None, extract_frames, self.video_path, self.frames_dir, self.interval, progress_callback)
            
            if not frames:
                raise Exception("Aucune frame n'a pu être extraite.")
                
            await progress_callback({"status": "ocr", "progress": 0, "message": f"Démarrage OCR sur {len(frames)} frames..."})
            ocr_results = await run_ocr_on_frames(frames, self.lang, progress_callback)
            
            if not ocr_results:
                raise Exception("Aucun texte n'a été détecté dans la vidéo.")
                
            await progress_callback({"status": "processing", "progress": 90, "message": "Consolidation du texte..."})
            consolidated = consolidate_text(ocr_results)
            final_result = format_output(consolidated)
            
            return {
                "info": info,
                "data": final_result
            }
            
        except Exception as e:
            raise e
        finally:
            self.cleanup()
            
    def cleanup(self):
        try:
            if os.path.exists(self.work_dir):
                shutil.rmtree(self.work_dir)
        except:
            pass
