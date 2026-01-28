from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import re
import random

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "j5OXE9NqqCa2JoUXotEQGWDum6lmvFgA" # ⚠️ مفتاحك الحقيقي
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

    # 2. التحقق من التوكن (التعديل هنا 👇)
    if token != MY_SECRET:
        # بنرجع كود 200 (نجاح اتصال) بس بنقول "فشل عملية"
        return JSONResponse(
            status_code=200, # ✅ ضروري جداً عشان اللوحة تقرأ الرد
            content={
                "isSuccess": False,          # ❌ فشل
                "operationId": "0",          # ⛔ صفر يعني ما في طلب
                "result": "خطأ في التوكن - Invalid Token", # سبب الرفض
                "value": 0,
                "isDirectableToManual": False,
                "isRepeatableFailedBuy": True,
                "creditAfter": -1
            }
        )

    # 3. تجهيز الطلب للمورد
    products_map = {"257": {"game": "mobilelegend", "pack": "86"}}
    item = products_map.get(note1)
    
    final_success = False
    final_message = "Error"
    final_op_id = "0"

    if item:
        game = item["game"]
        pack = item["pack"]
        
        final_uid = numberId
        final_zone_id = ""
        # (نفس كود المعالجة)
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
            # إرسال للمورد
            response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers, timeout=10)
            result_json = response.json()
            
            if result_json.get("success"):
                final_success = True
                final_message = "تم الارسال بنجاح"
                final_op_id = str(random.randint(10000000, 99999999)) 
            else:
                final_success = False
                final_message = result_json.get("error", "Failed")
                final_op_id = "0"
                
        except:
            final_success = False
            final_message = "Connection Error"
            final_op_id = "0"
    else:
        final_message = "Product Not Found (Check Gateway ID)"
        final_op_id = "0"

    # 4. الرد النهائي (دائماً 200)
    return JSONResponse(
        status_code=200, 
        content={
            "isSuccess": final_success,
            "operationId": final_op_id,
            "result": final_message,
            "value": 0,
            "isDirectableToManual": False,
            "isRepeatableFailedBuy": True,
            "creditAfter": -1
        }
    )

