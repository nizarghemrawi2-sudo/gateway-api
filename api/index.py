from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "j5OXE9NqqCa2JoUXotEQGWDum6lmvFgA" # ⚠️ حط مفتاحك الحقيقي
MY_SECRET = "NIZAR_SECURE_2026"

# هيك شكل البيانات اللي عم توصلك باللوج
class PanelRequest(BaseModel):
    token: str          
    numberId: str       
    note1: str          # رقم المنتج (257)
    orderId: int = None
    note2: str = None   # احتياط للزون
    
@app.get("/")
def home():
    return {"status": "Online", "System": "Gateway Ready"}

# 👇 هون التعديل: كتبنا Buy بالحرف الكبير لتطابق الرابط
@app.post("/api/Buy") 
def process_order(data: PanelRequest):
    
    # 1. فحص التوكن
    if data.token != MY_SECRET:
        return {"error": "Invalid Token"}

    # 2. تحويل رقم المنتج (257) لطلب المورد
    products_map = {
        "257": {"game": "pubg", "pack": "60_uc"},         
        "258": {"game": "freefire", "pack": "100_diamonds"}, 
        "259": {"game": "mobilelegend", "pack": "86"}     
    }

    item = products_map.get(data.note1)
    
    if not item:
        return {"error": f"Product {data.note1} not configured"}

    # 3. تجهيز الطلب
    payload = {
        "game": item["game"],
        "pack": item["pack"],
        "uid": data.numberId 
    }
    
    # معالجة خاصة لـ Mobile Legends
    if item["game"] == "mobilelegend":
        # نفترض الزون جايي بـ note2 أو مدموج، حالياً رح نعتبره ناقص
        if not data.note2 or data.note2 == "-":
             return {"error": "Zone ID missing in note2"}
        payload["zoneId"] = data.note2

    # 4. الشراء الفعلي
    headers = {"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}
    
    try:
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers)
        result = response.json()

        if result.get("success"):
            return {
                "status": "completed", # كلمة بيفهمها موقعك
                "supplier_id": result["data"]["orderId"]
            }
        else:
            return {"status": "error", "message": result.get("error")}

    except Exception as e:
        return {"status": "error", "message": str(e)}
