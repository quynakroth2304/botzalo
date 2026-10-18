import time
import threading
import random 
import string
import requests
import os
import urllib.parse
from flask import Flask, request, jsonify
from zlapi import ZaloAPI, ZaloAPIException
from zlapi.models import Message

class Honhattruong(ZaloAPI):
    def __init__(self, api_key, secret_key, imei, session_cookies):
        super().__init__(api_key, secret_key, imei=imei, session_cookies=session_cookies)
        
        # ==========================================
        # 1. CẤU HÌNH NGÂN HÀNG & DỊCH VỤ CỦA BẠN
        # ==========================================
        # Khách dùng MoMo hay App Bank nào quét VietQR này cũng được
        self.BANK_ID = "TCB"                 # Mã ngân hàng (VD: MB, VCB, TCB, VPB...)
        self.ACCOUNT_NO = "9823042007"      # Số tài khoản ngân hàng của bạn
        self.ACCOUNT_NAME = "NGUYEN DUC DUY TRUONG" # Tên in trên thẻ (Viết Hoa Không Dấu)
        # Bảng giá dịch vụ
        self.dich_vu = {
            "vip1": 10000,   
            "vip2": 50000,   
            "tool": 100000   
        }
        
        # Lưu các mã đơn hàng đang chờ khách thanh toán
        self.pending_orders = {} 
        
        # Bật server lắng nghe Webhook chạy ngầm
        self.start_webhook_server()

    # ==========================================
    # 2. HÀM TẠO MÃ NỘI DUNG CHUYỂN KHOẢN
    # ==========================================
    def generate_random_code(self):
        # Tạo 5 số ngẫu nhiên. VD: NDDTNTP84729 (Viết liền để khách dễ copy/nhìn)
        random_str = ''.join(random.choices(string.digits, k=5))
        return f"NDDTNTP {random_str}"

    # ==========================================
    # 3. HÀM LẮNG NGHE WEBHOOK TỪ SEPAY/CASSO
    # ==========================================
    def start_webhook_server(self):
        app = Flask(__name__)

        @app.route('/api/webhook/sepay', methods=['POST'])
        def receive_webhook():
            try:
                data = request.json
                
                # Format data chuẩn của SePay (Dịch vụ Webhook Ngân Hàng miễn phí)
                so_tien_vao = int(data.get('transferAmount', 0))
                noi_dung_ck = data.get('content', '').upper()
                ma_gd = data.get('referenceCode', '')

                print(f"\n💰 [WEBHOOK] Có tiền vào: +{so_tien_vao:,}đ | ND: {noi_dung_ck}")

                # Quét xem nội dung CK có chứa mã đơn hàng nào đang chờ không
                for order_code, info in list(self.pending_orders.items()):
                    if order_code in noi_dung_ck:
                        thread_id = info['thread_id']
                        thread_type = info['thread_type']
                        ten_goi = info['ten_goi']
                        gia_tien_goc = info['amount']
                        
                        # Check xem khách chuyển đủ tiền không
                        if so_tien_vao >= gia_tien_goc:
                            msg_text = (
                                f"✅ THANH TOÁN THÀNH CÔNG!\n"
                                f"📦 Dịch vụ: {ten_goi.upper()}\n"
                                f"💰 Số tiền: +{so_tien_vao:,} VND\n"
                                f"Mã GD: {ma_gd}\n\n"
                                f"🎉 Hệ thống đã tự động kích hoạt dịch vụ cho bạn!"
                            )
                        else:
                            msg_text = (
                                f"⚠️ THANH TOÁN THIẾU TIỀN!\n"
                                f"Bạn vừa chuyển {so_tien_vao:,}đ cho gói {ten_goi.upper()} (Giá: {gia_tien_goc:,}đ).\n"
                                f"Vui lòng liên hệ Admin để được hỗ trợ."
                            )
                        
                        # Bắn tin nhắn lên Zalo
                        self.send(Message(text=msg_text), thread_id=thread_id, thread_type=thread_type)
                        
                        # Xóa đơn khỏi hàng đợi
                        del self.pending_orders[order_code]
                        break 

                return jsonify({"success": True}), 200
            except Exception as e:
                print(f"Lỗi Webhook: {e}")
                return jsonify({"success": False}), 500

        # Chạy Flask Server ngầm ở port 5000
        threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False), daemon=True).start()
        print("🚀 Đã khởi động Webhook Server tại port 5000!")

    # ==========================================
    # 4. LẮNG NGHE LỆNH TỪ ZALO
    # ==========================================
    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        if not isinstance(message, str): return
        
        if text.lower() == "id":
            self.replyMessage(
        Message(text=f"👤 UID của bạn: {author_id}\n💬 ID khung chat này: {thread_id}"),
        message_object, thread_id, thread_type
    )
            return

        # ------------------------------------------------
        # LỆNH: .mua <tên_gói>
        # ------------------------------------------------
        if message.startswith(".mua"):
            parts = message.split()
            
            if len(parts) < 2:
                danh_sach = "\n".join([f"- {k}: {v:,} VNĐ" for k, v in self.dich_vu.items()])
                self.replyMessage(
                    Message(text=f"🚫 Vui lòng chọn gói dịch vụ.\nDanh sách:\n{danh_sach}\n\n👉 Cú pháp: .mua <tên_gói>"), 
                    message_object, thread_id=thread_id, thread_type=thread_type
                )
                return
                
            ten_goi = parts[1].lower()
            
            if ten_goi not in self.dich_vu:
                self.replyMessage(Message(text=f"🚫 Gói dịch vụ '{ten_goi}' không tồn tại!"), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            amount = self.dich_vu[ten_goi]
            noidung_chuyenkhoan = self.generate_random_code()
            
            self.replyMessage(Message(text=f"⏳ Đang tạo mã VietQR cho gói {ten_goi.upper()}..."), message_object, thread_id=thread_id, thread_type=thread_type)

            try:
                # Lưu thông tin đơn hàng để chờ Webhook
                self.pending_orders[noidung_chuyenkhoan] = {
                    'thread_id': thread_id,
                    'thread_type': thread_type,
                    'ten_goi': ten_goi,
                    'amount': amount
                }

                # Mã hóa dữ liệu để tạo Link QR
                msg_encoded = urllib.parse.quote(noidung_chuyenkhoan)
                name_encoded = urllib.parse.quote(self.ACCOUNT_NAME)
                
                # Lấy ảnh VietQR (Chuẩn quốc gia - Quét app nào cũng dính)
                qr_url = f"https://img.vietqr.io/image/{self.BANK_ID}-{self.ACCOUNT_NO}-compact2.png?amount={amount}&addInfo={msg_encoded}&accountName={name_encoded}"

                img_response = requests.get(qr_url)
                qr_filename = f"qr_{noidung_chuyenkhoan}.png"
                with open(qr_filename, 'wb') as f:
                    f.write(img_response.content)

                # Gửi ảnh QR lên Zalo
                text_msg = (
                    f"💳 THANH TOÁN TỰ ĐỘNG\n"
                    f"📦 Gói: {ten_goi.upper()}\n"
                    f"💰 Số tiền: {amount:,} VND\n"
                    f"📝 Lời nhắn CK: {noidung_chuyenkhoan}\n\n"
                    f"👉 Lưu ảnh này và mở App MoMo (hoặc App Ngân Hàng) để quét.\n"
                    f"⚠️ LƯU Ý: Giữ nguyên lời nhắn chuyển khoản để Bot tự động duyệt nhé!"
                )
                self.sendLocalImage(qr_filename, thread_id=thread_id, thread_type=thread_type, message=Message(text=text_msg))

                # Dọn dẹp ảnh
                os.remove(qr_filename)

            except Exception as e:
                self.replyMessage(Message(text=f"🚫 Có lỗi khi tải mã QR: {e}"), message_object, thread_id=thread_id, thread_type=thread_type)
            
            return

        if message == ".ping":
            self.replyMessage(Message(text="Bot đang hoạt động nha!"), message_object, thread_id=thread_id, thread_type=thread_type)

# ==========================================
# KHỞI CHẠY BOT
# ==========================================
if __name__ == "__main__":
    imei = "aa98367f-255d-4304-8f2e-12c4d9a7d48d-925436884cc9a6b8005feb055c610baf" 
    
    # [QUAN TRỌNG] THAY COOKIE MỚI NHẤT VÀO ĐÂY ĐỂ KHÔNG BỊ LỖI
    session_cookies = {"_ga_YT9TMXZYV9":"GS2.1.s1783138882$o2$g0$t1783138887$j55$l0$h0","_ga":"GA1.2.898049639.1775112362","__zi":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8Wxd-oYcKXQY76UwApSIbs6VfZkepCo.1","__zi-legacy":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8Wxd-oYcKXQY76UwApSIbs6VfZkepCo.1","_ga_RYD7END4JE":"GS2.2.s1776578868$o2$g1$t1776578869$j59$l0$h0","_ga_YS1V643LGV":"GS2.1.s1789306579$o5$g0$t1789306580$j59$l0$h0","_ga_3EM8ZPYYN3":"GS2.2.s1792313585$o8$g0$t1792313585$j60$l0$h0","_zlang":"vn","_gid":"GA1.2.137833363.1792313586","_gat":"1","zsid":"EXPIRED","zpsid":"mQ5b.456166036.6.jpSKFjWYXMXCgBLpr2A5QArHzrpj5BHUxXAsNjaKaRaCrXFRsIaClB8YXMW","zpw_sek":"-jJu.456166036.a0.zrK_dx96JPanCyZqXBduxzwRdOI7WzgtresrfvRgmPh2yvg1vDVAlkRDZ8VqXCNDsBZE-tHj37aMkFDcSTFuxm","app.event.zalo.me":"2887145055420781720"}
    
    try:
        bot = Honhattruong('api_key', 'secret_key', imei=imei, session_cookies=session_cookies)
        bot.listen()
    except Exception as e:
        print(f"Lỗi khởi động Bot Zalo: {e}")