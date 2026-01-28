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

# ---------------------------------------------------------
# 1. دالة الشراء (نفس اللي زبطت معك)
# ---------------------------------------------------------
@app.api_route("/api/{path_name:path}", methods=["GET", "POST"])
async def catch_all(request: Request, path_name: str):
    
    # تحديد نوع الطلب (هل هو فحص حالة؟)
    # بعض اللوحات بتبعت action=status للفحص
    params = dict(request.query_params)
    try:
        form = await request.form()
        params.update(form)
    except:
        pass
        
    # إذا الطلب هو "فحص حالة" (Status Check)
    if params.get("action") == "status" or "status" in path_name.lower():
        return await check_order_status(params)

    # --- منطق الشراء (Buy) ---
    gateway_id = random.randint(10000000, 99999999)
    
    token = params.get("token")
    numberId = str(params.get("numberId", "")).strip()
    note1 = str(params.get("note1", "")).strip()
    note2 = params.get("note2")       

    # التحقق
    if token != MY_SECRET:
        return JSONResponse(content={"isSuccess": False, "operationId": "0", "result": "Invalid Token"})

    # تجهيز الطلب
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
            # إرسال للمورد
            response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers, timeout=10)
            result_json = response.json()
            
            if result_json.get("success"):
                final_success = True
                final_message = "تم الارسال بنجاح"
                # بنحفظ رقم المورد الحقيقي في مكان ما لو أمكن، أو بنعتمد على رقمنا
                # للتبسيط رح نرجع رقم عشوائي ليقبله الموقع
                final_op_id = str(gateway_id) 
            else:
                final_success = False
                final_message = result_json.get("error", "Failed")
                final_op_id = "0"
                
        except:
            final_success = False
            final_message = "Connection Error"
            final_op_id = "0"
    else:
        final_message = "Product Not Found"

    return JSONResponse(content={
        "isSuccess": final_success,
        "operationId": final_op_id,
        "result": final_message,
        "value": 0,
        "isDirectableToManual": False,
        "isRepeatableFailedBuy": True
    })

# ---------------------------------------------------------
# 2. دالة فحص الحالة (الجديدة) 🔄
# ---------------------------------------------------------
async def check_order_status(params):
    # بنجيب الآيدي اللي اللوحة عم تسأل عنه
    order_id = params.get("order") or params.get("id")
    
    # ملاحظة: بما أننا ما عنا قاعدة بيانات، ما فينا نعرف رقم المورد الحقيقي من رقم البوت
    # فـ رح نفترض أن اللوحة بتبعت رقم المورد (إذا كانت حافظته)
    # أو رح نرد بحالة افتراضية للتجربة
    
    # ⚠️ هذا الجزء بيعتمد كيف بتفحص الحالة مع المورد
    # هل الرابط هو /orders/status ؟
    # لنفترض أننا عم نسأل المورد:
