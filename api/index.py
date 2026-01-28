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

    # استخراج البيانات
    token = data.get("token")
    numberId = str(data.get("numberId", "")).strip()
    note1 = str(data.get("note1", "")).strip()
    note2 = data.get("note2")       

    # التحقق من التوكن
    if token != MY_SECRET:
        return JSONResponse(content={
            "isSuccess": False,
            "operationId": "0", # ⛔ صفر يعني فشل
            "result": "Invalid Token",
            "value": 0
        })

    # 2. تجهيز الطلب للمورد
    products_map = {"257": {"game": "mobilelegend", "pack": "86"}}
    item = products_map.get(note1)
    
    # متغيرات النتيجة
    final_success = False
    final_message = "Error"
    final_op_id = "0" # الافتراضي صفر (فشل)

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

        # 3. التواصل الحقيقي مع المورد
        try:
            response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers, timeout=10)
            result_json = response.json()
            
            if result_json.get("success"):
                # ✅ حالة النجاح: بنولد رقم وبنرجع True
                final_success = True
                final_message = "تم تسجيل الطلب بنجاح"
                final_op_id = str(random.randint(10000000, 99999999)) # رقم العملية
            else:
                # ❌ حالة الفشل من المورد (رصيد، خطأ..)
                final_success = False
                final_message = result_json.get("error", "Supplier Error")
                final_op_id = "0" # بنرجع صفر عشان اللوحة تفهم إنه فشل
                
        except Exception as e:
            # ⛔ حالة الفشل بالاتصال (مثل حظر الآيبي)
            final_success = False
            final_message = "Connection Failed / IP Blocked"
            final_op_id = "0" # صفر يعني فشل
    else:
        final_message = "Product Not Found"
        final_op_id = "0"

    # 4. الرد النهائي
    return JSONResponse(content={
        "isSuccess": final_success,          # True أو False
        "operationId": final_op_id,          # رقم أو صفر
        "result": final_message,             # رسالة الخطأ
        "value": 0,
        "isDirectableToManual": False,
        "isRepeatableFailedBuy": True,
        "creditAfter": -1
    })
