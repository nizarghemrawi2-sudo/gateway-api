import json
import time
import random
import string
import re
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BASE_URL = "https://api.umanageapp.uk/api/v1/external"

API_KEY = "pk_live_11ae8d782682b05262b790b562c4c7a0e18fb0b030a3299d" 
API_SECRET = "sk_live_1add57867178ac564018c1c7f9cf057ea304d4b139cbec320bca0c85f6c04651"

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY,
    "X-API-Secret": API_SECRET
}

STORE_ID = None
ORDERS_DB = {}


def get_store_id():
    global STORE_ID
    try:
        print("[*] Connecting to Provider...")
        res = requests.get(f"{BASE_URL}/stores", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get('success') and data.get('stores'):
                STORE_ID = data['stores'][0]['store_id']
                print(f"[+] Connected! Store ID: {STORE_ID}")
                return STORE_ID
        print(f"[!] Auth Failed.")
        return None
    except Exception as e:
        print(f"[!] Exception: {e}")
        return None


def generate_order_id():
    random_part = ''.join(random.choices(string.hexdigits.lower(), k=16))
    return f"ID_{random_part}"


# ============================================
# Response Builders - Play4Cards Format
# ============================================

def accept_response(order_id, message="Order completed successfully", price=0):
    return {
        "status": "OK",
        "data": {
            "order_id": str(order_id),
            "status": "accept",
            "price": price,
            "data": {},
            "replay_api": [{"replay": [message]}]
        }
    }


def reject_response(order_id, message="Order failed"):
    return {
        "status": "OK",
        "data": {
            "order_id": str(order_id),
            "status": "reject",
            "price": 0,
            "data": {},
            "replay_api": [{"replay": [message]}]
        }
    }


# ============================================
# Main Buy API
# ============================================
@app.route('/api/Buy', methods=['GET', 'POST'])
def buy_api():
    token_nizar = request.args.get('token')
    number_id = request.args.get('numberId')
    bundle_id = request.args.get('note1')

    my_order_id = generate_order_id()

    if token_nizar != "NIZAR_SECURE_2026":
        return jsonify(reject_response(my_order_id, "Security Error")), 200

    current_store_id = STORE_ID
    if not current_store_id:
        current_store_id = get_store_id()
    
    if not current_store_id:
        return jsonify(reject_response(my_order_id, "System Error")), 200

    raw_order_id = request.args.get('orderId', 'unknown')
    if '|' in str(raw_order_id):
        dashboard_order_id = str(raw_order_id).split('|')[0].strip()
    else:
        dashboard_order_id = str(raw_order_id)

    # تنظيف الرقم من أي حروف مخفية
    clean_number = re.sub(r'[^\d]', '', str(number_id))
    
    print(f"\n{'='*50}")
    print(f"[*] Original number: {repr(number_id)}")
    print(f"[*] Clean number: {clean_number}")
    print(f"[*] Bundle ID: {bundle_id}")
    print(f"[*] Dashboard Order ID: {dashboard_order_id}")

    payload = {
        "bundle_id": int(bundle_id),
        "secondary_number": clean_number,
        "app_user_reference": dashboard_order_id
    }

    try:
        res = requests.post(
            f"{BASE_URL}/stores/{current_store_id}/orders",
            headers=HEADERS,
            json=payload,
            timeout=15
        )

        data = res.json()
        print(f"[DEBUG] Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if not data.get('success'):
            error_msg = data.get('error', {}).get('message', 'Unknown error')
            print(f"[!] REJECT: {error_msg}")
            return jsonify(reject_response(my_order_id, error_msg)), 200

        order_data = data.get('order', {})
        provider_order_id = order_data.get('order_id')
        status = order_data.get('status')
        
        print(f"[*] Provider Order ID: {provider_order_id}, Status: {status}")

        # انتظار النتيجة
        for i in range(40):
            print(f"[*] Check {i+1}/40 - Status: {status}")
            
            if status == 'completed':
                print(f"[+] ACCEPT!")
                return jsonify(accept_response(my_order_id, "Order completed successfully")), 200
            
            if status == 'failed':
                reason = order_data.get('alfa_response')
                if isinstance(reason, dict):
                    reason = reason.get('message') or "Failed"
                reason = str(reason) if reason else "Unknown"
                
                if "Please enter an Alfa line number different than the one related to this account" in reason:
                    reason = "Error: Cannot recharge same number (Self-Recharge)"
                
                print(f"[!] REJECT: {reason}")
                return jsonify(reject_response(my_order_id, reason)), 200

            time.sleep(3)
            
            try:
                check_res = requests.get(
                    f"{BASE_URL}/stores/{current_store_id}/orders/{provider_order_id}", 
                    headers=HEADERS, 
                    timeout=10
                )
                if check_res.status_code == 200:
                    check_data = check_res.json()
                    order_data = check_data.get('order', {})
                    status = order_data.get('status')
            except Exception as e:
                print(f"[!] Check Error: {e}")

        # Timeout
        print("[!] TIMEOUT -> REJECT")
        return jsonify(reject_response(my_order_id, "Timeout")), 200

    except Exception as e:
        print(f"[!] EXCEPTION: {e}")
        return jsonify(reject_response(my_order_id, str(e))), 200


# ============================================
# Query API
# ============================================
@app.route('/api/Check', methods=['GET', 'POST'])
@app.route('/api/check', methods=['GET', 'POST'])
@app.route('/api/Query', methods=['GET', 'POST'])
def check_order():
    token = request.args.get('token')
    if token != "NIZAR_SECURE_2026":
        return jsonify(reject_response(generate_order_id(), "Security Error")), 200
    
    order_id = request.args.get('orderId') or request.args.get('order_id')
    
    if not order_id:
        return jsonify(reject_response(generate_order_id(), "Missing orderId")), 200
    
    if '|' in str(order_id):
        order_id = str(order_id).split('|')[0].strip()
    
    print(f"[*] Query: {order_id}")
    
    if order_id in ORDERS_DB:
        order = ORDERS_DB[order_id]
        if order['status'] == 'accept':
            return jsonify(accept_response(order['order_id'], "Success")), 200
        else:
            return jsonify(reject_response(order['order_id'], order['message'] or "Failed")), 200
    
    return jsonify(reject_response(generate_order_id(), "Order not found")), 200


@app.route('/api/health', methods=['GET'])
@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "OK", "store_id": STORE_ID}), 200


if __name__ == '__main__':
    print("="*50)
    print("  Play4Cards API")
    print("="*50)
    get_store_id()
    app.run(host='0.0.0.0', port=5050, debug=False)
