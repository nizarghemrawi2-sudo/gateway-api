from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import re
import random # لاستخدام التوليد العشوائي

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "j5OXE9NqqCa2JoUXotEQGWDum6lmvFgA" # ⚠️ مفتاحك الحقيقي
MY_SECRET = "NIZAR_SECURE_2026"

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

    # 2. البيانات
    token = data.get("token")
    numberId = str(data.get("numberId", "")).strip()
    note1 = str(data.get("note1", "")).strip()
    note2 = data.get("note2")       

    # التحقق
    if token != MY_SECRET:
        return {"error": "Invalid Token"}

    # 3. القاموس
    products_map = {
        "257": {"game": "mobilelegend", "pack": "86"},
        # ضيف باقي الألعاب هون
    }

    item = products_map.get(note1)
    if not item:
        return {"error": "Product not found"}

    game = item["game"]
    pack = item["pack"]

    # 4. معالجة الآيدي
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
            return {"error": "Zone ID Missing"}

    # 5. الإرسال للمورد
    payload = {"game": game, "pack": pack, "uid": final_uid}
    if game == "mobilelegend":
        payload["zoneId"] = final_zone_id
        payload["server"] = "Asia"

    headers = {"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}
    
    try:
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers)
        result = response.json()

        if result.get("success"):
            # ✅✅✅ هون التعديل الجذري ✅✅✅
            
            # 1. توليد رقم عملية خاص بالبوت (Gateway ID)
            # رقم عشوائي بين 10 مليون و 99 مليون (مستحيل يتكرر بالصدفة)
            gateway_order_id = random.randint(10000000, 99999999)
            
            # 2. الرد على اللوحة بهذا الرقم فقط
            # اللوحة رح تشوف رقم صحيح (Integer) ورح تنبسط وتخزنه
            return {
                "order": gateway_order_id, # أغلب اللوحات بتدور ع هي الكلمة
                "id": gateway_order_id,    # وهون احتياط
                "status": "success"
            }
        else:
            return {"error": result.get("error")}

    except Exception as e:
        return {"error": str(e)}
