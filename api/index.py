from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import asyncio
import time

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "j5OXE9NqqCa2JoUXotEQGWDum6lmvFgA" # ⚠️ مفتاحك الحقيقي
MY_SECRET = "NIZAR_SECURE_2026"

# 🔥 التوقيت الذهبي 🔥
# لوحتك بتفصل عالـ 100 ثانية
# البوت رح يفصل عالـ 85 ثانية عشان يلحق يسلمك الرد
MAX_WAIT_TIME = 85 

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

    # التحقق
    if data.get("token") != MY_SECRET:
        return response_ayome(False, None, "Invalid Token")

    # 2. تجهيز الطلب
    products_map = {"257": {"game": "mobilelegend", "pack": "86"}}
    item = products_map.get(str(data.get("note1", "")).strip())
    
    if not item: return response_ayome(False, None, "Product Not Found")

    game, pack = item["game"], item["pack"]
    numberId = str(data.get("numberId", "")).strip()
    
    # معالجة الآيدي
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
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers, timeout=30)
        result_json = response.json()
        
        if result_json.get("success"):
            # ✅ أخذنا رقم العملية الحقيقي
            real_order_id = str(result_json.get("id") or result_json.get("order"))
            
            # 🔥 4. الانتظار الذكي 🔥
            start_time = time.time()
            
            while (time.time() - start_time) < MAX_WAIT_TIME:
                
                # بنشيك كل 5 ثواني
                await asyncio.sleep(5)
                
                status_check = check_supplier_status(real_order_id)
                
                if status_check == "Canceled":
                    return response_ayome(False, None, "Failed by Supplier")
                
                elif status_check == "Completed":
                    return response_ayome(True, real_order_id, "Success")

            # ⚠️ 5. صفارة الحكم! خلص الوقت (85 ثانية)
            # المورد لسا ما خلص، بس نحنا لازم نرد عليك فوراً
            # بنقلك "نجاح مبدئي" وبنعطيك الرقم عشان تحفظه عندك باللوحة
            return response_ayome(True, real_order_id, "Processing (Saved)")
            
        else:
            return response_ayome(False, None, result_json.get("error", "Failed Immediately"))
            
    except Exception as e:
        return response_ayome(False, None, f"Error: {str(e)}")

# --- دالة فحص الحالة ---
def check_supplier_status(order_id):
    try:
        status_url = f"{SUPPLIER_URL.replace('/orders/game', '')}/orders/status"
        res = requests.post(
            status_url, 
            json={"order": order_id}, 
            headers={"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}, 
            timeout=5
        )
        data = res.json()
        status = ""
        if isinstance(data, dict):
            if "status" in data: status = data["status"]
            elif str(order_id) in data: status = data[str(order_id)].get("status")
            
        s = str(status).lower()
        if "cancel" in s or "fail" in s or "error" in s: return "Canceled"
        if "complet" in s or "success" in s: return "Completed"
    except: pass
    return "Pending"

# --- تنسيق الرد ---
def response_ayome(success, op_id, msg):
    return JSONResponse(status_code=200, content={
        "isSuccess": success,
        "operationId": op_id, 
        "result": msg,
        "value": 0,
        "isDirectableToManual": False,
        "isRepeatableFailedBuy": True,
        "creditAfter": -1
    })
