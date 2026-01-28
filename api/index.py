from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

# --- إعدادات المورد (Son of Utred) ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
# ⚠️ هام: حط مفتاح الـ API تبعك هون (جيبه من بوت التيليجرام)
SUPPLIER_API_KEY = "j5OXE9NqqCa2JoUXotEQGWDum6lmvFgA"

# كلمة السر الخاصة فيك للحماية
MY_SECRET = "NIZAR_SECURE_2026"

class OrderRequest(BaseModel):
    player_id: str
    product_code: str
    api_secret: str
    zone_id: str = None # اختياري (بس لموبايل ليجند)

@app.get("/")
def home():
    return {"status": "Online", "System": "Son of Utred Gateway 🚀"}

# --- 1. فحص الرصيد (للتجربة) ---
@app.get("/api/balance")
def check_balance(api_secret: str):
    if api_secret != MY_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # اتصال حقيقي بالمورد
        headers = {"X-API-Key": SUPPLIER_API_KEY}
        response = requests.get(f"{SUPPLIER_URL}/balance", headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# --- 2. تنفيذ الطلب (شراء حقيقي) ---
@app.post("/api/buy")
def process_order(order: OrderRequest):
    # أ. الحماية
    if order.api_secret != MY_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # ب. ترجمة المنتجات (من أسماء موقعك لأسماء المورد)
    # حسب التوثيق: game و pack
    products_map = {
        "PUBG_60":  {"game": "pubg", "pack": "60_uc"},
        "FF_100":   {"game": "freefire", "pack": "100_diamonds"},
        "ML_86":    {"game": "mobilelegend", "pack": "86"}, # بيحتاج zone_id
    }

    item = products_map.get(order.product_code)
    if not item:
        return {"success": False, "message": "Product code not found"}

    # ج. تجهيز الطلب للمورد
    payload = {
        "game": item["game"],
        "pack": item["pack"],
        "uid": order.player_id
    }
    
    # إذا اللعبة موبايل ليجند، لازم نضيف zone_id
    if item["game"] == "mobilelegend":
        if not order.zone_id:
            return {"success": False, "message": "Zone ID required for MLBB"}
        payload["zoneId"] = order.zone_id

    try:
        # د. إرسال الطلب للمورد (Son of Utred)
        headers = {
            "X-API-Key": SUPPLIER_API_KEY,
            "Content-Type": "application/json"
        }
        
        # ⚠️ تنبيه: هذا السطر سيخصم رصيد حقيقي!
        response = requests.post(
            f"{SUPPLIER_URL}/orders/game", 
            json=payload, 
            headers=headers
        )
        
        result = response.json()
        
        # تحليل رد المورد
        if result.get("success") == True:
            return {
                "success": True,
                "transaction_id": result["data"].get("orderId"), # رقم الطلب عند المورد
                "message": "Order Placed Successfully",
                "supplier_response": result
            }
        else:
            return {
                "success": False,
                "message": "Supplier Error",
                "details": result.get("error")
            }

    except Exception as e:
        return {"success": False, "message": f"Connection Error: {str(e)}"}
