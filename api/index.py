from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests

app = FastAPI()

# --- إعدادات المورد ---
SUPPLIER_URL = "https://api.sonofutred.uk/api/v1"
SUPPLIER_API_KEY = "j5OXE9NqqCa2JoUXotEQGWDum6lmvFgA" # ⚠️ مفتاحك الحقيقي
MY_SECRET = "NIZAR_SECURE_2026"

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

    # فحص هل الطلب هو "فحص حالة" (Status Check)؟
    action = data.get("action")
    if action == "status" or "status" in path_name.lower():
        return check_status(data)

    # --- منطق الشراء السريع ---
    if data.get("token") != MY_SECRET:
        return response_ayome(False, None, "Invalid Token")

    # تجهيز الطلب
    products_map = {"257": {"game": "mobilelegend", "pack": "86"}}
    item = products_map.get(str(data.get("note1", "")).strip())
    
    if not item: return response_ayome(False, None, "Product Not Found")

    game, pack = item["game"], item["pack"]
    numberId = str(data.get("numberId", "")).strip()
    
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
        # إرسال للمورد (انتظار 30 ثانية فقط للاستجابة الأولية)
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers, timeout=30)
        result_json = response.json()
        
        if result_json.get("success"):
            # ✅ النجاح السريع
            # بناخد الرقم وبنرد عاللوحة فوراً "باي باي"
            real_order_id = str(result_json.get("id") or result_json.get("order"))
            return response_ayome(True, real_order_id, "Order Placed (Processing)")
        else:
            return response_ayome(False, None, result_json.get("error", "Failed Immediately"))
            
    except Exception as e:
        return response_ayome(False, None, f"Connection Error: {str(e)}")

# --- دالة فحص الحالة (اللوحة بتناديها كل دقيقة) ---
def check_status(data):
    order_id = data.get("order") or data.get("id")
    if not order_id: return JSONResponse({"status": "Error"})

    try:
        status_url = f"{SUPPLIER_URL.replace('/orders/game', '')}/orders/status"
        res = requests.post(
            status_url, 
            json={"order": order_id}, 
            headers={"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}, 
            timeout=10
        )
        data = res.json()
        
        status = "Pending"
        if isinstance(data, dict):
            if "status" in data: status = data["status"]
            elif str(order_id) in data: status = data[str(order_id)].get("status")
            
        s = str(status).lower()
        final_status = "Pending"
        if "cancel" in s or "fail" in s or "error" in s: final_status = "Canceled"
        elif "complet" in s or "success" in s or "done" in s: final_status = "Completed"
        
        return JSONResponse(content={
            "status": final_status,
            "charge": "0", "start_count": "0", "remains": "0", "currency": "USD"
        })
    except:
        return JSONResponse({"status": "Pending"})

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
