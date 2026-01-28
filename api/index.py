from fastapi import FastAPI, Form, Request
import requests

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "j5OXE9NqqCa2JoUXotEQGWDum6lmvFgA" # ⚠️ مفتاحك الحقيقي
MY_SECRET = "NIZAR_SECURE_2026"

@app.get("/")
def home():
    return {"status": "Online", "System": "Gateway V4 (Form Data) 🚀"}

# استخدمنا Form بدلاً من BaseModel لنقبل بيانات موقعك
@app.post("/api/Buy")
async def process_order(
    token: str = Form(...),       # إجباري
    numberId: str = Form(...),    # إجباري
    note1: str = Form(...),       # رقم المنتج (257)
    note2: str = Form(None),      # اختياري (للزون)
    orderId: str = Form(None)     # اختياري
):
    
    # 1. فحص التوكن
    if token != MY_SECRET:
        return {"error": "Invalid Token", "ws": {"detail": "Auth Failed"}}

    # 2. تحويل رقم المنتج (257) لطلب المورد
    products_map = {
        "257": {"game": "pubg", "pack": "60_uc"},         
        "258": {"game": "freefire", "pack": "100_diamonds"}, 
        "259": {"game": "mobilelegend", "pack": "86"}     
    }

    item = products_map.get(note1)
    
    if not item:
        return {"error": f"Product {note1} not configured in Gateway"}

    # 3. تجهيز الطلب
    payload = {
        "game": item["game"],
        "pack": item["pack"],
        "uid": numberId
    }
    
    # معالجة خاصة لـ Mobile Legends
    if item["game"] == "mobilelegend":
        # إذا الزون غير موجود أو عبارة عن شرطة "-"
        if not note2 or note2 == "-":
             return {"error": "Zone ID is required for MLBB", "ws": {"detail": "Missing Zone"}}
        payload["zoneId"] = note2

    # 4. الشراء الفعلي
    headers = {"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}
    
    try:
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers)
        result = response.json()

        if result.get("success"):
            return {
                "status": "completed", 
                "order_id": result["data"]["orderId"],
                "api_order_id": orderId # بنرجع نفس الرقم اللي وصلنا
            }
        else:
            return {"status": "error", "message": result.get("error")}

    except Exception as e:
        return {"status": "error", "message": str(e)}
