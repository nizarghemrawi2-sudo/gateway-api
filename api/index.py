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

@app.api_route("/api/{path_name:path}", methods=["GET", "POST"])
async def catch_all(request: Request, path_name: str):
    
    # 1. توليد رقم العملية
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

    token = data.get("token")
    numberId = str(data.get("numberId", "")).strip()
    note1 = str(data.get("note1", "")).strip()
    note2 = data.get("note2")       

    # التحقق من التوكن
    if token != MY_SECRET:
        return JSONResponse(content={
            "isSuccess": False,
            "operationId": str(gateway_id),
            "result": "Invalid Token",
            "value": 0
        })

    # 3. تجهيز الطلب
    products_map = {"257": {"game": "mobilelegend", "pack": "86"}}
    item = products_map.get(note1)
    
    # متغيرات النتيجة النهائية
    final_success = False
    final_message = "General Error"

    if item:
        game = item["game"]
        pack = item["pack"]
        
        # معالجة الآيدي والزون
        final_uid = numberId
        final_zone_id = ""
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

        # 4. محاولة الإرسال والحصول على النتيجة الحقيقية
        try:
            response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers, timeout=10)
            result_json = response.json()
            
            if result_json.get("success"):
                final_success = True
                final_message = "تم تسجيل الطلب بنجاح"
            else:
                final_success = False
                final_message = result_json.get("error", "Failed from Supplier")
                
        except Exception as e:
            # في حال الحظر أو فشل الاتصال
            final_success = False
            final_message = "Connection Failed / IP Blocked"
    else:
        final_message = "Product Not Found"

    # 5. الرد الذكي (Ayome Style)
    # بنرجع الحالة الحقيقية (نجاح أو فشل) بس مع المحافظة على الهيكلية عشان ما يطلع null
    return JSONResponse(content={
        "isSuccess": final_success,          # ✅ هون رح يطلع False إذا في حظر
        "operationId": str(gateway_id),      # ✅ الرقم موجود دائماً
        "result": final_message,             # ✅ رسالة الخطأ رح تظهر باللوحة
        "value": 0,
        "isDirectableToManual": False,
        "isRepeatableFailedBuy": True,
        "creditAfter": -1
    })
