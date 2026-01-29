'use client'

import { useState, useEffect, useCallback } from 'react';

export interface ChatMessage {
  role: 'user' | 'bot';
  message: string;
}

interface UseChatbotProps {
  userId?: string;    
  apiBaseUrl: string;  
}

export function useChatbot({ userId, apiBaseUrl }: UseChatbotProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // State lưu ID thực tế sẽ dùng (User thật hoặc Guest tự sinh)
  const [sessionId, setSessionId] = useState<string>("");

  // --- 1. XÁC ĐỊNH SESSION ID (Logic Guest) ---
  useEffect(() => {
    // Nếu đã có User ID (đăng nhập) -> Dùng luôn
    if (userId) {
      setSessionId(userId);
      return;
    }

    // Nếu chưa đăng nhập -> Xử lý Guest ID (Chỉ chạy ở Client)
    if (typeof window !== 'undefined') {
      let guestId = localStorage.getItem("tour_chatbot_guest_id");
      
      if (!guestId) {
        // Tạo ID ngẫu nhiên: guest_xyz123...
        guestId = `guest_${Math.random().toString(36).substring(2, 11)}_${Date.now()}`;
        localStorage.setItem("tour_chatbot_guest_id", guestId);
      }
      
      setSessionId(guestId);
    }
  }, [userId]);

  // --- 2. TẢI LỊCH SỬ CHAT ---
  useEffect(() => {
    // Chỉ chạy khi đã xác định được sessionId (không phải chuỗi rỗng)
    if (!sessionId) return;

    const fetchHistory = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${apiBaseUrl}/ai/history/${sessionId}`);
        
        // Nếu guest mới tinh chưa có lịch sử (404 hoặc list rỗng), API có thể trả về lỗi nhẹ hoặc rỗng
        // Ta chỉ throw error nếu là lỗi server thực sự (500)
        if (res.status === 500) throw new Error('Server Error');

        const data = await res.json();

        if (data.history && Array.isArray(data.history)) {
          const mappedHistory = data.history.map((msg: any) => ({
            role: msg.role === 'ai' ? 'bot' : 'user',
            message: msg.content,
          }));
          setMessages(mappedHistory);
        }
      } catch (err) {
        console.error("Lỗi tải history:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [sessionId, apiBaseUrl]); // ⚠️ Quan trọng: Phụ thuộc vào sessionId

  // --- 3. GỬI TIN NHẮN ---
  const sendMessage = useCallback(async (messageText: string) => {
    if (!messageText.trim() || !sessionId) return; // Chặn nếu chưa có ID

    setError(null);
    
    // UI Update
    const userMsg: ChatMessage = { role: 'user', message: messageText };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch(`${apiBaseUrl}/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageText,
          user_id: sessionId, 
        }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);

      const data = await res.json();
      const botMsg: ChatMessage = { role: 'bot', message: data.reply };
      setMessages((prev) => [...prev, botMsg]);

    } catch (err) {
      console.error("Lỗi chat:", err);
      setError("Mất kết nối server.");
      setMessages((prev) => [
        ...prev, 
        { role: 'bot', message: "⚠️ *Hệ thống đang bận, vui lòng thử lại sau.*" }
      ]);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, sessionId]); // ⚠️ Phụ thuộc vào sessionId

  const clearChat = useCallback(() => {
      setMessages([]);
      if(sessionId) {
          fetch(`${apiBaseUrl}/ai/reset/${sessionId}`, { method: 'DELETE' }).catch(console.error);
      }
  }, [apiBaseUrl, sessionId]);

  return { messages, sendMessage, loading, error, clearChat };
}