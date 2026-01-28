from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "YOUR_REAL_API_KEY_HERE" # ⚠️ مفتاحك الحقيقي
MY_SECRET = "NIZAR_SECURE_2026"

class OrderRequest(BaseModel):
    player_id: str
    product_code: str
    api_secret: str
    zone_id: str = None 

class CheckRequest(BaseModel):
    transaction_id: str # رقم الطلب عند المورد
    api_secret: str

@app.get("/")
def home():
    return {"status": "Online", "System": "Gateway V2 🚀"}

# --- الرابط الأول: إرسال الطلب ---
@app.post("/api/buy")
def process_order(order: OrderRequest):
    if order.api_secret != MY_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    products_map = {
        "PUBG_60":  {"game": "pubg", "pack": "60_uc"},
        "FF_100":   {"game": "freefire", "pack": "100_diamonds"},
        "ML_86":    {"game": "mobilelegend", "pack": "86"},
    }

    item = products_map.get(order.product_code)
    if not item:
        return {"success": False, "message": "Product code not found"}

    payload = {
        "game": item["game"],
        "pack": item["pack"],
        "uid": order.player_id
    }
    if item["game"] == "mobilelegend":
        if not order.zone_id:
            return {"success": False, "message": "Zone ID required"}
        payload["zoneId"] = order.zone_id

    headers = {"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}
    
    try:
        # إرسال الطلب فقط (بدون انتظار النتيجة النهائية)
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers)
        result = response.json()

        if result.get("success"):
            # بنرجع رقم الطلب للموقع فوراً
            return {
                "success": True,
                "status": "processing", # لسا ما خلص
                "transaction_id": result["data"]["orderId"], 
                "message": "Order Submitted. Please check status."
            }
        else:
            return {"success": False, "message": result.get("error")}

    except Exception as e:
        return {"success": False, "message": str(e)}

# --- الرابط الثاني: فحص الحالة (جديد) ---
@app.post("/api/check_status")
def check_status(req: CheckRequest):
    if req.api_secret != MY_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    headers = {"X-API-Key": SUPPLIER_API_KEY}
    
    try:
        # نسأل المورد عن حالة هذا الطلب
        response = requests.get(f"{SUPPLIER_URL}/orders/{req.transaction_id}", headers=headers)
        data = response.json()
        
        if not data.get("success"):
             return {"success": False, "status": "unknown"}
        
        supplier_status = data["data"]["status"] # processing, done, failed
        
        return {
            "success": True,
            "transaction_id": req.transaction_id,
            "status": supplier_status 
        }

    except Exception as e:
         return {"success": False, "message": str(e)}
