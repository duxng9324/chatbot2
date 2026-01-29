def build_intent_prompt(session, current_message):
    history_text = ""
    if session.get("history"):
        for h in session["history"][-6:]:
            role = "User" if h["role"] == "user" else "Assistant"
            history_text += f"{role}: {h['content']}\n"

    return f"""
Bạn là AI đặt tour. Phân tích câu nói để trích xuất thông tin.

Lịch sử chat:
{history_text}

Câu người dùng: "{current_message}"

Nhiệm vụ: Xác định Intent và trích xuất thông tin.

ĐỊNH NGHĨA INTENT (Rất quan trọng):
1. "SEARCH_TOUR": CHỈ KHI người dùng nhắc đến **ĐỊA ĐIỂM** hoặc **THỜI GIAN** cụ thể.
   - Ví dụ: "Tìm tour đi Đà Nẵng", "Có tour nào đi biển không?", "Đi Sapa mấy tiền?", "Tour 3 ngày 2 đêm".
   
2. "RECOMMEND_TOUR": Khi người dùng hỏi **DANH SÁCH** hoặc **GỢI Ý** mà KHÔNG có địa điểm cụ thể.
   - Ví dụ: "Bạn có những tour nào?", "Liệt kê các tour đang có", "Gợi ý cho tôi đi chơi", "Bên mình có gì hot?".

3. "BOOK_TOUR": Muốn đặt vé, chốt đơn.
4. "GREETING": Chào hỏi xã giao.

Format JSON bắt buộc:
{{
  "intent": "GREETING" | "SEARCH_TOUR" | "RECOMMEND_TOUR" | "BOOK_TOUR" | "UNKNOWN",
  "departure_point": string (Nơi đi) hoặc null,
  "destination_point": string (Nơi đến) hoặc null,
  "people": number hoặc null,
  "days": number hoặc null,
  "language": "vi" | "en"
}}
"""

SYSTEM_INSTRUCTION = """
Bạn là trợ lý du lịch chuyên nghiệp. 
Hãy trả lời câu hỏi một cách ngắn gọn, thân thiện bằng ngôn ngữ: {lang}.
**Yêu cầu định dạng:** Sử dụng Markdown (in đậm, gạch đầu dòng, heading, code block) để câu trả lời dễ đọc hơn.
"""