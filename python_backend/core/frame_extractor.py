import cv2
import os
import asyncio

def extract_frames(video_path: str, output_dir: str, interval: float = 2.0, progress_callback=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Impossible d'ouvrir la vidéo pour l'extraction.")
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or fps != fps:
        fps = 25.0
        
    total_frames_in_video = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames_in_video / fps if fps > 0 else 0
    
    if video_duration > 300:
        interval = max(interval, 5.0)
        
    frame_interval = int(fps * interval)
    if frame_interval <= 0:
        frame_interval = 1
        
    count = 0
    extracted_count = 0
    saved_frames = []
    prev_hist = None
    loop = asyncio.get_event_loop()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if count % frame_interval == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            cv2.normalize(hist, hist)
            
            skip = False
            if prev_hist is not None:
                diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)
                if diff < 0.05:
                    skip = True
            
            if not skip:
                timestamp = count / fps
                filename = f"frame_{int(timestamp):04d}.png"
                filepath = os.path.join(output_dir, filename)
                
                h, w = frame.shape[:2]
                if w > 1080:
                    scale = 1080 / w
                    frame = cv2.resize(frame, (1080, int(h * scale)))
                
                cv2.imwrite(filepath, frame)
                saved_frames.append({"path": filepath, "timestamp": timestamp})
                prev_hist = hist
                extracted_count += 1
                
                if progress_callback and extracted_count % 10 == 0:
                    percent_done = min((count / total_frames_in_video) * 100, 100)
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            progress_callback({"status": "extracting", "progress": percent_done, "message": f"Extraction frames... {extracted_count} sauvées"}), 
                            loop
                        )
        count += 1
        
    cap.release()
    return saved_frames
