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

# 🔥 التوقيت: أقصى مدة انتظار قبل ما لوحتك تفصل (90 ثانية)
MAX_WAIT_TIME = 90 

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

    # معالجة فحص الحالة
    if data.get("action") == "status": return check_status(data)
    if data.get("token") != MY_SECRET: return response_ayome(False, None, "Invalid Token")

    products_map = {"257": {"game": "mobilelegend", "pack": "86"}}
    item = products_map.get(str(data.get("note1", "")).strip())
    if not item: return response_ayome(False, None, "Product Not Found")

    game, pack = item["game"], item["pack"]
    numberId = str(data.get("numberId", "")).strip()
    final_uid = "".join(filter(str.isdigit, numberId.split()[0] if " " in numberId else numberId))
    
    payload = {"game": game, "pack": pack, "uid": final_uid}
    headers = {"X-API-Key": SUPPLIER_API_KEY, "Content-Type": "application/json"}

    try:
        # 1. إرسال الطلب للمورد
        response = requests.post(f"{SUPPLIER_URL}/orders/game", json=payload, headers=headers, timeout=30)
        
        try:
            res_json = response.json()
        except:
            return response_ayome(False, None, f"Supplier Error (HTML/Block)")

        # هل المورد قبل الطلب؟ (حتى لو Processing)
        # ملاحظة: هون ما بنرد عاللوحة، بس بنحفظ الآيدي وبندخل بـ Loop
        is_accepted = res_json.get("success") or \
                      res_json.get("status") == "processing" or \
                      "process" in str(res_json.get("message", "")).lower()

        if is_accepted:
            real_order_id = str(res_json.get("id") or res_json.get("order"))
            
            # 👇👇👇 هون السر! لن نغلق الخط! 👇👇👇
            # بدل ما نرجع response فوراً، رح ندخل بحلقة انتظار إجبارية
            
            start_time = time.time()
            
            while (time.time() - start_time) < MAX_WAIT_TIME:
                
                # نام 5 ثواني (والخط لسا مفتوح غصب عنه)
                await asyncio.sleep(5)
                
                # اسأل المورد شو صار
                status = check_supplier_status(real_order_id)
                
                # إذا النتيجة صارت نهائية -> هلق بس بنسمح للبوت يسكر الخط
                if status == "Canceled":
                    return response_ayome(False, None, "Failed by Supplier")
                elif status == "Completed":
                    return response_ayome(True, real_order_id, "Success")
                
                # إذا لسا Processing -> ممنوع يسكر الخط، عيد اللفة...
            
            # ⚠️ إذا وصلنا لهون، يعني مرقت 90 ثانية والمورد لسا عم يشتغل
            # مضطرين نرد "نجاح" هلق عشان لوحتك ما تفصل وتعطي Error
            return response_ayome(True, real_order_id, "Processing (Saved)")

        else:
            return response_ayome(False, None, res_json.get("error", "Refused"))
            
    except Exception as e:
        return response_ayome(False, None, f"Error: {str(e)}")

# --- دوال مساعدة ---
def check_supplier_status(order_id):
    try:
        status_url = f"{SUPPLIER_URL.replace('/orders/game', '')}/orders/status"
        res = requests.post(status_url, json={"order": order_id}, headers={"X-API-Key": SUPPLIER_API_KEY}, timeout=10)
        data = res.json()
        
        st = ""
        if isinstance(data, dict):
            if "status" in data: st = data["status"]
            elif str(order_id) in data: st = data[str(order_id)].get("status")
            
        s = str(st).lower()
        if "cancel" in s or "fail" in s or "error" in s: return "Canceled"
        if "complet" in s or "success" in s: return "Completed"
    except: pass
    return "Pending"

def check_status(data): return JSONResponse({"status": "Pending"})

def response_ayome(success, op_id, msg):
    return JSONResponse(status_code=200, content={
        "isSuccess": success, "operationId": op_id, "result": msg, 
        "value": 0, "isDirectableToManual": False, "isRepeatableFailedBuy": True
    })

