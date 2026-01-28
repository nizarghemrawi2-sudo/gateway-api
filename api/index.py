from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import re
import random

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "j5OXE9NqqCa2JoUXotEQGWDum6lmvFgA" # ⚠️ حط مفتاحك
MY_SECRET = "NIZAR_SECURE_2026"

# ✅ هاد السطر بيستقبل أي رابط بتخترعه اللوحة (/buy, /Buy, /order...)
@app.api_route("/api/{path_name:path}", methods=["GET", "POST"])
async def catch_all(request: Request, path_name: str):
    
    # 1. توليد رقم العملية فوراً
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

    # 3. التحقق (شكلي)
    if token != MY_SECRET:
        # بنرجع رقم حتى لو التوكن غلط عشان اللوحة ما تعلق
        return JSONResponse(content={"order": gateway_id, "error": "Invalid Token"})

    # 4. محاولة الإرسال للمورد (بدون ما ننتظر النتيجة)
    products_map = {"257": {"game": "mobilelegend", "pack": "86"}}
    item = products_map.get(note1)
    
    if item:
        game = item["game"]
        pack = item["pack"]
        
        final_uid = numberId
        final_zone_id = ""
        # (نفس كود المعالجة السابق للموبايل ليجند)
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

    # 5. الرد الشامل (المهم)
    # حطينا الرقم كـ Int وكـ String وبكل الأسماء
    return JSONResponse(content={
        "status": "success",
        "order": gateway_id,       # للوحات اللي بدها رقم
        "id": gateway_id,          # للوحات اللي بدها id
        "order_id": gateway_id,    # للوحات القديمة
        "order_id_string": str(gateway_id) # احتياط
    })
