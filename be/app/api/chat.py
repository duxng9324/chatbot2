from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse, HistoryResponse, Message
from app.core.memory import get_session, update_session, add_history
from app.services import llm_service, tour_service
from app.core import i18n

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    user_id = req.user_id
    add_history(user_id, "user", req.message)
    session = get_session(user_id)

    # 1. Phân tích Intent & Trích xuất thông tin (Luôn làm bước này)
    intent_data = llm_service.call_ollama_intent(session, req.message)
    
    # 2. Cập nhật Session (Lưu nhặt dần các thông tin khách nói)
    updates = {}
    if intent_data.departure_point: updates["departure_point"] = intent_data.departure_point
    if intent_data.destination_point: updates["destination_point"] = intent_data.destination_point
    if intent_data.days: updates["days"] = intent_data.days
    if intent_data.people: updates["people"] = intent_data.people
    
    # Lưu ý: Luôn update để nhớ ngữ cảnh cũ (Ví dụ câu trước nói "Đi Đà Nẵng", câu sau nói "3 ngày")
    update_session(user_id, updates)
    session = get_session(user_id) # Reload session mới nhất
    
    current_lang = session.get("language", "vi")
    intent = intent_data.intent

    # 3. XỬ LÝ GỘP (CONSULT_TOUR)
    # Gộp cả SEARCH_TOUR và RECOMMEND_TOUR vào một luồng duy nhất
    if intent in ["SEARCH_TOUR", "RECOMMEND_TOUR", "GREETING"]: 
        
        # a. Lấy các bộ lọc hiện có trong Session
        filters = {
            "departure_point": session.get("departure_point"),
            "destination_point": session.get("destination_point"),
            "days": session.get("days"),
            # "people": session.get("people")
        }
        
        # b. TÌM KIẾM LUÔN (Dựa trên những gì đang có)
        # Nếu chưa có gì -> Tìm hết. Có "Đà Nẵng" -> Tìm Đà Nẵng.
        tours = tour_service.search_tours(
            departure=filters["departure_point"],
            destination=filters["destination_point"],
            days=filters["days"]
        )
        
        # c. NÉM CHO OLLAMA XỬ LÝ (Tư vấn hoặc Hỏi tiếp)
        reply_text = llm_service.call_ollama_consultant(
            user_msg=req.message,
            found_tours=tours,      # Dữ liệu thực tế
            current_filters=filters, # Những gì máy đã hiểu
            lang=current_lang
        )

    # 4. Xử lý BOOKING (Giữ nguyên)
    elif intent == "BOOK_TOUR":
        reply_text = "Dạ vâng! Để chốt đơn, bạn vui lòng để lại Số điện thoại nhé..."
    
    # Fallback
    else:
        reply_text = llm_service.call_ollama_chat(req.message, current_lang)

    add_history(user_id, "ai", reply_text)
    return ChatResponse(reply=reply_text)

@router.get("/history/{user_id}", response_model=HistoryResponse)
def get_chat_history(user_id: str):
    """Lấy toàn bộ lịch sử chat của User"""
    
    # 1. Lấy session từ Redis (hoặc RAM)
    session = get_session(user_id)

    # print("user_id:", user_id)
    # print("session:", session)
    
    # 2. Lấy list history (Mặc định là rỗng nếu chưa có)
    raw_history = session.get("history", [])
    
    # 3. Trả về đúng định dạng Schema
    return HistoryResponse(
        user_id=user_id,
        history=raw_history
    )

# --- (Optional) ENDPOINT XÓA HISTORY ---
@router.delete("/history/{user_id}")
def clear_chat_history(user_id: str):
    """Xóa lịch sử chat để bắt đầu lại"""
    try:
        # Import rds từ memory để xóa key
        from app.core.memory import rds, LOCAL_MEMORY, IS_REDIS_AVAILABLE
        
        key = f"session:{user_id}"
        
        if IS_REDIS_AVAILABLE and rds:
            rds.delete(key)
        else:
            if user_id in LOCAL_MEMORY:
                del LOCAL_MEMORY[user_id]
                
        return {"status": "success", "message": "Đã xóa lịch sử chat"}
    except Exception as e:
        return {"status": "error", "message": str(e)}