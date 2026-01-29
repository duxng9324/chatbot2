import requests
import json
import re
from app.config import settings
from app.core.prompts import build_intent_prompt, SYSTEM_INSTRUCTION
from app.schemas.chat import IntentData

def extract_json(text: str):
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else None

def normalize_days(days):
    if isinstance(days, str):
        match = re.search(r"\d+", days)
        return int(match.group()) if match else None
    return days

def call_ollama_intent(session: dict, message: str) -> IntentData:
    prompt = build_intent_prompt(session, message)
    payload = {"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False}

    try:
        res = requests.post(settings.OLLAMA_URL, json=payload, timeout=60)
        res.raise_for_status()
        raw = res.json().get("response", "")
        
        json_text = extract_json(raw)
        if not json_text:
            return IntentData(intent="UNKNOWN")

        data = json.loads(json_text)
        
        # Chuẩn hóa
        data["days"] = normalize_days(data.get("days"))
        try:
            if data.get("people"): data["people"] = int(data.get("people"))
        except:
            data["people"] = None
            
        return IntentData(**data)
        
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return IntentData(intent="UNKNOWN")

def call_ollama_chat(message: str, lang: str) -> str:
    prompt = f"{SYSTEM_INSTRUCTION.format(lang=lang)}\nUser: {message}"
    payload = {"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False}
    try:
        res = requests.post(settings.OLLAMA_URL, json=payload, timeout=120)
        return res.json().get("response", "")
    except:
        return "Service unavailable."

def call_ollama_consultant(user_msg: str, found_tours: list, current_filters: dict, lang: str = "vi") -> str:
    """
    Hàm này để Ollama tự quyết định: Nên hỏi tiếp hay nên trả lời danh sách tour.
    """
    
    # 1. Tóm tắt danh sách tour (chỉ lấy 3 cái đầu để tiết kiệm token)
    tours_summary = []
    for t in found_tours[:3]:
        tours_summary.append(f"- {t['tenTour']} ({t['soNgay']} ngày): {int(t['gia']):,}đ")
    
    tours_text = "\n".join(tours_summary) if tours_summary else "Không tìm thấy tour nào phù hợp."
    
    # 2. Xác định thông tin đang có
    missing_info = []
    if not current_filters.get('destination_point'): missing_info.append("Điểm đến")
    if not current_filters.get('departure_point'): missing_info.append("Nơi khởi hành")
    # if not current_filters.get('days'): missing_info.append("Số ngày dự kiến") # Có thể bỏ qua nếu muốn tư vấn thoáng hơn

    missing_text = ", ".join(missing_info)

    # 3. Prompt thông minhz
    system_prompt = f"""
    Bạn là nhân viên tư vấn du lịch xuất sắc.
    Ngôn ngữ: {lang}
    
    TÌNH TRẠNG HIỆN TẠI:
    - Khách đang tìm kiếm với bộ lọc: {json.dumps(current_filters, ensure_ascii=False)}
    - Kết quả tìm được ({len(found_tours)} tour):
    {tours_text}
    
    NHIỆM VỤ CỦA BẠN (Chọn 1 trong 2 hướng):
    
    HƯỚNG 1 (Hỏi thêm): Nếu kết quả tìm kiếm quá nhiều (>5) HOẶC không tìm thấy gì, VÀ còn thiếu thông tin quan trọng ({missing_text}):
    -> Hãy khéo léo hỏi khách thông tin còn thiếu để lọc kỹ hơn. Đừng hỏi như công an, hãy hỏi gợi mở.
    
    HƯỚNG 2 (Tư vấn): Nếu đã tìm thấy tour phù hợp (có kết quả trong danh sách trên):
    -> Hãy giới thiệu ngay các tour đó thật hấp dẫn (dùng Emoji 🌟✈️). 
    -> Bỏ qua việc hỏi thông tin thiếu nếu bạn cảm thấy danh sách tour này đã đủ tốt để gợi ý.
    
    Lưu ý: Chỉ tư vấn tour có trong danh sách trên. Câu trả lời ngắn gọn, thân thiện, trả lời bằng ngôn ngữ {lang}.
    """

    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": f"{system_prompt}\n\nKhách nói: \"{user_msg}\"",
        "stream": False,
        "options": {"temperature": 0.6}
    }

    try:
        print("🤖 Ollama đang suy nghĩ chiến thuật tư vấn...")
        res = requests.post(settings.OLLAMA_URL, json=payload, timeout=120) # Timeout cao vì prompt dài
        return res.json().get("response", "")
    except Exception as e:
        print(f"❌ Lỗi AI Consultant: {e}")
        # Fallback cứng nếu AI chết
        if found_tours:
            return "Mình tìm thấy vài tour này, bạn xem thử nhé:\n" + tours_text
        return "Bạn muốn đi du lịch ở đâu nhỉ? Cho mình biết thêm chi tiết nha."