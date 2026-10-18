from flask import Flask, request, jsonify, render_template, send_file, Response, stream_with_context
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import io
import time
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from zlapi import ZaloAPI
from zlapi.models import Message, ThreadType
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
app = Flask(__name__)

# ================= CẤU HÌNH TOÀN CỤC =================
ZALO_IMEI = "f52aff4f-3486-49b8-8108-df11cfb621e5-6c7753023a346715c58bb220997cb8f2"
ZALO_COOKIES = {"_ga_YT9TMXZYV9":"GS2.1.s1775112361$o1$g0$t1775112366$j55$l0$h0","_ga":"GA1.2.898049639.1775112362","_gid":"GA1.2.2087904641.1775112368","_gat":"1","_zlang":"vn","__zi":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8yscUwdaqPRY7kGwQFQHbsDVPZWeJ8s.1","__zi-legacy":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8yscUwdaqPRY7kGwQFQHbsDVPZWeJ8s.1","_ga_RYD7END4JE":"GS2.2.s1775112374$o1$g1$t1775112374$j60$l0$h0","_ga_YS1V643LGV":"GS2.1.s1775112374$o1$g0$t1775112375$j59$l0$h0","_ga_3EM8ZPYYN3":"GS2.2.s1775112377$o1$g0$t1775112377$j60$l0$h0","zpsid":"ZLfn.380341803.15.Mdy2BhgWv-gHBapyjg3dwi_JbTc2aDJUYvZNsRH8RvfL0_Xdkstt9DEWv-e","zpw_sek":"w2Df.380341803.a0.XHdvCl47h57QYGT7q0UiKOeboJhJFOu7lc3y7AD6ps6cC-f-cNt3PibsncUWEf5pZ0b4sO7e3qvy1c91FswiKG","app.event.zalo.me":"1697436733231772679"}
ZALO_CAMPAIGN_MAP = {
    "2602843309562232631": ["S"],                    
    "7954028088476649546": ["THE MATRIX ONE", "MỸ ĐÌNH PEARL", "GS", "SOLAR","SOLA"], 
    "8993819747961891064": ["SA", "VICTORIA", "GS", "CANOPY", "VIN GARDENIA","TC"], 
    "5067757448250152572": ["Masteri", "Canopy", "West point", "Sky lake", "Vin gardenia","Dcapital"], 
    "5570888047176402535": ["TK","IMPERIA","LUMIER EVER GREEN"] 
}
ZALO_DEFAULT_GROUP = "333333333333333"

GREEN_KEYWORDS = ["giá", "bao nhiêu", "mua", "bán", "liên hệ", "zalo", "nhắn", "gửi", "tư vấn", "số điện thoại", "sđt", "quan tâm", "xem căn", "có nhé", "ừ"]
RED_KEYWORDS = ["không", "bận", "nhầm", "sai số", "đừng gọi", "tắt", "chưa có nhu cầu", "nhầm máy"]

UCALL_TOKEN = ""

