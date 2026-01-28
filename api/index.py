from fastapi import FastAPI, Request
import requests
import re
import random

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "j5OXE9NqqCa2JoUXotEQGWDum6lmvFgA" # ⚠️ مفتاحك الحقيقي
MY_SECRET = "NIZAR_SECURE_2026"

@app.get("/")
def home():
    return {"status": "Online", "System": "Gateway Integer Fix V9 🚀"}

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
    note1 = str(data.get("note1", "")).strip()
    note2 = data.get("note2")       
    orderId_site = data.get("orderId") # هذا رقم الطلب بموقعك (رقم صحيح)

    if token != MY_SECRET:
        return {"status": "error", "message": "Invalid Token"}

    # 3. القاموس
    products_map = {
        "257": {"game": "mobilelegend", "pack": "86"},
        # ضيف باقي الألعاب
    }

    item = products_map.get(note1)
    if not item:
        return {"status": "error", "message": f"Product {note1} not defined"}

    game = item["game"]
    pack = item["pack"]

    # 4. معالجة الآيدي والزون
    final_uid = numberId
    final_zone_id = ""

    if game == "mobilelegend":
        if note2 and str(note2) != "-" and str(note2).strip() != "":
            final_zone_id = str(note2)
        elif " " in numberId: 
            parts = numberId.split()
            if len(parts) >= 2:
                final_uid = parts[0]
                final_zone_id = parts[1]
        elif "(" in numberId:
            match = re.search(r'\((.*?)\)', numberId)
            if match:
                final_zone_id = match.group(1)
                final_uid = numberId.split('(')[0]
        
        final_uid = re.sub(r'\D', '', final_uid)
        final_zone_id = re.sub(r'\D', '', final_zone_id)

        if not final_zone_id:
            return {"status": "error", "message": "Zone ID Missing"}

    # 5. الإرسال
    payload = {"game": game, "pack": pack, "uid": final_uid}
    if game == "mobilelegend":
        payload["zoneId"] = final_zone_id
        payload["server"] = "Asia"

    headers = {"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}
    
    try:
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers)
        result = response.json()

        if result.get("success"):
            real_supplier_id = result["data"]["orderId"] # GO-xxxx
            fake_numeric_id = int(orderId_site) if orderId_site else random.randint(100000, 999999)

            # 👇 الرد الشامل لكل أنواع السكربتات
            return {
                # 1. الرد المباشر (للأنظمة البسيطة)
                "status": "success",
                "success": True,
                "error": 0,             # بعض الأنظمة بتشيك إذا الخطأ صفر
                "message": "Success",
                "id": fake_numeric_id,
                "order_id": fake_numeric_id,
                
                # 2. الرد المغلف بـ data (للأنظمة الحديثة) <-- غالباً موقعك بدو هي
                "data": {
                    "order_id": fake_numeric_id,
                    "id": fake_numeric_id,
                    "order": fake_numeric_id,
                    "status": "success",
                    "supplier_ref": real_supplier_id # عشان لو حب يخزنه
                },

                # 3. معلومات إضافية إلك
                "debug_real_id": real_supplier_id
            }
            }
        else:
            return {"status": "error", "message": result.get("error")}

    except Exception as e:
        return {"status": "error", "message": str(e)}

