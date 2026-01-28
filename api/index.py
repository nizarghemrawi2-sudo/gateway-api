from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import asyncio
import time

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "YOUR_REAL_API_KEY_HERE" # ⚠️ مفتاحك الحقيقي
MY_SECRET = "NIZAR_SECURE_2026"

# 🔥 إعدادات الانتظار (Vercel Pro) 🔥
# معنا 300 ثانية، رح نستخدم 260 ثانية (4 دقائق و 20 ثانية) لنكون بالسليم
MAX_WAIT_TIME = 260 

@app.api_route("/api/{path_name:path}", methods=["GET", "POST"])
async def handle_request(request: Request, path_name: str):
    
    # 1. تجميع البيانات
    data = dict(request.query_params)
    try:
        form = await request.form()
        data.update(form)
    except: pass
    try:
        json_body = await request.json()
        if isinstance(json_body, dict): data.update(json_body)
    except: pass

    # التحقق من التوكن
    if data.get("token") != MY_SECRET:
        return response_ayome(False, None, "Invalid Token")

    # 2. تجهيز الطلب
    products_map = {"257": {"game": "mobilelegend", "pack": "86"}}
    note1 = str(data.get("note1", "")).strip()
    item = products_map.get(note1)
    
    if not item: return response_ayome(False, None, "Product Not Found")

    game, pack = item["game"], item["pack"]
    numberId = str(data.get("numberId", "")).strip()
    
    # معالجة الآيدي والزون
    final_uid, final_zone_id = numberId, ""
    if game == "mobilelegend":
        if " " in numberId: final_uid, final_zone_id = numberId.split()[0], numberId.split()[1]
        elif "(" in numberId: final_uid = numberId.split('(')[0]
        final_uid = "".join(filter(str.isdigit, final_uid))
        final_zone_id = "".join(filter(str.isdigit, final_zone_id))

    payload = {"game": game, "pack": pack, "uid": final_uid}
    if final_zone_id: payload.update({"zoneId": final_zone_id, "server": "Asia"})

    headers = {"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}

    try:
        # 3. إرسال الطلب للمورد
        # زدنا وقت الانتظار لـ 30 ثانية للطلب الأول
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers, timeout=30)
        result_json = response.json()
        
        if result_json.get("success"):
            # ✅ أخذنا رقم العملية الحقيقي
            real_order_id = str(result_json.get("id") or result_json.get("order"))
            
            # 🔥 4. مرحلة الانتظار الطويل (The Waiting Game) 🔥
            start_time = time.time()
            
            while (time.time() - start_time) < MAX_WAIT_TIME:
                
                # ننتظر 5 ثواني بين كل فحص وفحص
                await asyncio.sleep(5)
                
                # نسأل المورد: شو صار؟
                status_check = check_supplier_status(real_order_id)
                
                if status_check == "Canceled":
                    # ❌ المورد رفض (بعد دقيقتين مثلاً) -> بنرجع فشل فوراً
                    return response_ayome(False, None, "Failed by Supplier (Rejected)")
                
                elif status_check == "Completed":
                    # ✅ المورد خلص -> بنرجع نجاح
                    return response_ayome(True, real_order_id, "Success (Completed)")
                
                # إذا لسا Pending.. بنكمل اللفة وبنضل ناطرين..

            # ⚠️ 5. إذا خلص الوقت (4 دقائق) والمورد لسا ما رد
            # بنرجع "نجاح" وبنسلم الرقم للوحة عشان نحفظ حقنا
            return response_ayome(True, real_order_id, "Processing (Took too long)")
            
        else:
            # رفض فوري من البداية
            return response_ayome(False, None, result_json.get("error", "Failed Immediately"))
            
    except Exception as e:
        return response_ayome(False, None, f"Error: {str(e)}")

# --- دالة فحص الحالة عند المورد ---
def check_supplier_status(order_id):
    try:
        # تأكد إن الرابط صح حسب توثيق المورد
        status_url = f"{SUPPLIER_URL.replace('/orders/game', '')}/orders/status"
        res = requests.post(
            status_url, 
            json={"order": order_id}, 
            headers={"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}, 
            timeout=10
        )
        data = res.json()
        
        status = ""
        if isinstance(data, dict):
            if "status" in data: status = data["status"]
            elif str(order_id) in data: status = data[str(order_id)].get("status")
            
        s = str(status).lower()
        if "cancel" in s or "fail" in s or "error" in s or "refund" in s: return "Canceled"
        if "complet" in s or "success" in s or "done" in s: return "Completed"
        
    except:
        pass
    return "Pending"

# --- تنسيق الرد ---
def response_ayome(success, op_id, msg):
    # إذا فشل بنرجع operationId: None عشان اللوحة تقلب حالة الطلب لـ Canceled/Error
    return JSONResponse(status_code=200, content={
        "isSuccess": success,
        "operationId": op_id, 
        "result": msg,
        "value": 0,
        "isDirectableToManual": False,
        "isRepeatableFailedBuy": True,
        "creditAfter": -1
    })
