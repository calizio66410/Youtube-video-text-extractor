import cv2
import pytesseract
import concurrent.futures
import asyncio

def preprocess_image(image_path: str):
    image = cv2.imread(image_path)
    if image is None:
        return None
        
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    h, w = gray.shape
    if h < 720:
        gray = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(blur)
    
    thresh = cv2.adaptiveThreshold(contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    morph = cv2.dilate(thresh, kernel, iterations=1)
    
    return morph

def process_single_image(frame_data, lang='fra+eng'):
    image_path = frame_data["path"]
    timestamp = frame_data["timestamp"]
    
    processed_img = preprocess_image(image_path)
    if processed_img is None:
        return {"timestamp": timestamp, "text": "", "words": []}
        
    custom_config = r'--oem 3 --psm 11'
    data = pytesseract.image_to_data(processed_img, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)
    
    extracted_words = []
    full_text_parts = []
    
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        conf = float(data['conf'][i])
        text = data['text'][i].strip()
        
        if conf >= 60.0 and len(text) > 0:
            extracted_words.append({
                "text": text,
                "conf": conf,
                "box": (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            })
            full_text_parts.append(text)
            
    return {
        "timestamp": timestamp,
        "text": " ".join(full_text_parts),
        "words": extracted_words
    }

async def run_ocr_on_frames(frames, lang='fra+eng', progress_callback=None):
    results = []
    total = len(frames)
    loop = asyncio.get_event_loop()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = []
        for frame in frames:
            fut = loop.run_in_executor(pool, process_single_image, frame, lang)
            futures.append(fut)
            
        done = 0
        for f in asyncio.as_completed(futures):
            res = await f
            if res["text"]:
                results.append(res)
            done += 1
            if progress_callback and done % 5 == 0:
                percent = (done / total) * 100
                await progress_callback({
                    "status": "ocr", 
                    "progress": percent, 
                    "message": f"OCR en cours... {done}/{total} frames traitées"
                })
                
    results.sort(key=lambda x: x["timestamp"])
    return results
