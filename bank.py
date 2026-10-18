import os
import re
import time
import json
import queue
import random
import string
import hashlib
import logging
import threading
import traceback
import urllib.parse
from datetime import datetime

import requests
from flask import Flask, request, jsonify
from zlapi import ZaloAPI
from zlapi.models import Message, ThreadType

# ==========================================
# 0. LOG
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("bank")
logging.getLogger("werkzeug").setLevel(logging.WARNING)

# ==========================================
# 1. CẤU HÌNH TÀI KHOẢN NGÂN HÀNG (TECHCOMBANK)
# ==========================================
BANK_ID = "TCB"
ACCOUNT_NO = "19075062035014"
ACCOUNT_NAME = "NGUYEN DUC DUY TRUONG"

# ==========================================
# 2. CẤU HÌNH ZALO BOT & BẢO MẬT WEBHOOK
# ==========================================
IMEI = "aa98367f-255d-4304-8f2e-12c4d9a7d48d-925436884cc9a6b8005feb055c610baf"
SESSION_COOKIES = {
    "_ga_YT9TMXZYV9": "GS2.1.s1783138882$o2$g0$t1783138887$j55$l0$h0",
    "_ga": "GA1.2.898049639.1775112362",
    "__zi": "3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8Wxd-oYcKXQY76UwApSIbs6VfZkepCo.1",
    "__zi-legacy": "3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8Wxd-oYcKXQY76UwApSIbs6VfZkepCo.1",
    "_ga_RYD7END4JE": "GS2.2.s1776578868$o2$g1$t1776578869$j59$l0$h0",
    "_ga_YS1V643LGV": "GS2.1.s1789306579$o5$g0$t1789306580$j59$l0$h0",
    "_ga_3EM8ZPYYN3": "GS2.2.s1792313585$o8$g0$t1792313585$j60$l0$h0",
    "_zlang": "vn",
    "_gid": "GA1.2.137833363.1792313586",
    "_gat": "1",
    "zsid": "EXPIRED",
    "zpsid": "mQ5b.456166036.6.jpSKFjWYXMXCgBLpr2A5QArHzrpj5BHUxXAsNjaKaRaCrXFRsIaClB8YXMW",
    "zpw_sek": "-jJu.456166036.a0.zrK_dx96JPanCyZqXBduxzwRdOI7WzgtresrfvRgmPh2yvg1vDVAlkRDZ8VqXCNDsBZE-tHj37aMkFDcSTFuxm",
    "app.event.zalo.me": "2887145055420781720",
}

ADMIN_ZALO_ID = "3978113450181458224"   
WEBHOOK_SECRET = "truong_tcb_2026"       

ORDER_TTL = 30 * 60        
DEDUPE_WINDOW = 15         
SEND_RETRIES = 3

os.makedirs("cache", exist_ok=True)

def fmt_money(n: int) -> str:
    return "{:,.0f}".format(n).replace(",", ".")

# ==========================================
# 3. HỆ THỐNG SỔ TÀI CHÍNH (QUẢN LÝ THU CHI & NỢ)
# ==========================================
FINANCE_FILE = "cache/finance.json"
finance_lock = threading.Lock()

