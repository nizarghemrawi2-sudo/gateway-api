from fastapi import FastAPI, Request
import requests
import re

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "j5OXE9NqqCa2JoUXotEQGWDum6lmvFgA" # ⚠️ مفتاحك الحقيقي
MY_SECRET = "NIZAR_SECURE_2026"

@app.get("/")
def home():
    return {"status": "Online", "System": "MLBB Gateway V6 🚀"}

@app.post("/api/Buy")
@app.get("/api/Buy")
async def process_order(request: Request):
    
    # 1. تجميع البيانات
    data = {}
    data.update(request.query_params)
    try:
        form = await request.form()
        data.update(form)
    except:
        pass
    try:
        json_body = await request.json()
        if isinstance(json_body, dict):
            data.update(json_body)
    except:
        pass

    # 2. استخراج البيانات
    token = data.get("token")
    numberId = str(data.get("numberId", "")).strip() # تنظيف المسافات الزائدة
    note1 = data.get("note1")       
    note2 = data.get("note2")       
    orderId_site = data.get("orderId")

    # 3. التحقق من التوكن
    if token != MY_SECRET:
        return {"status": "error", "message": "Invalid Token"}

    # 4. تحديد المنتج
    if str(note1) == "257": 
        game = "mobilelegend"
        pack = "257"
    else:
        return {"status": "error", "message": f"Product {note1} not defined"}

    # 5. --- الذكاء في استخراج الزون (Zone ID) --- 🧠
    final_uid = numberId
    final_zone_id = ""

    # المحاولة 1: الزون موجود في note2
    if note2 and str(note2) != "-" and str(note2).strip() != "":
        final_zone_id = str(note2)
    
    # المحاولة 2: الزون مفصول بمسافة (1234567 1234) <-- حالتك أنت
    elif " " in numberId:
        parts = numberId.split()
        if len(parts) >= 2:
            final_uid = parts[0]
            final_zone_id = parts[1] # الرقم الثاني هو الزون

    # المحاولة 3: الزون بين أقواس (1234567(1234))
    elif "(" in numberId and ")" in numberId:
        match = re.search(r'\((.*?)\)', numberId)
        if match:
            final_zone_id = match.group(1)
            final_uid = numberId.split('(')[0]

    # تنظيف الأرقام من أي رموز غريبة
    final_uid = re.sub(r'\D', '', final_uid) # خذ الأرقام فقط
    final_zone_id = re.sub(r'\D', '', final_zone_id) # خذ الأرقام فقط

    # فحص أخير
    if not final_zone_id:
        return {
            "status": "error", 
            "message": "Zone ID missing. Please allow space between ID and Zone (e.g., 123456 1234)"
        }

    # 6. الإرسال للمورد
    payload = {
        "game": game,
        "pack": pack,
        "uid": final_uid,
        "zoneId": final_zone_id,
        "server": "Asia"
    }

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
            # رسالة خطأ واضحة لك
            return {
                "status": "error", 
                "message": result.get("error"), 
                "sent_data": {"uid": final_uid, "zone": final_zone_id} # عشان تشوف شو انبعث
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}

