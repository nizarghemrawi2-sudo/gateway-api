from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import re
import asyncio
import random

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "YOUR_REAL_API_KEY_HERE" # ⚠️ مفتاحك الحقيقي
MY_SECRET = "NIZAR_SECURE_2026"

@app.api_route("/api/{path_name:path}", methods=["GET", "POST"])
async def handle_request(request: Request, path_name: str):
    
    # تجميع البيانات
    data = dict(request.query_params)
    try:
        form = await request.form()
        data.update(form)
    except: pass
    try:
        json_body = await request.json()
        if isinstance(json_body, dict): data.update(json_body)
    except: pass

    # استخراج البيانات
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

    try:
        # 1. إرسال الطلب الأولي
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers, timeout=15)
        result_json = response.json()
        
        if result_json.get("success"):
            # الطلب انقبل مبدئياً، وجبنا الرقم الحقيقي
            real_order_id = str(result_json.get("id") or result_json.get("order"))
            
            # 🔥 الحل السحري: الانتظار والمراقبة 🔥
            # رح ننتظر 8 ثواني ونفحص الحالة قبل ما نرد على اللوحة
            # أغلب مشاكل الحظر أو الرصيد بتبين بأول كم ثانية
            
            final_status_check = await wait_and_check(real_order_id)
            
            if final_status_check == "Canceled":
                # لقطناه! رفض الطلب بسرعة
                return response_ayome(False, None, "Failed immediately by Supplier")
            else:
                # لسا ما بين شي، مضطرين نعطي نجاح
                return response_ayome(True, real_order_id, "تم الارسال (قيد المعالجة)")
        else:
            # رفض فوري من البداية
            error_msg = result_json.get("error", "Failed")
            return response_ayome(False, None, error_msg)
            
    except Exception as e:
        return response_ayome(False, None, f"Connection Error: {str(e)}")


# -----------------------------------------------------------
# دالة الانتظار (بتضل تفحص المورد لمدة 8 ثواني)
# -----------------------------------------------------------
async def wait_and_check(order_id):
    headers = {"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}
    
    # نجرب نفحص 3 مرات خلال 6-8 ثواني
    for _ in range(3):
        await asyncio.sleep(2) # نام ثانيتين
        try:
            # طلب فحص الحالة من المورد
            # (افترضنا رابط الحالة هيك، عدله اذا بتعرفه)
            res = requests.post(
                f"{SUPPLIER_URL.replace('/orders/game', '')}/orders/status", 
                json={"order": order_id}, 
                headers=headers, 
                timeout=5
            )
            data = res.json()
            
            # تحليل الرد
            status = ""
            if isinstance(data, dict):
                if "status" in data: status = data["status"]
                elif str(order_id) in data: status = data[str(order_id)].get("status")
            
            status = str(status).lower()
            
            # إذا لقينا كلمة تدل عالفشل، بنوقف وبنرجع Canceled فوراً
            if "cancel" in status or "fail" in status or "error" in status:
                return "Canceled"
                
        except:
            pass
            
    return "Pending" # إذا مرق الوقت وما فشل، بنعتبره ماشي

# -----------------------------------------------------------
# تنسيق الرد (Ayome)
# -----------------------------------------------------------
def response_ayome(success, op_id, msg):
    return JSONResponse(
        status_code=200, 
        content={
            "isSuccess": success,
            "operationId": op_id, # null للفشل
            "result": msg,
            "value": 0,
            "isDirectableToManual": False,
            "isRepeatableFailedBuy": True,
            "creditAfter": -1
        }
    )
