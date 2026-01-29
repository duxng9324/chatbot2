# 📦 Chatbot Stour – Hướng dẫn chạy dự án

Dự án gồm **2 phần chính**:

- **Backend (BE)**: Python (FastAPI) – xử lý AI, chat, tour
- **Frontend (FE)**: Next.js – hiển thị chatbot widget

---

## 🧩 Cấu trúc tổng quan

```txt
chatbot-stour
├── be/            # Backend FastAPI
├── chatbot/       # Frontend Next.js (chatbot widget)
└── .git/
```

---

## ✅ Yêu cầu môi trường

### Backend
- Python >= **3.10**
- pip

### Frontend
- Node.js **20.x**
- npm

# 🚀 Chạy BACKEND (FastAPI)

## 1️⃣ Khởi tạo Redis bằng docker

```bash
docker run -d -p 6379:6379 --name redis-stour redis
```

## 2️⃣ Di chuyển vào thư mục backend

```bash
cd be
```

## 3️⃣ Tạo virtual environment (khuyến nghị)

```bash
python -m venv venv
```

### Kích hoạt venv

**Windows**
```bash
venv\Scripts\activate
```

**Mac / Linux**
```bash
source venv/bin/activate
```

## 3️⃣ Cài dependency

```bash
pip install -r requirements.txt
```

## 4️⃣ Chạy server

```bash
python run.py
```

Hoặc:

```bash
uvicorn app.main:app --port 8000
```

✅ Backend chạy tại:
```
http://localhost:8000
```

---

# 🚀 Chạy FRONTEND (Next.js)

## 1️⃣ Di chuyển vào thư mục chatbot

```bash
cd chatbot
```

## 2️⃣ Cài dependency

```bash
npm install
```

> Nếu gặp lỗi react / react-dom:
```bash
npm install react@18.2.0 react-dom@18.2.0
```

## 3️⃣ Chạy dev server

```bash
npm run dev
```

✅ Frontend chạy tại:
```
http://localhost:3001
```

---

# 🤖 Chatbot Widget

- Component chính:  
  `chatbot/components/ChatbotWidget.tsx`

- Hook xử lý logic:  
  `chatbot/hooks/useChatbot.ts`

- API backend sử dụng:
  - `POST /ai/chat`
  - `GET /ai/history`

---

# 🔄 Load lịch sử chat

Frontend **tự động load lịch sử chat** khi mở widget bằng API:

```
GET http://localhost:8000/ai/history
```

---

# 🛠 Các lỗi thường gặp

### ❌ Trắng màn hình
- Sai version React / React-DOM
- Dùng `useLayoutEffect`
- Import component MF khi SSR

👉 Đảm bảo:
- `"use client"`
- dynamic import `{ ssr: false }`

---

### ❌ Shared module react-dom doesn't exist
- React version không đồng bộ
- Module Federation config sai

👉 Fix nhanh:
```bash
npm install react@18.2.0 react-dom@18.2.0
```
---

# 📌 Ghi chú

- Backend & Frontend **phải chạy song song**
- Nếu đổi port BE → nhớ update `apiBaseUrl` trong ChatbotWidget
