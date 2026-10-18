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
logging.getLogger("werkzeug").setLevel(logging.WARNING)  # bớt ồn log Flask

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

# Danh sách UID nhận thông báo biến động số dư (thêm bao nhiêu cũng được)
ADMIN_ZALO_IDS = [
    "3978113450181458224",
    "4153887186312882080",
]
WEBHOOK_SECRET = "truong_tcb_2026"       # khớp với MacroDroid

ORDER_TTL = 30 * 60        # đơn QR hết hạn sau 30 phút
DEDUPE_WINDOW = 15         # chống MacroDroid bắn trùng thông báo (giây)
SEND_RETRIES = 3

os.makedirs("cache", exist_ok=True)

# ==========================================
# 3. TRẠNG THÁI DÙNG CHUNG
# ==========================================
pending_orders = {}                 # mã TTxxxx -> thông tin đơn
orders_lock = threading.Lock()

recent_hashes = {}                  # chống xử lý trùng
recent_lock = threading.Lock()

# Khung chat gần nhất từng nhắn cho bot (chắc chắn gửi lại được)
last_chat = {"thread_id": None, "thread_type": None}

send_queue = queue.Queue()
bot_client = None


def fmt_money(n: int) -> str:
    return "{:,.0f}".format(n).replace(",", ".")


# ==========================================
# 4. GỬI TIN ZALO (HÀNG ĐỢI + THỬ LẠI + DỰ PHÒNG)
# ==========================================
def admin_targets():
    """Danh sách nơi báo cho admin, thử lần lượt tới khi thành công."""
    return [(uid, ThreadType.USER) for uid in ADMIN_ZALO_IDS]


def enqueue_admin(text: str):
    """Gửi cho TỪNG admin (mỗi người một tin, lỗi người này không ảnh hưởng người kia)."""
    for uid in ADMIN_ZALO_IDS:
        send_queue.put((text, [(uid, ThreadType.USER)]))


def deliver(text: str, targets) -> bool:
    for thread_id, thread_type in targets:
        for attempt in range(1, SEND_RETRIES + 1):
            try:
                res = bot_client.send(
                    Message(text=text), thread_id=thread_id, thread_type=thread_type
                )
                log.info("Đã gửi Zalo -> %s (%s) | kết quả: %s", thread_id, thread_type, res)
                return True
            except Exception as e:
                log.error(
                    "Gửi Zalo THẤT BẠI -> %s lần %d/%d: %s",
                    thread_id, attempt, SEND_RETRIES, e,
                )
                log.debug(traceback.format_exc())
                time.sleep(1.5 * attempt)
        log.warning("Bỏ qua đích %s, thử đích dự phòng (nếu có)...", thread_id)
    log.error("KHÔNG gửi được tin nào. Nội dung chưa gửi:\n%s", text)
    return False


def sender_worker():
    while True:
        text, targets = send_queue.get()
        try:
            if bot_client is None:
                log.error("bot_client chưa sẵn sàng, bỏ tin.")
            else:
                deliver(text, targets)
        except Exception:
            log.error("Lỗi worker gửi tin:\n%s", traceback.format_exc())
        finally:
            send_queue.task_done()


def enqueue(text: str, targets):
    send_queue.put((text, targets))


