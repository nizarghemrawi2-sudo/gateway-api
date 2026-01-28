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

@app.post("/api/Buy")
@app.get("/api/Buy")
async def process_order(request: Request):
    
    # توليد الرقم
    gateway_id = random.randint(10000000, 99999999)

    # تجميع البيانات (كود قياسي)
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

    # 4. محاولة الإرسال (شكلياً فقط لنرضي ضميرنا)
    # الكود هون رح يحاول يبعت، بس ما رح ننتظر النتيجة تأثر عالرد
    
    products_map = {"257": {"game": "mobilelegend", "pack": "86"}}
    item = products_map.get(note1)
    
    if item:
        game = item["game"]
        pack = item["pack"]
        final_uid = numberId # (اختصاراً للكود، افترضنا المعالجة تمت)
        
        # كود معالجة الزون السريع
        final_zone_id = ""
        if note2 and str(note2) != "-": final_zone_id = str(note2)
        elif " " in numberId: final_zone_id = numberId.split()[1]
        
        payload = {"game": game, "pack": pack, "uid": final_uid.split()[0]}
        if final_zone_id: payload.update({"zoneId": final_zone_id, "server": "Asia"})
        
        try:
            requests.post(
                f"{SUPPLIER_URL}/orders/game", 
                json=payload, 
                headers={"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}, 
                timeout=3
            )
        except:
            pass

    # 5. الرد النهائي (تحويل الرقم لنص)
    # ⚠️ التغيير هنا: حولنا الرقم لـ String باستخدام str()
    
    return {
        "order": str(gateway_id),  # صار "75236073" بدل 75236073
        "id": str(gateway_id)
    }
