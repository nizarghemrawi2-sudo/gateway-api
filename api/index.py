from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random

app = FastAPI()

# 1. شكل البيانات اللي رح يستقبلها البوت من موقعك
class OrderRequest(BaseModel):
    player_id: str
    product_code: str  # الكود متل ما هو بموقعك
    api_secret: str    # كلمة السر للحماية

@app.get("/")
def home():
    return {"status": "Online", "System": "Gateway is Ready 🚀"}

@app.post("/api/process_order")
def process_order(order: OrderRequest):
    # 2. الحماية: التأكد من كلمة السر
    MY_SECRET = "NIZAR_SECURE_2026"  # هاي الكلمة اللي بتعطيها للمبرمج
    
    if order.api_secret != MY_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized: كلمة السر غلط")

    # 3. قاموس الترجمة (Mapping)
    # اليسار: اسم المنتج بموقعك | اليمين: اسم المنتج عند المورد
    product_map = {
        "PUBG_60": "pubg_mobile_60_uc_global",
        "PUBG_325": "pubg_mobile_325_uc_global",
        "FF_100": "free_fire_100_diamonds",
        # ضيف منتجاتك هون بنفس الطريقة
    }

    # البحث عن الاسم عند المورد
    supplier_code = product_map.get(order.product_code)

    if not supplier_code:
        return {
            "success": False, 
            "message": f"المنتج {order.product_code} غير معرف في القاموس"
        }

    # 4. (محاكاة) الرد بالنجاح
    # لاحقاً هون بنحط كود الاتصال بالمورد الحقيقي
    return {
        "success": True,
        "transaction_id": f"TRX-{random.randint(10000,99999)}",
        "message": "Order processed",
        "original_product": order.product_code,
        "supplier_product": supplier_code  # لنعرف شو طلبنا من المورد
    }