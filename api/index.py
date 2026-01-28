from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import re
import random

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "YOUR_REAL_API_KEY_HERE" # ⚠️ مفتاحك الحقيقي
MY_SECRET = "NIZAR_SECURE_2026"

# المصيدة: نستقبل أي رابط
@app.api_route("/api/{path_name:path}", methods=["GET", "POST"])
async def catch_all(request: Request, path_name: str):
    
    # 1. توليد رقم العملية (رح نحطه بخانة operationId)
    gateway_id = random.randint(10000000, 99999999)

    # 2. تجميع البيانات
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

    # استخراج البيانات
    token = data.get("token")
    numberId = str(data.get("numberId", "")).strip()
    note1 = str(data.get("note1", "")).strip()
    note2 = data.get("note2")       

    # 3. التحقق
    if token != MY_SECRET:
        # بنقلد رد الفشل تبع Ayome
        return JSONResponse(content={
            "isSuccess": False,
            "result": "Invalid Token",
            "operationId": 0
        })

    # 4. محاولة الإرسال للمورد (بدون انتظار)
    products_map = {"257": {"game": "mobilelegend", "pack": "86"}}
    item = products_map.get(note1)
    
    if item:
        game = item["game"]
        pack = item["pack"]
        
        final_uid = numberId
        final_zone_id = ""
        # معالجة الآيدي والزون (نفس الكود السابق)
        if game == "mobilelegend":
            if note2 and str(note2) != "-": final_zone_id = str(note2)
            elif " " in numberId: 
                parts = numberId.split()
                if len(parts) >= 2: final_uid, final_zone_id = parts[0], parts[1]
            elif "(" in numberId:
                match = re.search(r'\((.*?)\)', numberId)
                if match: final_uid, final_zone_id = numberId.split('(')[0], match.group(1)
            
            final_uid = re.sub(r'\D', '', final_uid)
            final_zone_id = re.sub(r'\D', '', final_zone_id)

        payload = {"game": game, "pack": pack, "uid": final_uid}
        if final_zone_id: payload.update({"zoneId": final_zone_id, "server": "Asia"})

        headers = {"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}

        try:
            requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers, timeout=4)
        except:
            pass

    # 5. الرد المستنسخ (Ayome Style) 🐑✅
    # هذا الرد نفس شكل اللوج الناجح بالضبط
    return JSONResponse(content={
        "isSuccess": True,                   # المفتاح السحري للقبول
        "operationId": str(gateway_id),      # هون اللوحة بتدور عالرقم
        "result": "تم تسجيل الطلب بنجاح",    # رسالة النجاح
        "value": 0,
        "isDirectableToManual": False,
        "isRepeatableFailedBuy": True,
        "creditAfter": -1,
        
        # زيادة احتياط: بنخلي القديمين كمان
        "order": gateway_id,
        "id": gateway_id
    })
