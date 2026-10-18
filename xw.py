import time
import threading
import json
import random 
import requests
import os
import uuid
import hmac
import hashlib
import qrcode
from flask import Flask, request, jsonify
from zlapi import ZaloAPI, ZaloAPIException
from zlapi.models import Message, ThreadType

class Honhattruong(ZaloAPI):
    def __init__(self, api_key, secret_key, imei, session_cookies):
        super().__init__(api_key, secret_key, imei=imei, session_cookies=session_cookies)
        
        # ==========================================
        # 1. CẤU HÌNH HỆ THỐNG THANH TOÁN
        # ==========================================
        # [QUAN TRỌNG] ĐIỀN LINK NGROK CỦA BẠN VÀO ĐÂY (Không có dấu / ở cuối)
        self.NGROK_URL = "https://THAY_LINK_NGROK_CUA_BAN_VAO_DAY.ngrok-free.app"
        
        # Bảng giá dịch vụ của bạn
        self.dich_vu = {
            "vip1": 10000,  # Gói vip1 giá 10k
            "vip2": 50000,  # Gói vip2 giá 50k
            "tool": 100000  # Mua tool giá 100k
        }
        
        self.pending_orders = {} # Lưu trữ các đơn hàng đang chờ khách quét QR
        
        # Khởi động Webhook Server chạy ngầm
        self.start_webhook_server()

    # ==========================================
    # 2. HÀM GỌI API MOMO TẠO ĐƠN HÀNG
    # ==========================================
    def create_momo_payment(self, amount, order_id):
        # Thông tin Test từ MoMo API V2
        endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
        partnerCode = "MOMO"
        accessKey = "F8BBA842ECF85"
        secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
        orderInfo = f"Thanh toan don hang {order_id}"
        
        ipnUrl = f"{self.NGROK_URL}/api/webhook/momo" 
        redirectUrl = ipnUrl
        
        requestId = str(uuid.uuid4())
        requestType = "captureWallet"
        extraData = ""

        # Tạo chữ ký điện tử (Signature)
        rawSignature = f"accessKey={accessKey}&amount={amount}&extraData={extraData}&ipnUrl={ipnUrl}&orderId={order_id}&orderInfo={orderInfo}&partnerCode={partnerCode}&redirectUrl={redirectUrl}&requestId={requestId}&requestType={requestType}"
        h = hmac.new(bytes(secretKey, 'ascii'), bytes(rawSignature, 'ascii'), hashlib.sha256)
        signature = h.hexdigest()

        data = {
            'partnerCode': partnerCode,
            'partnerName': "Test Store",
            'storeId': "MomoTestStore",
            'requestId': requestId,
            'amount': str(amount),
            'orderId': order_id,
            'orderInfo': orderInfo,
            'redirectUrl': redirectUrl,
            'ipnUrl': ipnUrl,
            'lang': "vi",
            'extraData': extraData,
            'requestType': requestType,
            'signature': signature
        }

        response = requests.post(endpoint, json=data)
        return response.json()

    # ==========================================
    # 3. HÀM LẮNG NGHE WEBHOOK (TỰ ĐỘNG CHECK TIỀN)
    # ==========================================
    def start_webhook_server(self):
        app = Flask(__name__)

        @app.route('/api/webhook/momo', methods=['POST'])
        def momo_webhook():
            try:
                data = request.json
                order_id = data.get('orderId')
                result_code = data.get('resultCode')
                amount_received = int(data.get('amount', 0))

                print(f"\n[MOMO WEBHOOK] Báo cáo đơn {order_id} - KQ: {result_code} - Tiền: {amount_received}")

                # Nếu MoMo báo thành công (0) và đơn hàng có trong danh sách chờ
                if result_code == 0 and order_id in self.pending_orders:
                    info = self.pending_orders[order_id]
                    thread_id = info['thread_id']
                    thread_type = info['thread_type']
                    ten_goi = info['ten_goi']
                    gia_tien_goc = info['amount']
                    
                    # Kiểm tra an toàn: Số tiền nhận được phải >= giá của gói
                    if amount_received >= gia_tien_goc:
                        msg_text = (
                            f"✅ THANH TOÁN THÀNH CÔNG!\n"
                            f"📦 Dịch vụ: {ten_goi.upper()}\n"
                            f"💰 Số tiền: {amount_received:,} VND\n"
                            f"Mã đơn: {order_id}\n\n"
                            f"🎉 Hệ thống đã ghi nhận và kích hoạt dịch vụ cho bạn!"
                        )
                        # TẠI ĐÂY: Bạn có thể code thêm logic cộng tiền vào DB, cấp quyền,...
                    else:
                        msg_text = (
                            f"⚠️ THANH TOÁN LỖI!\n"
                            f"Mã đơn: {order_id}\n"
                            f"Bạn chuyển thiếu tiền ({amount_received:,} / {gia_tien_goc:,} VND).\n"
                            f"Vui lòng liên hệ Admin để xử lý."
                        )
                    
                    # Gửi tin nhắn thông báo vào nhóm Zalo
                    self.send(Message(text=msg_text), thread_id=thread_id, thread_type=thread_type)
                    
                    # Xóa đơn hàng khỏi danh sách chờ
                    del self.pending_orders[order_id]

                return "", 204 # HTTP 204 báo cho MoMo là đã nhận thành công
            except Exception as e:
                print(f"Lỗi xử lý Webhook MoMo: {e}")
                return jsonify({"error": "Internal Error"}), 500

        # Chạy Flask ở port 5000 ngầm để không chặn Zalo Bot
        threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
        print("🚀 Đã khởi động Webhook MoMo tại port 5000!")

    # ==========================================
    # 4. HÀM XỬ LÝ TIN NHẮN ZALO TỪ NGƯỜI DÙNG
    # ==========================================
    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        if not isinstance(message, str): return

        # ------------------------------------------------
        # LỆNH: .mua <tên_gói>
        # ------------------------------------------------
        if message.startswith(".mua"):
            parts = message.split()
            
            # Nếu người dùng chỉ gõ ".mua" mà không ghi tên gói
            if len(parts) < 2:
                danh_sach_goi = "\n".join([f"- {k}: {v:,} VNĐ" for k, v in self.dich_vu.items()])
                self.replyMessage(
                    Message(text=f"🚫 Vui lòng chọn một dịch vụ. Danh sách gói:\n{danh_sach_goi}\nCú pháp: .mua <tên_gói>"), 
                    message_object, thread_id=thread_id, thread_type=thread_type
                )
                return
                
            ten_goi = parts[1].lower()
            
            # Kiểm tra xem gói có tồn tại trong bảng giá không
            if ten_goi not in self.dich_vu:
                self.replyMessage(Message(text=f"🚫 Dịch vụ '{ten_goi}' không tồn tại!"), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            # Lấy giá tiền và tạo Order ID
            amount = self.dich_vu[ten_goi]
            order_id = f"MOMO_{int(time.time())}_{random.randint(100, 999)}"
            
            self.replyMessage(Message(text=f"⏳ Đang khởi tạo cổng thanh toán cho gói {ten_goi.upper()}..."), message_object, thread_id=thread_id, thread_type=thread_type)

            # Gọi API MoMo để lấy payUrl
            momo_response = self.create_momo_payment(amount, order_id)
            
            if momo_response.get('resultCode') == 0:
                pay_url = momo_response.get('payUrl')
                
                # Lưu thông tin đơn hàng để chờ Webhook xử lý
                self.pending_orders[order_id] = {
                    'thread_id': thread_id,
                    'thread_type': thread_type,
                    'ten_goi': ten_goi,
                    'amount': amount
                }

                # Dùng thư viện tạo ảnh QR từ pay_url
                img = qrcode.make(pay_url)
                qr_filename = f"qr_{order_id}.png"
                img.save(qr_filename)

                # Gửi ảnh QR lên Zalo
                self.sendLocalImage(qr_filename, thread_id=thread_id, thread_type=thread_type)
                
                # Gửi Text hướng dẫn kèm link (Người dùng dùng đt bấm vào link là tự nhảy sang MoMo)
                text_msg = (
                    f"💳 ĐƠN HÀNG: {ten_goi.upper()}\n"
                    f"💰 Giá tiền: {amount:,} VND\n\n"
                    f"👉 Quét mã QR phía trên HOẶC bấm vào link dưới đây để mở MoMo thanh toán:\n{pay_url}\n\n"
                    f"⏳ Bot sẽ tự động thông báo tại đây ngay khi bạn thanh toán xong."
                )
                self.replyMessage(Message(text=text_msg), message_object, thread_id=thread_id, thread_type=thread_type)

                # Dọn dẹp ảnh QR rác trong máy tính sau khi gửi xong
                os.remove(qr_filename)
            else:
                err_msg = momo_response.get('message', 'Lỗi không xác định')
                self.replyMessage(Message(text=f"🚫 Lỗi kết nối MoMo: {err_msg}"), message_object, thread_id=thread_id, thread_type=thread_type)
            
            return

        # ------------------------------------------------
        # Test Ping
        # ------------------------------------------------
        if message == ".ping":
            self.replyMessage(Message(text="Bot đang hoạt động ổn định!"), message_object, thread_id=thread_id, thread_type=thread_type)


# ==========================================
# KHỞI CHẠY BOT
# ==========================================
if __name__ == "__main__":
    imei = "f52aff4f-3486-49b8-8108-df11cfb621e5-6c7753023a346715c58bb220997cb8f2" 
    
    # THAY COOKIE CỦA BẠN VÀO ĐÂY
    session_cookies = {"_ga_YT9TMXZYV9":"GS2.1.s1775112361$o1$g0$t1775112366$j55$l0$h0","_ga":"GA1.2.898049639.1775112362","__zi":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8Wxd-oYcKXQY76UwAFJJ5g6Svhhh3an.1","__zi-legacy":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8Wxd-oYcKXQY76UwAFJJ5g6Svhhh3an.1","_ga_RYD7END4JE":"GS2.2.s1776578868$o2$g1$t1776578869$j59$l0$h0","_ga_YS1V643LGV":"GS2.1.s1776578868$o2$g0$t1776578869$j59$l0$h0","_ga_3EM8ZPYYN3":"GS2.2.s1776578873$o2$g1$t1776579163$j60$l0$h0","_gid":"GA1.2.1145648030.1776578869","_zlang":"vn","app.event.zalo.me":"2887145055420781720","_gat":"1","zpsid":"-Bg3.456166036.0.4_nvHXqkG6I9f71_4Iv0P6XTCb0e675IAnvpKYUKuezAvzzu77WpW7GkG6G","zpw_sek":"Pzvw.456166036.a0.P9ZGrRThwZqZuTecbclgFSn9ZrQLKSXvqLFQUuGjcax53eDdWJ6RMlW_laZ0LjSVob5Gdrmy8wAhQhnEKmBgFG"}
    
    try:
        bot = Honhattruong('api_key', 'secret_key', imei=imei, session_cookies=session_cookies)
        bot.listen()
    except Exception as e:
        print(f"Lỗi khởi động Bot Zalo: {e}")
        '
        {"_ga_YT9TMXZYV9":"GS2.1.s1775112361$o1$g0$t1775112366$j55$l0$h0","_ga":"GA1.2.898049639.1775112362","__zi":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8Wxd-oYcKXQY76UwAFJJ5g6Svhhh3an.1","__zi-legacy":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8Wxd-oYcKXQY76UwAFJJ5g6Svhhh3an.1","_ga_RYD7END4JE":"GS2.2.s1776578868$o2$g1$t1776578869$j59$l0$h0","_ga_YS1V643LGV":"GS2.1.s1776578868$o2$g0$t1776578869$j59$l0$h0","_ga_3EM8ZPYYN3":"GS2.2.s1776578873$o2$g1$t1776580017$j60$l0$h0","_gid":"GA1.2.1145648030.1776578869","_zlang":"vn","app.event.zalo.me":"2887145055420781720","zpw_sek":"gCd4.456166036.a0.e8En-YXETHYyn4K32Kvr65Di47CAT5TwHtbURN4R1sfzBImhNZeYLXjsB5LvSqWwLNJFkiCPl8SqJvrjp2Tr60","_gat":"1","zpsid":"t8FP.456166036.1.oGUQRULpk3bn-OWYwNEuEP00oWtGHOaFqqEB3z_96jAokYSbv9JDtOnpk3a"}'