# ==========================================
# 5. CLASS BOT ZALO XỬ LÝ LỆNH
# ==========================================
class MoneyBot(ZaloAPI):
    # Thêm =None vào session_cookies để nó không bị bắt buộc truyền vào lúc gọi
    def __init__(self, api_key, secret_key, imei, session_cookies=None):
        super().__init__(api_key, secret_key, imei=imei)
        if session_cookies:
            self.session_cookies = session_cookies

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        if not isinstance(message, str):
            return

        # Ghi nhớ khung chat để làm đích dự phòng khi báo tiền
        if str(author_id) in ADMIN_ZALO_IDS or str(thread_id) in ADMIN_ZALO_IDS:
            last_chat["thread_id"] = thread_id
            last_chat["thread_type"] = thread_type

        text = message.strip().lower()

        if text == "id":
            self.replyMessage(
                Message(
                    text=f"📌 THÔNG TIN ID KHUNG CHAT:\n"
                         f"- UID cá nhân của bạn: {author_id}\n"
                         f"- ID khung chat hiện tại (Thread ID): {thread_id}"
                ),
                message_object, thread_id, thread_type,
            )
            return

        if text == "test":
            self.replyMessage(
                Message(text="✅ Bot đang hoạt động, gửi/nhận tin bình thường."),
                message_object, thread_id, thread_type,
            )
            return

        if text.startswith(("qr ", "/qr ")):
            self.handle_qr(message.strip(), message_object, thread_id, thread_type)

    def handle_qr(self, raw_text, message_object, thread_id, thread_type):
        parts = raw_text.split(maxsplit=2)
        if len(parts) < 2:
            self.replyMessage(
                Message(text="⚠️ Sai cú pháp! Hãy nhập: qr <số tiền>\nVí dụ: qr 50000"),
                message_object, thread_id, thread_type,
            )
            return

        raw_amount = parts[1].lower().replace("k", "000").replace(",", "").replace(".", "")
        if not raw_amount.isdigit() or int(raw_amount) <= 0:
            self.replyMessage(
                Message(text="⚠️ Số tiền không hợp lệ! Vui lòng nhập số (VD: qr 50000)."),
                message_object, thread_id, thread_type,
            )
            return

        amount = int(raw_amount)

        # Sinh mã không trùng với đơn đang chờ
        with orders_lock:
            while True:
                trans_code = "TT" + "".join(random.choices(string.digits, k=4))
                if trans_code not in pending_orders:
                    break

        extra_note = parts[2] if len(parts) > 2 else ""
        transfer_content = f"{trans_code} {extra_note}".strip()

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
            log.info("Tạo đơn %s | %s VNĐ | thread %s", trans_code, amount, thread_id)

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
            log.error("Lỗi tạo QR: %s", e)
            self.replyMessage(
                Message(text=f"❌ Lỗi khi tạo mã QR: {e}"),
                message_object, thread_id, thread_type,
            )
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

    # Số tiền: +2,000 VND (tiền vào) hoặc -2,000 VND (tiền ra)
    # (?<![\w]) để không bắt nhầm dấu '-' trong ngày kiểu 18-10-2026
    credit = re.search(r"(?<![\w])\+\s*(?:VND|VNĐ)?\s*([\d][\d\.,]*)", full_text, re.IGNORECASE)
    debit = re.search(r"(?<![\w])-\s*(?:VND|VNĐ)?\s*([\d][\d\.,]*)", full_text, re.IGNORECASE)

    direction, amount = None, 0
    if credit:
        direction = "in"
        amount = int(re.sub(r"[^\d]", "", credit.group(1)) or 0)
    elif debit:
        direction = "out"
        amount = int(re.sub(r"[^\d]", "", debit.group(1)) or 0)

    # Số dư
    balance = "Không rõ"
    balance_int = None
    bal = re.search(r"Số dư[:\s]*(?:VND|VNĐ)?\s*([\d][\d\.,]*)", full_text, re.IGNORECASE)
    if bal:
        digits = re.sub(r"[^\d]", "", bal.group(1))
        if digits:
            balance_int = int(digits)
            balance = fmt_money(balance_int)

    # Mã đơn TTxxxx
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


BALANCE_FILE = "cache/last_balance.json"


def load_last_balance():
    try:
        with open(BALANCE_FILE, "r", encoding="utf-8") as f:
            return int(json.load(f).get("balance"))
    except Exception:
        return None


def save_last_balance(value: int):
    try:
        with open(BALANCE_FILE, "w", encoding="utf-8") as f:
            json.dump({"balance": value}, f)
    except Exception as e:
        log.error("Không lưu được số dư: %s", e)


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
            log.info("Đơn %s hết hạn, đã xoá.", c)


# ==========================================
# 7. SERVER FLASK NHẬN BIẾN ĐỘNG TỪ ANDROID
# ==========================================
app = Flask(__name__)


def parse_body() -> dict:
    """Đọc body kể cả khi JSON bị hỏng do nội dung thông báo có xuống dòng / dấu nháy."""
    raw = request.get_data(as_text=True) or ""
    try:
        data = json.loads(raw, strict=False)  # strict=False cho phép xuống dòng trong chuỗi
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    log.warning("JSON hỏng, dùng bộ đọc dự phòng. Body gốc:\n%s", raw)
    data = {}
    m = re.search(r'"secret"\s*:\s*"(.*?)"\s*[,}]', raw, re.S)
    if m:
        data["secret"] = m.group(1)
    m = re.search(r'"title"\s*:\s*"(.*?)"\s*,\s*"(?:content|big)"', raw, re.S)
    if m:
        data["title"] = m.group(1)
    m = re.search(r'"content"\s*:\s*"(.*?)"\s*(?:,\s*"big"|\}\s*$)', raw, re.S)
    if m:
        data["content"] = m.group(1)
    m = re.search(r'"big"\s*:\s*"(.*)"\s*\}\s*$', raw, re.S)
    if m:
        data["big"] = m.group(1)
    return data


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "bot_ready": bot_client is not None,
        "pending": list(pending_orders.keys()),
        "queue": send_queue.qsize(),
    })


@app.route("/test", methods=["GET"])
def test_send():
    """Mở http://127.0.0.1:5000/test?secret=... để thử bot có gửi được Zalo không."""
    if request.args.get("secret") != WEBHOOK_SECRET:
        return jsonify({"status": "unauthorized"}), 401
    enqueue_admin("🔔 Tin nhắn thử từ webhook: nếu bạn thấy tin này thì Zalo gửi OK.")
    return jsonify({"status": "queued"})


