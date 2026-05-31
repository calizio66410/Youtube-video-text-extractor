import difflib

def consolidate_text(results_list):
    if not results_list:
        return []
        
    consolidated = []
    current_text = ""
    current_start = 0
    current_end = 0
    
    for res in results_list:
        text = res["text"].strip()
        timestamp = res["timestamp"]
        
        if not text:
            continue
            
        if not current_text:
            current_text = text
            current_start = timestamp
            current_end = timestamp
            continue
            
        similarity = difflib.SequenceMatcher(None, current_text, text).ratio()
        
        if similarity > 0.8:
            current_end = timestamp
            if len(text) > len(current_text):
                current_text = text
        else:
            consolidated.append({
                "start": current_start,
                "end": current_end,
                "text": current_text
            })
            current_text = text
            current_start = timestamp
            current_end = timestamp
            
    if current_text:
         consolidated.append({
            "start": current_start,
            "end": current_end,
            "text": current_text
        })
         
    return consolidated

def format_output(consolidated_results):
    formatted_texts = []
    srt_lines = []
    total_words = 0
    
    for i, item in enumerate(consolidated_results):
        start_seconds = item["start"]
        end_seconds = item["end"]
        text = item["text"]
        
        words = text.split()
        total_words += len(words)
        
        start_m, start_s = divmod(int(start_seconds), 60)
        end_m, end_s = divmod(int(end_seconds), 60)
        
        formatted_texts.append(f"[{start_m:02d}:{start_s:02d}] {text}")
        
        start_ms = int((start_seconds - int(start_seconds)) * 1000)
        end_ms = int((end_seconds - int(end_seconds)) * 1000)
        srt_lines.append(str(i+1))
        srt_lines.append(f"00:{start_m:02d}:{start_s:02d},{start_ms:03d} --> 00:{end_m:02d}:{end_s:02d},{end_ms:03d}")
        srt_lines.append(text)
        srt_lines.append("")
        
    full_text = "\n".join(formatted_texts)
    srt_text = "\n".join(srt_lines)
    
    duration_covered = 0
    if consolidated_results:
        duration_covered = consolidated_results[-1]["end"] - consolidated_results[0]["start"]
        
    return {
        "text_with_timestamps": full_text,
        "srt": srt_text,
        "raw_consolidated": consolidated_results,
        "stats": {
            "total_words": total_words,
            "blocks": len(consolidated_results),
            "duration_covered_sec": duration_covered
        }
    }