def load_finance():
    data = {"balance": 0, "debt": 0, "history": [], "debt_details": {}}
    if os.path.exists(FINANCE_FILE):
        try:
            with open(FINANCE_FILE, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                data.update(saved_data)
                if "debt_details" not in data:
                    data["debt_details"] = {}
        except:
            pass
    return data

def save_finance(data):
    try:
        with open(FINANCE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log.error(f"Lỗi lưu sổ tài chính: {e}")

finance_data = load_finance()

def add_transaction(txn_type, amount, reason, person=None):
    """Thêm giao dịch vào sổ: phân biệt doanh thu ngân hàng và chi tiêu ngoài"""
    global finance_data
    with finance_lock:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        
        if txn_type in ["thu", "doanh_thu"]:
            finance_data["balance"] += amount
        elif txn_type in ["chi", "chi_ngoai"]:
            finance_data["balance"] -= amount
        elif txn_type == "vay":
            finance_data["balance"] += amount
            finance_data["debt"] += amount
            if person:
                finance_data["debt_details"][person] = finance_data["debt_details"].get(person, 0) + amount
        elif txn_type == "tra":
            finance_data["balance"] -= amount
            finance_data["debt"] = max(0, finance_data["debt"] - amount)
            if person:
                finance_data["debt_details"][person] = finance_data["debt_details"].get(person, 0) - amount
                if finance_data["debt_details"][person] <= 0:
                    del finance_data["debt_details"][person]
            
        finance_data["history"].insert(0, {
            "type": txn_type,
            "amount": amount,
            "reason": reason,
            "date": date_str,
            "time": time_str
        })
        
        finance_data["history"] = finance_data["history"][:50]
        save_finance(finance_data)

def generate_finance_report():
    """Tạo báo cáo thống kê hiển thị Doanh thu và Chi tiêu ngoài"""
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    today_display = now.strftime("%d/%m/%Y")
    
    doanh_thu_ngay = 0
    chi_tieu_ngoai = 0
    
    history_lines = []
    with finance_lock:
        for tx in finance_data["history"]:
            if tx["date"] == today_str:
                if tx["type"] in ["thu", "doanh_thu", "vay"]:
                    doanh_thu_ngay += tx["amount"]
                elif tx["type"] in ["chi", "chi_ngoai", "tra"]:
                    chi_tieu_ngoai += tx["amount"]
                    
        for tx in finance_data["history"][:5]:
            icon = "🔺" if tx["type"] in ["thu", "doanh_thu", "vay"] else "🔻"
            action = tx["type"].upper()
            history_lines.append(f"{icon} {tx['time']}: {action} {fmt_money(tx['amount'])}đ ({tx['reason']})")
            
        debt_details_str = ""
        if finance_data.get("debt_details"):
            for person, debt_amt in finance_data["debt_details"].items():
                if debt_amt > 0:
                    debt_details_str += f"   👤 Nợ {person}: {fmt_money(debt_amt)} VNĐ\n"
                    
    history_str = "\n".join(history_lines) if history_lines else "Chưa có giao dịch nào."
    
    debt_section = f"💳 Tổng nợ: {fmt_money(finance_data['debt'])} VNĐ\n{debt_details_str}" if finance_data['debt'] > 0 else "💳 Đang nợ: 0 VNĐ\n"
    
    msg = (
        f"📊 BÁO CÁO TÀI CHÍNH ({today_display})\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💵 Quỹ hiện tại: {fmt_money(finance_data['balance'])} VNĐ\n"
        f"{debt_section}"
        f"┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n"
        f"📈 Doanh thu ngày: +{fmt_money(doanh_thu_ngay)} VNĐ\n"
        f"📉 Chi tiêu ngoài: -{fmt_money(chi_tieu_ngoai)} VNĐ\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📝 5 GIAO DỊCH GẦN NHẤT:\n"
        f"{history_str}"
    )
    return msg

def parse_money_command(text, prefix):
    content = text[len(prefix):].strip()
    parts = content.split(maxsplit=1)
    if not parts:
        return 0, ""
    
    raw_amt = parts[0].replace('k', '000').replace('K', '000').replace(',', '').replace('.', '')
    if not raw_amt.isdigit() or int(raw_amt) <= 0:
        return 0, ""
        
    amount = int(raw_amt)
    reason = parts[1] if len(parts) > 1 else "Không ghi chú"
    return amount, reason

def parse_debt_command(text, prefix):
    content = text[len(prefix):].strip()
    parts = content.split(maxsplit=2)
    if len(parts) < 2:
        return 0, "", ""
    
    raw_amt = parts[0].replace('k', '000').replace('K', '000').replace(',', '').replace('.', '')
    if not raw_amt.isdigit() or int(raw_amt) <= 0:
        return 0, "", ""
        
    amount = int(raw_amt)
    person = parts[1].capitalize() 
    reason = parts[2] if len(parts) > 2 else "Không ghi chú"
    return amount, person, reason

# ==========================================
# 4. TRẠNG THÁI WEBHOOK & ĐƠN HÀNG
# ==========================================
pending_orders = {}                 
orders_lock = threading.Lock()

recent_hashes = {}                  
recent_lock = threading.Lock()

last_chat = {"thread_id": None, "thread_type": None}
send_queue = queue.Queue()
bot_client = None

def admin_targets():
    targets = [(ADMIN_ZALO_ID, ThreadType.USER)]
    if last_chat["thread_id"] and last_chat["thread_id"] != ADMIN_ZALO_ID:
        targets.append((last_chat["thread_id"], last_chat["thread_type"]))
    return targets

def deliver(text: str, targets) -> bool:
    for thread_id, thread_type in targets:
        for attempt in range(1, SEND_RETRIES + 1):
            try:
                res = bot_client.send(
                    Message(text=text), thread_id=thread_id, thread_type=thread_type
                )
                return True
            except Exception as e:
                time.sleep(1.5 * attempt)
    return False

def sender_worker():
    while True:
        text, targets = send_queue.get()
        try:
            if bot_client is not None:
                deliver(text, targets)
        except Exception:
            pass
        finally:
            send_queue.task_done()

def enqueue(text: str, targets):
    send_queue.put((text, targets))


# ==========================================
# 5. CLASS BOT ZALO XỬ LÝ LỆNH
# ==========================================
class MoneyBot(ZaloAPI):
    def __init__(self, api_key, secret_key, imei, session_cookies):
        ZaloAPI.__init__(self, api_key, secret_key, imei=imei, session_cookies=session_cookies)

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        if not isinstance(message, str):
            return

        if str(author_id) == ADMIN_ZALO_ID or str(thread_id) == ADMIN_ZALO_ID:
            last_chat["thread_id"] = thread_id
            last_chat["thread_type"] = thread_type

        text = message.strip().lower()

        if text == "id":
            self.replyMessage(
                Message(text=f"📌 THÔNG TIN ID:\n- UID của bạn: {author_id}\n- Thread ID: {thread_id}"),
                message_object, thread_id, thread_type,
            )
            return

        # ======================================
        # CÁC LỆNH SỔ TÀI CHÍNH
        # ======================================
        if text == "tk" or text == "thongke":
            report_msg = generate_finance_report()
            self.replyMessage(Message(text=report_msg), message_object, thread_id, thread_type)
            return

        # Lệnh ghi nhận chi tiêu ngoài
        if text.startswith("chi "):
            amount, reason = parse_money_command(text, "chi ")
            if amount > 0:
                add_transaction("chi_ngoai", amount, reason)
                self.replyMessage(Message(text=f"✅ Đã ghi CHI TIÊU NGOÀI: -{fmt_money(amount)}đ ({reason})"), message_object, thread_id, thread_type)
            else:
                self.replyMessage(Message(text="⚠️ Sai cú pháp! Mẫu: chi 50k do xang"), message_object, thread_id, thread_type)
            return

        if text.startswith("thu "):
            amount, reason = parse_money_command(text, "thu ")
            if amount > 0:
                add_transaction("thu", amount, reason)
                self.replyMessage(Message(text=f"✅ Đã ghi THU: +{fmt_money(amount)}đ ({reason})"), message_object, thread_id, thread_type)
            else:
                self.replyMessage(Message(text="⚠️ Sai cú pháp! Mẫu: thu 100k luong"), message_object, thread_id, thread_type)
            return
            
        if text.startswith("vay "):
            amount, person, reason = parse_debt_command(text, "vay ")
            if amount > 0 and person:
                add_transaction("vay", amount, f"Vay {person}: {reason}", person)
                self.replyMessage(Message(text=f"✅ Đã ghi VAY: +{fmt_money(amount)}đ từ {person} ({reason}). Đã cộng vào Sổ Nợ."), message_object, thread_id, thread_type)
            else:
                self.replyMessage(Message(text="⚠️ Sai cú pháp! Mẫu: vay 500k Nam muon mua dt"), message_object, thread_id, thread_type)
            return

        if text.startswith("tra "):
            amount, person, reason = parse_debt_command(text, "tra ")
            if amount > 0 and person:
                add_transaction("tra", amount, f"Trả {person}: {reason}", person)
                self.replyMessage(Message(text=f"✅ Đã ghi TRẢ NỢ: -{fmt_money(amount)}đ cho {person} ({reason}). Đã trừ Sổ Nợ."), message_object, thread_id, thread_type)
            else:
                self.replyMessage(Message(text="⚠️ Sai cú pháp! Mẫu: tra 200k Nam tra bot tien"), message_object, thread_id, thread_type)
            return

        # ======================================
        # LỆNH TẠO MÃ QR THU TIỀN
        # ======================================
        if text.startswith(("qr ", "/qr ")):
            self.handle_qr(message.strip(), message_object, thread_id, thread_type)

    def handle_qr(self, raw_text, message_object, thread_id, thread_type):
        parts = raw_text.split(maxsplit=2)
        if len(parts) < 2:
            self.replyMessage(Message(text="⚠️ Sai cú pháp! Mẫu: qr 50000"), message_object, thread_id, thread_type)
            return

        raw_amount = parts[1].lower().replace("k", "000").replace(",", "").replace(".", "")
        if not raw_amount.isdigit() or int(raw_amount) <= 0:
            self.replyMessage(Message(text="⚠️ Số tiền không hợp lệ!"), message_object, thread_id, thread_type)
            return

        amount = int(raw_amount)

        with orders_lock:
            while True:
                trans_code = "TT" + "".join(random.choices(string.digits, k=4))
                if trans_code not in pending_orders:
                    break

        extra_note = parts[2] if len(parts) > 2 else ""
        transfer_content = f"Thanh toan bee {trans_code} {extra_note}".strip()

        qr_url = (
            f"https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NO}-compact2.png"
            f"?amount={amount}"
            f"&addInfo={urllib.parse.quote(transfer_content)}"
            f"&accountName={urllib.parse.quote(ACCOUNT_NAME)}"
        )

        qr_path = f"cache/qr_{trans_code}.png"
        try:
            resp = requests.get(qr_url, timeout=15)
            resp.raise_for_status()
            with open(qr_path, "wb") as f:
                f.write(resp.content)

            with orders_lock:
                pending_orders[trans_code] = {
                    "amount": amount,
                    "content": transfer_content,
                    "thread_id": thread_id,
                    "thread_type": thread_type,
                    "created_at": time.time(),
                }

            caption = (
                f"💳 MÃ QR CHUYỂN KHOẢN\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🏦 Ngân hàng: Techcombank\n"
                f"👤 Chủ TK: {ACCOUNT_NAME}\n"
                f"🔢 STK: {ACCOUNT_NO}\n"
                f"💰 Số tiền: {fmt_money(amount)} VNĐ\n"
                f"📝 Nội dung (Bắt buộc): {transfer_content}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"⏳ Đang chờ nhận tiền... Hệ thống sẽ tự động báo ngay khi tiền vào!"
            )
            self.sendLocalImage(
                qr_path,
                thread_id=thread_id,
                thread_type=thread_type,
                message=Message(text=caption),
                width=600,
                height=750,
            )
        except Exception as e:
            self.replyMessage(Message(text=f"❌ Lỗi khi tạo mã QR: {e}"), message_object, thread_id, thread_type)
        finally:
            if os.path.exists(qr_path):
                try:
                    os.remove(qr_path)
                except OSError:
                    pass


# ==========================================
# 6. PHÂN TÍCH THÔNG BÁO TECHCOMBANK
# ==========================================
def parse_tcb_notification(title: str, content: str):
    full_text = f"{title} | {content}".strip(" |")

    credit = re.search(r"(?:\+\s*(?:VND|VNĐ)?\s*([\d\.,]+))|(?:(?:VND|VNĐ)\s*([\d\.,]+))", full_text, re.IGNORECASE)
    debit = re.search(r"-\s*(?:VND|VNĐ)?\s*([\d\.,]+)", full_text, re.IGNORECASE)

    direction, amount = "in", 0 
    
    if credit:
        raw_val = credit.group(1) or credit.group(2)
        if raw_val:
            amount = int(re.sub(r"[^\d]", "", raw_val) or 0)
    elif debit:
        direction = "out"
        amount = int(re.sub(r"[^\d]", "", debit.group(1)) or 0)
    else:
        all_nums = re.findall(r'[\d\.,]+', title)
        if all_nums:
            raw_num = re.sub(r'[^\d]', '', all_nums[0])
            if raw_num.isdigit():
                amount = int(raw_num)

    balance = "Không rõ"
    balance_int = None
    bal = re.search(r"Số dư[:\s]*(?:VND|VNĐ)?\s*([\d\.,]*)", full_text, re.IGNORECASE)
    if bal:
        digits = re.sub(r"[^\d]", "", bal.group(1))
        if digits:
            balance_int = int(digits)
            balance = fmt_money(balance_int)

    code = None
    m = re.search(r"(TT\d{4})", full_text, re.IGNORECASE)
    if m:
        code = m.group(1).upper()

    return {
        "direction": direction,
        "amount": amount,
        "balance": balance,
        "balance_int": balance_int,
        "code": code,
        "full_text": full_text,
    }

def is_duplicate(title: str, content: str) -> bool:
    key = hashlib.md5(f"{title}|{content}".encode("utf-8")).hexdigest()
    now = time.time()
    with recent_lock:
        for k in [k for k, t in recent_hashes.items() if now - t > DEDUPE_WINDOW]:
            recent_hashes.pop(k, None)
        if key in recent_hashes:
            return True
        recent_hashes[key] = now
    return False

def purge_expired_orders():
    now = time.time()
    with orders_lock:
        expired = [c for c, o in pending_orders.items() if now - o["created_at"] > ORDER_TTL]
        for c in expired:
            pending_orders.pop(c, None)


# ==========================================
# 7. SERVER FLASK NHẬN BIẾN ĐỘNG TỪ ANDROID
# ==========================================
app = Flask(__name__)

def parse_body() -> dict:
    raw = request.get_data(as_text=True) or ""
    try:
        data = json.loads(raw, strict=False)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    data = {}
    m = re.search(r'"secret"\s*:\s*"(.*?)"\s*[,}]', raw, re.S)
    if m:
        data["secret"] = m.group(1)
    m = re.search(r'"title"\s*:\s*"(.*?)"\s*,', raw, re.S)
    if m:
        data["title"] = m.group(1)
    m = re.search(r'"content"\s*:\s*"(.*?)"\s*\}\s*$', raw, re.S)
    if m:
        data["content"] = m.group(1)
    return data

@app.route("/webhook/bank", methods=["POST"])
def receive_bank_notification():
    try:
        data = parse_body()
        if data.get("secret") != WEBHOOK_SECRET:
            return jsonify({"status": "unauthorized"}), 401

        title = str(data.get("title", ""))
        content = str(data.get("content", ""))

        if is_duplicate(title, content):
            return jsonify({"status": "duplicate"}), 200

        if bot_client is None:
            return jsonify({"status": "bot_not_ready"}), 503

        purge_expired_orders()
        info = parse_tcb_notification(title, content)
        amount = info["amount"]
        
        # === TỰ ĐỘNG GHI SỔ DOANH THU KHI NHẬN TIỀN ===
        if amount > 0 and info["direction"] == "in":
            add_transaction("doanh_thu", amount, f"Ngân hàng TCB: {info['code'] if info['code'] else 'Ngoài luồng'}")

        display_amount = amount if amount > 0 else 2000
        formatted_received = "{:,.0f}".format(display_amount).replace(",", ".")
        matched_code = None

        if info["code"] and info["code"] in pending_orders:
            matched_code = info["code"]
        else:
            for code, order in list(pending_orders.items()):
                if code.lower() in info["full_text"].lower():
                    matched_code = code
                    break

        if matched_code and bot_client:
            order = pending_orders.pop(matched_code)
            expected_amount = order["amount"]
            formatted_expected = "{:,.0f}".format(expected_amount).replace(",", ".")

            if display_amount >= expected_amount:
                msg = (
                    f"✅ ĐÃ NHẬN TIỀN THÀNH CÔNG!\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔑 Mã đơn: {matched_code}\n"
                    f"💰 Số tiền nhận: +{formatted_received} VNĐ\n"
                    f"💳 Biến động Techcombank: {info['balance']} VNĐ\n"
                    f"🕒 Trạng thái: Đã thanh toán đủ"
                )
            else:
                thieu = "{:,.0f}".format(expected_amount - display_amount).replace(",", ".")
                msg = (
                    f"⚠️ ĐÃ NHẬN NHƯNG CHƯA ĐỦ TIỀN!\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔑 Mã đơn: {matched_code}\n"
                    f"💰 Đã nhận: +{formatted_received} / {formatted_expected} VNĐ\n"
                    f"💳 Biến động Techcombank: {info['balance']} VNĐ\n"
                    f"❗ Còn thiếu: {thieu} VNĐ"
                )

            targets = [(order["thread_id"], order["thread_type"])] + admin_targets()
            enqueue(msg, targets)
        else:
            msg = (
                f"🔔 BIẾN ĐỘNG SỐ DƯ TECHCOMBANK\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💰 Số tiền: +{formatted_received} VNĐ\n"
                f"💳 Số dư hiện tại: {info['balance']} VNĐ\n"
                f"📄 Chi tiết: {info['full_text']}"
            )
            enqueue(msg, admin_targets())

        return jsonify({"status": "success", "matched": matched_code}), 200

    except Exception as e:
        log.error("WEBHOOK ERROR:\n%s", traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

def start_webhook_server():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

# ==========================================
# 8. KHỞI CHẠY HỆ THỐNG
# ==========================================
if __name__ == "__main__":
    bot_client = MoneyBot("</>", "</>", imei=IMEI, session_cookies=SESSION_COOKIES)

    threading.Thread(target=sender_worker, daemon=True).start()
    threading.Thread(target=start_webhook_server, daemon=True).start()

    log.info("✅ Bot Quản Lý Tài Chính & Ngân Hàng đã chạy!")

    # Vòng lặp tự động kết nối lại khi rớt mạng
    while True:
        try:
            bot_client.listen()
        except Exception as e:
            log.error(f"⚠️ Rớt mạng hoặc Zalo ngắt kết nối: {e}")
            log.info("⏳ Tự động khởi động lại bot sau 5 giây...")
            time.sleep(5)