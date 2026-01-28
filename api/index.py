from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import re
import json

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "j5OXE9NqqCa2JoUXotEQGWDum6lmvFgA" # ⚠️ مفتاحك الحقيقي
MY_SECRET = "NIZAR_SECURE_2026"

@app.api_route("/api/{path_name:path}", methods=["GET", "POST"])
async def handle_request(request: Request, path_name: str):
    
    # تجميع البيانات (Get + Post + JSON)
    data = dict(request.query_params)
    try:
        form = await request.form()
        data.update(form)
    except: pass
    try:
        json_body = await request.json()
        if isinstance(json_body, dict): data.update(json_body)
    except: pass

    # تحديد نوع العملية (شراء أم فحص حالة؟)
    action = data.get("action")
    
    # 1. إذا كان طلب فحص حالة (Status Check)
    if action == "status":
        return await check_status(data)
    
    # 2. إذا كان طلب شراء (Buy / Add)
    else:
        return await process_order(data)

# -----------------------------------------------------------
# دالة معالجة الطلب (Buy)
# -----------------------------------------------------------
async def process_order(data):
    token = data.get("token")
    numberId = str(data.get("numberId", "")).strip()
    note1 = str(data.get("note1", "")).strip()
    note2 = data.get("note2")       

    # التحقق من التوكن
    if token != MY_SECRET:
        return response_ayome(False, None, "Invalid Token")

    # تجهيز الطلب
    products_map = {"257": {"game": "mobilelegend", "pack": "86"}}
    item = products_map.get(note1)
    
    if not item:
        return response_ayome(False, None, "Product Not Found")

    game = item["game"]
    pack = item["pack"]
    
    # معالجة الآيدي
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

    try:
        # إرسال للمورد
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers, timeout=15)
        result_json = response.json()
        
        if result_json.get("success"):
            # ✅ أهم نقطة: بناخد رقم المورد الحقيقي
            # المورد غالباً بيرجع {"success": true, "id": 554433}
            real_order_id = str(result_json.get("id") or result_json.get("order"))
            return response_ayome(True, real_order_id, "تم الارسال بنجاح")
        else:
            # فشل فوري
            error_msg = result_json.get("error", "Failed")
            return response_ayome(False, None, error_msg)
            
    except Exception as e:
        return response_ayome(False, None, f"Connection Error: {str(e)}")

# -----------------------------------------------------------
# دالة فحص الحالة (Status Check)
# -----------------------------------------------------------
async def check_status(data):
    # اللوحة بتبعت الآيدي تبعنا اللي خزنته عندها
    order_id = data.get("order") or data.get("id")
    
    if not order_id:
        return JSONResponse(content={"status": "Error", "error": "Missing ID"})

    # بنسأل المورد عن هاد الرقم
    # ملاحظة: تأكد من رابط فحص الحالة عند موردك، غالباً هو /orders/status
    try:
        headers = {"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}
        payload = {"order": order_id} # بعض الموردين بدهم {"ids": "1,2"}
        
        # بنجرب نبعت طلب فحص للمورد
        # تنويه: هون لازم تكون عارف رابط الـ Status عند المورد بالضبط
        # رح افترض إنه هيك بناء على الرابط الأساسي
        res = requests.post(f"{SUPPLIER_URL.replace('/orders/game', '')}/orders/status", json=payload, headers=headers, timeout=10)
        
        # إذا الرابط غلط بنجرب الطريقة القياسية
        if res.status_code == 404:
             res = requests.post("https://api.sonofutred.uk/api/v1/orders/status", json={"ids": order_id}, headers=headers)

        res_json = res.json()
        
        # تحليل رد المورد وترجمته للوحتك
        # رد المورد المتوقع: {"status": "Canceled", ...} أو {"123": {"status": "Canceled"}}
        
        supplier_status = ""
        
        if isinstance(res_json, dict):
            # حالة 1: الرد مباشر
            if "status" in res_json:
                supplier_status = res_json["status"]
            # حالة 2: الرد قاموس آيديات
            elif order_id in res_json:
                supplier_status = res_json[order_id].get("status")
        
        # الترجمة (Mapping)
        final_status = "Pending" # الافتراضي
        s_lower = str(supplier_status).lower()
        
        if "cancel" in s_lower or "fail" in s_lower or "refund" in s_lower:
            final_status = "Canceled"
        elif "complet" in s_lower or "success" in s_lower or "done" in s_lower:
            final_status = "Completed"
        elif "process" in s_lower or "pend" in s_lower:
            final_status = "Pending"
            
        return JSONResponse(content={
            "status": final_status,
            "charge": "0",
            "start_count": "0", 
            "remains": "0",
            "currency": "USD"
        })

    except:
        # في حال الفشل بالفحص، بنقله لسا Pending
        return JSONResponse(content={"status": "Pending"})

# -----------------------------------------------------------
# دالة مساعدة لتنسيق الرد (Ayome Format)
# -----------------------------------------------------------
def response_ayome(success, op_id, msg):
    return JSONResponse(
        status_code=200, 
        content={
            "isSuccess": success,
            "operationId": op_id, # Null للفشل، رقم للنجاح
            "result": msg,
            "value": 0,
            "isDirectableToManual": False,
            "isRepeatableFailedBuy": True,
            "creditAfter": -1
        }
    )
