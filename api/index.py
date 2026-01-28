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
    return {"status": "Online", "System": "Universal Gateway V7 🚀"}

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
    numberId = str(data.get("numberId", "")).strip()
    note1 = str(data.get("note1", "")).strip() # رقم المنتج
    note2 = data.get("note2")       
    orderId_site = data.get("orderId")

    # 3. التحقق من التوكن
    if token != MY_SECRET:
        return {"status": "error", "message": "Invalid Token"}

    # 4. --- القاموس الشامل (مهم جداً تعبيه) --- 📝
    products_map = {
        # موبايل ليجند
        "257": {"game": "mobilelegend", "pack": "86"},
        
        # ببجي (أمثلة - عدل الأرقام حسب موقعك)
        "1001": {"game": "pubg", "pack": "60_uc"},
        "1002": {"game": "pubg", "pack": "325_uc"},
        
        # فري فاير
        "2001": {"game": "freefire", "pack": "100_diamonds"},
    }

    item = products_map.get(note1)
    
    if not item:
        # هذا الخطأ هو سبب الـ 0-null (المنتج غير موجود)
        return {"status": "error", "message": f"Product ID {note1} is not defined in Gateway"}

    game = item["game"]
    pack = item["pack"]

    # 5. معالجة الآيدي والزون
    final_uid = numberId
    final_zone_id = ""

    # منطق خاص لـ Mobile Legends فقط
    if game == "mobilelegend":
        if note2 and str(note2) != "-" and str(note2).strip() != "":
            final_zone_id = str(note2)
        elif " " in numberId: # فصل المسافة
            parts = numberId.split()
            if len(parts) >= 2:
                final_uid = parts[0]
                final_zone_id = parts[1]
        elif "(" in numberId: # فصل الأقواس
            match = re.search(r'\((.*?)\)', numberId)
            if match:
                final_zone_id = match.group(1)
                final_uid = numberId.split('(')[0]
        
        # تنظيف الأرقام
        final_uid = re.sub(r'\D', '', final_uid)
        final_zone_id = re.sub(r'\D', '', final_zone_id)

        if not final_zone_id:
            return {"status": "error", "message": "Zone ID Missing for MLBB"}

    # 6. تجهيز البايلود حسب اللعبة
    payload = {
        "game": game,
        "pack": pack,
        "uid": final_uid
    }
    
    # إضافة الزون والسيرفر فقط إذا اللعبة موبايل ليجند
    if game == "mobilelegend":
        payload["zoneId"] = final_zone_id
        payload["server"] = "Asia"

    # 7. الإرسال
    headers = {"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}
    
    try:
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers)
        result = response.json()

        if result.get("success"):
            return {
                "status": "processing",
                "order_id": result["data"]["orderId"], # الرقم اللي بينتظره موقعك
                "api_order_id": orderId_site
            }
        else:
            return {"status": "error", "message": result.get("error")}

    except Exception as e:
        return {"status": "error", "message": str(e)}