# ================= HỆ THỐNG REQUESTS =================
http_session = requests.Session()
retries = Retry(total=4, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
http_session.mount("https://", HTTPAdapter(max_retries=retries))

# ================= ZALO BOT =================
class ZaloBotApp(ZaloAPI):
    def __init__(self, imei, session_cookies):
        super().__init__('api_key', 'secret_key', imei=imei, session_cookies=session_cookies)

    def send_group_msg(self, group_id, text_content):
        try:
            msg = Message(text=text_content)
            self.send(msg, thread_id=str(group_id), thread_type=ThreadType.GROUP)
            return True, "Thành công"
        except Exception as e:
            return False, str(e)

try:
    zalo_bot = ZaloBotApp(ZALO_IMEI, ZALO_COOKIES)
    print("[*] Zalo Bot khởi tạo thành công.")
except Exception as e:
    zalo_bot = None
    print("[!] Lỗi Zalo Bot:", e)

# ================= CORE FUNCTIONS =================
def authenticate_ucall(email, password):
    global UCALL_TOKEN
    login_url = "https://admin.ucall.vn/api/signin"
    payload = {"username": email, "password": password}
    headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Mozilla/5.0", "Origin": "https://admin.ucall.vn", "Referer": "https://admin.ucall.vn/"}
    try:
        resp = http_session.post(login_url, json=payload, headers=headers, timeout=15, verify=False)
        if resp.status_code == 200:
            if token := resp.json().get('access'):
                UCALL_TOKEN = f"token {token}" if not token.startswith("token ") else token
                return True, "Xác thực Ucall thành công!"
        return False, f"Từ chối (Lỗi {resp.status_code})."
    except Exception as e:
        return False, str(e)

def fetch_campaigns_from_api():
    if not UCALL_TOKEN: return []
    campaigns, seen = [], set()
    headers = {'authorization': UCALL_TOKEN}
    for page in range(1, 10):
        try:
            resp = http_session.get(f'https://admin.ucall.vn/api/notification?page={page}', headers=headers, timeout=10, verify=False)
            results = resp.json().get('results', [])
            if not results: break
            for item in results:
                data_btn = str(item.get('data_button') or '') 
                if "call_campaign/" in data_btn:
                    camp_id = data_btn.split('/')[-1]
                    name = str(item.get('title') or '').replace("Chiến dịch Callbot: ", "").replace(" đã hoàn thành", "").replace(" đã bắt đầu chạy", "").replace("đã hoạt động lại", "").replace("Bạn đã được gán làm quản lý của chiến dịch Callbot", "").strip()
                    if camp_id not in seen and len(camp_id) > 10:
                        campaigns.append({'name': name, 'id': camp_id}); seen.add(camp_id)
        except: break
    return campaigns

def robust_extract_macan(attrs):
    if not isinstance(attrs, dict): return "N/A"
    u0, u1 = str(attrs.get('unnamed: 0', '')).strip(), str(attrs.get('unnamed: 1', '')).strip()
    if u0.isdigit() and u1 and any(c.isalpha() for c in u1): return u1.upper()
    if u0 and any(c.isalpha() for c in u0): return u0.upper()
    for key in ['custom_ma-can', 'ma_can', 'macan', 'Mã căn', 'căn hộ']:
        if val := attrs.get(key):
            s = str(val).strip().upper()
            if any(c.isalpha() for c in s) and not s.isdigit(): return s
    return "N/A"

def mark_customer_as_checked(campaign_id, customer_id):
    url = f'https://admin.ucall.vn/api/company/compa12039/call_campaign/{campaign_id}/customer_report/{customer_id}'
    headers = {'accept': 'application/json', 'authorization': UCALL_TOKEN, 'content-type': 'application/json'}
    try: http_session.put(url, headers=headers, json={'checked': True, 'is_view': True, 'is_read': True}, timeout=10, verify=False)
    except: pass

# ================= FLASK ROUTES =================
@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    success, msg = authenticate_ucall(data.get('email'), data.get('password'))
    return jsonify({"success": success, "message": msg})

@app.route('/api/campaigns', methods=['GET'])
def api_campaigns():
    return jsonify({"campaigns": fetch_campaigns_from_api()})

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    data = request.json
    start_page = int(data.get('page', 1))
    camp_id = data.get('campaign_id')
    want_checked = (data.get('checked', 'true') == 'true')
    
    url = f'https://admin.ucall.vn/api/company/compa12039/call_campaign/{camp_id}/customer_report/advance_filter'
    headers = {'authorization': UCALL_TOKEN, 'content-type': 'application/json'}
    
    # Ép Ucall lọc từ server, nếu hỗ trợ thì data sẽ chuẩn 100%
    json_data = {'filter_groups': {'object': 'callcampaigncustomer', 'filter_type': 'AND', 'groups': [{"filter_type": "AND", "filters": [{"field": "checked", "operator": "eq", "value": want_checked}]}]}}
    
    customers, total_records = [], 0
    try:
        # Chạy vòng lặp nhẹ để phòng trường hợp Ucall không lọc được trên server
        for p in range(start_page, start_page + 3):
            params = {'page': str(p), 'size': '10', 'quality': 'REPLY'}
            resp = http_session.post(url, params=params, headers=headers, json=json_data, timeout=20, verify=False)
            json_resp = resp.json()
            total_records = json_resp.get('count', 0)
            
            for r in json_resp.get('results', []):
                if bool(r.get('checked')) == want_checked:
                    thoai_cu, audio_url = "Không có lời thoại", r.get('record', '')
                    for val in r.get('call_results', {}).values():
                        if isinstance(val, dict) and 'text' in val:
                            thoai_cu, audio_url = val['text'].strip(), val.get('audio', audio_url)
                            break
                    t_low = thoai_cu.lower()
                    phan_loai = 'Có nhu cầu' if any(k in t_low for k in GREEN_KEYWORDS) else 'Không nhu cầu' if any(k in t_low for k in RED_KEYWORDS) else 'Chưa xác định'
                    customers.append({"ID": r.get('id', ''), "Mã": robust_extract_macan(r.get('other_attributes', {})), "SĐT": r.get('phone_number', 'N/A'), "Lời thoại cũ": thoai_cu, "Audio_URL": audio_url, "Phân loại": phan_loai})
            
            if len(customers) >= 10 or len(json_resp.get('results', [])) < 10: break
            
        customers = customers[:10]
        total_pages = (total_records + 9) // 10 if total_records > 0 else 1
        
        # Chỉ tích xanh khi đang xem "Chưa kiểm tra"
        if not want_checked and customers:
            def bg_task(clist):
                with ThreadPoolExecutor(max_workers=10) as ex:
                    for c in clist:
                        if c['ID']: ex.submit(mark_customer_as_checked, camp_id, c['ID'])
            threading.Thread(target=bg_task, args=(customers,), daemon=True).start()

        return jsonify({"success": True, "data": customers, "total_pages": total_pages, "total_records": total_records})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/send_zalo', methods=['POST'])
def api_send_zalo():
    if not zalo_bot: return jsonify({"success": False, "message": "Zalo Bot chưa được khởi tạo!"})
    data = request.json
    camp_name = data.get('camp_name', '')
    msg = f"{camp_name}\n{data.get('ma_can')}\n{data.get('sdt')}\n{data.get('phan_loai')}"
    target_group = ZALO_DEFAULT_GROUP
    for grp_id, keywords in ZALO_CAMPAIGN_MAP.items():
        if any(re.search(r'\b' + re.escape(kw.lower()) + r'\b', camp_name.lower()) for kw in keywords):
            target_group = grp_id; break
    success, err = zalo_bot.send_group_msg(target_group, msg)
    return jsonify({"success": success, "message": "Gửi thành công" if success else err})

@app.route('/api/export_excel', methods=['POST'])
def api_export_excel():
    data = request.json
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        if data.get('co_ma'): pd.DataFrame(data['co_ma']).to_excel(writer, sheet_name="Có Mã", index=False)
        if data.get('khong_ma'): pd.DataFrame(data['khong_ma']).to_excel(writer, sheet_name="Không Mã", index=False)
    output.seek(0)
    return send_file(output, download_name="bao_cao_ucall.xlsx", as_attachment=True)

@app.route('/api/play_audio', methods=['GET'])
def api_play_audio():
    audio_url = request.args.get('url')
    if not audio_url or audio_url == 'N/A': return "Không có file", 404
    try:
        resp = http_session.get(audio_url, stream=True, timeout=15, verify=False)
        def generate():
            for chunk in resp.iter_content(chunk_size=81920):
                if chunk: yield chunk
        return Response(stream_with_context(generate()), content_type=resp.headers.get('content-type', 'audio/mpeg'))
    except Exception as e: return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)