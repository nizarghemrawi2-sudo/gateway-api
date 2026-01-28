from fastapi import FastAPI, Request
import requests

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "j5OXE9NqqCa2JoUXotEQGWDum6lmvFgA" # ⚠️ مفتاحك الحقيقي
MY_SECRET = "NIZAR_SECURE_2026"

@app.get("/")
def home():
    return {"status": "Online", "System": "Gateway Universal V5 🚀"}

@app.post("/api/Buy")
@app.get("/api/Buy") # احتياطاً لو الموقع بعت GET
async def process_order(request: Request):
    
    # 1. تجميع البيانات من كل المصادر الممكنة (الجوكر) 🃏
    data = {}
    
    # أ. تجريب قراءة البيانات من الرابط (Query Params)
    data.update(request.query_params)
    
    # ب. تجريب قراءة البيانات من الفورم (Form Data)
    try:
        form = await request.form()
        data.update(form)
    except:
        pass
        
    # ج. تجريب قراءة البيانات كـ JSON
    try:
        json_body = await request.json()
        if isinstance(json_body, dict):
            data.update(json_body)
    except:
        pass

    # الآن البيانات صارت بمتغير اسمه data مهما كان مصدرها
    
    # 2. استخراج الحقول المطلوبة
    token = data.get("token")
    numberId = data.get("numberId")
    note1 = data.get("note1")
    note2 = data.get("note2")
    orderId_site = data.get("orderId")

    # 3. التحقق من التوكن
    if token != MY_SECRET:
        # طباعة المشكلة باللوج لمساعدتك
        return {
            "status": "error", 
            "message": "Invalid Token or Missing Data", 
            "debug_received": list(data.keys()) # بنرجعلك شو الحقول اللي وصلت عشان نتأكد
        }

    # 4. تحويل رقم المنتج (257) لطلب المورد
    products_map = {
        "257": {"game": "mobilelegend", "pack": "257"},         
        "258": {"game": "freefire", "pack": "100_diamonds"}, 
        "259": {"game": "mobilelegend", "pack": "86"}     
    }

    item = products_map.get(str(note1)) # حولنا لسترينغ احتياطاً
    
    if not item:
        return {"status": "error", "message": f"Product {note1} not found"}

    # 5. تجهيز الطلب
    payload = {
        "game": item["game"],
        "pack": item["pack"],
        "uid": numberId
    }
    
    if item["game"] == "mobilelegend":
        if not note2 or str(note2) == "-":
             return {"status": "error", "message": "Zone ID missing"}
        payload["zoneId"] = note2

    # 6. الشراء
    headers = {"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}
    
    try:
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers)
        result = response.json()

        if result.get("success"):
            return {
                "status": "completed", 
                "order_id": result["data"]["orderId"],
                "api_order_id": orderId_site
            }
        else:
            return {"status": "error", "message": result.get("error")}

    except Exception as e:
        return {"status": "error", "message": str(e)}

