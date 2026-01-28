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
    return {"status": "Online", "System": "Gateway Final V8 🚀"}

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
    orderId_site = data.get("orderId")

    # 3. التحقق
    if token != MY_SECRET:
        return {"status": "error", "message": "Invalid Token"}

    # 4. القاموس
    products_map = {
        "257": {"game": "mobilelegend", "pack": "86"},
        # ضيف باقي الألعاب هون
    }

    item = products_map.get(note1)
    if not item:
        return {"status": "error", "message": f"Product {note1} not defined"}

    game = item["game"]
    pack = item["pack"]

    # 5. معالجة الآيدي والزون
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

    # 6. التجهيز والإرسال
    payload = {"game": game, "pack": pack, "uid": final_uid}
    if game == "mobilelegend":
        payload["zoneId"] = final_zone_id
        payload["server"] = "Asia"

    headers = {"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}
    
    try:
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers)
        result = response.json()

        if result.get("success"):
            supplier_id = result["data"]["orderId"]
            
            # 🔥 التعديل الناري: إرضاء جميع السكربتات 🔥
            return {
                "status": "success",    # بعض السكربتات بتكره كلمة processing
                "success": True,        # احتياط
                "order_id": supplier_id,
                "id": supplier_id,      # أغلب السكربتات بتدور على هي
                "order": supplier_id,   # وهاد كمان
                "trans_id": supplier_id,
                "api_order_id": orderId_site
            }
        else:
            return {"status": "error", "message": result.get("error")}

    except Exception as e:
        return {"status": "error", "message": str(e)}