@app.route("/webhook/bank", methods=["POST"])
def receive_bank_notification():
    try:
        data = parse_body()
        log.info("Webhook nhận: %s", json.dumps(data, ensure_ascii=False))

        if data.get("secret") != WEBHOOK_SECRET:
            log.warning("Sai secret.")
            return jsonify({"status": "unauthorized"}), 401

        title = str(data.get("title", ""))
        content = str(data.get("content", ""))
        big = str(data.get("big", ""))

        # Dùng bản nội dung dài hơn (thường có đủ số dư)
        if len(big) > len(content):
            content = big

        # Magic text MacroDroid chưa được thay giá trị
        if re.fullmatch(r"\s*[\[\{].*?[\]\}]\s*", content):
            log.warning("Nội dung vẫn là placeholder '%s' -> sai tên magic text trong MacroDroid!", content)

        if is_duplicate(title, content):
            log.info("Thông báo trùng, bỏ qua.")
            return jsonify({"status": "duplicate"}), 200

        if bot_client is None:
            log.error("bot_client chưa khởi tạo.")
            return jsonify({"status": "bot_not_ready"}), 503

        purge_expired_orders()
        info = parse_tcb_notification(title, content)
        # Thông báo không có số tiền -> tính từ chênh lệch số dư so với lần trước
        if info["direction"] is None and info["balance_int"] is not None:
            prev = load_last_balance()
            if prev is not None and info["balance_int"] != prev:
                diff = info["balance_int"] - prev
                info["direction"] = "in" if diff > 0 else "out"
                info["amount"] = abs(diff)
                log.info("Số tiền tính từ chênh lệch số dư: %s -> %s = %s", prev, info["balance_int"], diff)
        if info["balance_int"] is not None:
            save_last_balance(info["balance_int"])

        log.info("Phân tích: %s", info)

        amount = info["amount"]
        matched_code = None
        order = None

        if info["direction"] == "in":
            with orders_lock:
                if info["code"] and info["code"] in pending_orders:
                    matched_code = info["code"]
                else:
                    low = info["full_text"].lower()
                    for code in pending_orders:
                        if code.lower() in low:
                            matched_code = code
                            break
                if matched_code:
                    order = pending_orders.pop(matched_code)

        if order:
            expected = order["amount"]
            if amount >= expected:
                msg = (
                    f"✅ ĐÃ NHẬN TIỀN THÀNH CÔNG!\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔑 Mã đơn: {matched_code}\n"
                    f"💰 Số tiền nhận: +{fmt_money(amount)} VNĐ\n"
                    f"💳 Số dư hiện tại: {info['balance']} VNĐ\n"
                    f"🕒 Trạng thái: Đã thanh toán đủ"
                )
            else:
                msg = (
                    f"⚠️ ĐÃ NHẬN NHƯNG CHƯA ĐỦ TIỀN!\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔑 Mã đơn: {matched_code}\n"
                    f"💰 Đã nhận: +{fmt_money(amount)} / {fmt_money(expected)} VNĐ\n"
                    f"💳 Số dư hiện tại: {info['balance']} VNĐ\n"
                    f"❗ Còn thiếu: {fmt_money(expected - amount)} VNĐ"
                )
            # Gửi về khung chat tạo QR; nếu lỗi thì dự phòng báo admin
            # Báo về khung chat đã tạo QR (lỗi thì dự phòng sang admin)
            enqueue(msg, [(order["thread_id"], order["thread_type"])] + admin_targets())
            # Đồng thời báo cho các admin khác (trừ khung chat vừa báo)
            for uid in ADMIN_ZALO_IDS:
                if str(uid) != str(order["thread_id"]):
                    send_queue.put((msg, [(uid, ThreadType.USER)]))
        else:
            if info["direction"] == "in":
                head = "🔔 BIẾN ĐỘNG SỐ DƯ TECHCOMBANK"
                money = f"💰 Số tiền: +{fmt_money(amount)} VNĐ\n"
            elif info["direction"] == "out":
                head = "🔻 TIỀN RA TECHCOMBANK"
                money = f"💰 Số tiền: -{fmt_money(amount)} VNĐ\n"
            else:
                head = "📩 THÔNG BÁO TỪ TECHCOMBANK"
                money = ""
            msg = (
                f"{head}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"{money}"
                f"💳 Số dư hiện tại: {info['balance']} VNĐ\n"
                f"📄 Chi tiết: {info['full_text']}"
            )
            enqueue_admin(msg)

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
    # Khởi tạo bot với các tham số cơ bản trước
    bot_client = MoneyBot("</>", "</>", imei=IMEI)
# Gán trực tiếp session_cookies vào thuộc tính của client sau khi khởi tạo
    bot_client.session_cookies = SESSION_COOKIES

    threading.Thread(target=sender_worker, daemon=True).start()
    threading.Thread(target=start_webhook_server, daemon=True).start()

    log.info("✅ Webhook Techcombank chạy tại cổng 5000")
    log.info("✅ Gõ 'qr <số tiền>' trên Zalo để tạo QR | 'test' để kiểm tra bot | 'id' để lấy ID")

    bot_client.listen()