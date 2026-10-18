import re
from zlapi import ZaloAPI, ZaloAPIException
from zlapi.models import *
import time
import threading
import json
import datetime
import subprocess
import random 
import requests
from PIL import Image, ImageDraw, ImageFont
import os
#admin:Hồ nhật trường (X)
#xoá 3 comment này là chó
#siuuuuu

class Honhattruong(ZaloAPI):
    def __init__(self, api_key, secret_key, imei, session_cookies):
        super().__init__(api_key, secret_key, imei=imei, session_cookies=session_cookies)
        self.idnguoidung = ['207754413506549669']
        self.excluded_user_ids = []
        self.spamming = False
        self.spam_thread = None
        self.name_change_thread = None
        self.isUndoLoop = False
        self.xoatn_mode = False
        self.dangky_file = 'tt.txt'
        self.codes = {
            'F88': 9999999,
            'HNTTOOL': 555555555555555
        }
        self.admin_key = '11009922'
        self.is_admin = False
        self.last_sms_times = {}
        self.random_users = set()  
        self.delete_links = False
        self.reo_spamming = False  
        self.reo_spam_thread = None
        self.Group = False
        self.color_list = [
            "#FFFFFF", "#00FF00", "#EEEEEE", "#DDDDDD", "#CCCCCC", 
            "#BBBBBB", "#AAAAAA", "#999999", "#888888", "#777777", 
            "#666666", "#555555", "#444444", "#333333", "#222222", 
            "#111111", "#000000", "#FF0000", "#EE0000", "#DD0000", 
            "#CC0000", "#BB0000", "#AA0000", "#990000", "#880000", 
            "#770000", "#660000", "#550000", "#440000", "#330000", 
            "#220000", "#110000", "#FFFFCC", "#FFFF99", "#FFFF66", 
            "#FFFF33", "#FFFF00", "#CCFFFF", "#CCFFCC", "#CCFF99", 
            "#CCFF66", "#CCFF33", "#CCFF00", "#99FFFF", "#99FFCC", 
            "#99FF99", "#99FF66", "#99FF33", "#99FF00", "#66FFFF", 
            "#66FFCC", "#66FF99", "#66FF66", "#66FF33", "#66FF00", 
            "#33FFFF", "#33FFCC", "#33FF99", "#33FF66", "#33FF33", 
            "#33FF00", "#00FFFF", "#00FFCC", "#00FF99", "#00FF66", 
            "#00FF33", "#00FF00", "#FFCCFF", "#FFCCCC", "#FFCC99", 
            "#FFCC66", "#FFCC33", "#FFCC00", "#CCCCFF", "#CCCCCC", 
            "#CCCC99", "#CCCC66", "#CCCC33", "#CCCC00", "#99CCFF", 
            "#99CCCC", "#99CC99", "#99CC66", "#99CC33", "#99CC00", 
            "#66CCFF", "#66CCCC", "#66CC99", "#66CC66", "#66CC33", 
            "#66CC00", "#33CCFF", "#33CCCC", "#33CC99", "#33CC66", 
            "#33CC33", "#33CC00", "#00CCFF", "#00CCCC", "#33CC66", 
            "#33CC33", "#00CC99", "#00CC66", "#00CC33", "#00CC00", 
            "#FF99FF", "#FF99CC", "#FF9999", "#FF9966", "#FF9933", 
            "#FF9900", "#CC99FF", "#CC99CC", "#CC9999", "#CC9966", 
            "#CC9933", "#CC9900", "#9999FF", "#9999CC", "#999999", 
            "#999966", "#999933", "#999900", "#6699FF", "#6699CC", 
            "#669999", "#669966", "#669933", "#669900", "#3399FF", 
            "#3399CC", "#339999", "#339966", "#339933", "#339900", 
            "#0099FF", "#0099CC", "#009999", "#009966", "#009933", 
            "#009900", "#FF66FF", "#FF66CC", "#FF6699", "#FF6666", 
            "#FF6633", "#FF6600", "#CC66FF", "#CC66CC", "#CC6699", 
            "#CC6666", "#CC6633", "#CC6600", "#9966FF", "#9966CC", 
            "#996699", "#996666", "#996633", "#996600", "#6666FF", 
            "#6666CC", "#666699", "#666666", "#666633", "#666600", 
            "#3366FF", "#3366CC", "#336699", "#336666", "#336633", 
            "#336600", "#0066FF", "#0066CC", "#006699", "#006666", 
            "#006633", "#006600", "#FF33FF", "#FF33CC", "#FF3399", 
            "#FF3366", "#FF3333", "#FF3300", "#CC33FF", "#CC33CC", 
            "#CC3399", "#CC3366", "#CC3333", "#CC3300", "#9933FF", 
            "#9933CC", "#993399", "#993366", "#993333", "#993300", 
            "#6633FF", "#6633CC", "#663399", "#663366", "#663333", 
            "#663300", "#3333FF", "#3333CC", "#333399", "#333366", 
            "#333333", "#333300", "#0033FF", "#FF3333", "#0033CC", 
            "#003399", "#003366", "#003333", "#003300", "#FF00FF", 
            "#FF00CC", "#FF0099", "#FF0066", "#FF0033", "#FF0000", 
            "#CC00FF", "#CC00CC", "#CC0099", "#CC0066", "#CC0033", 
            "#CC0000", "#9900FF", "#9900CC", "#990099", "#990066", 
            "#990033", "#990000", "#6600FF", "#6600CC", "#660099", 
            "#660066", "#660033", "#660000", "#3300FF", "#3300CC", 
            "#330099", "#330066", "#330033", "#330000", "#0000FF", 
            "#0000CC", "#000099", "#000066", "#000033", "#00FF00", 
            "#00EE00", "#00DD00", "#00CC00", "#00BB00", "#00AA00", 
            "#009900", "#008800", "#007700", "#006600", "#005500", 
            "#004400", "#003300", "#002200", "#001100", "#0000FF", 
            "#0000EE", "#0000DD", "#0000CC", "#0000BB", "#0000AA", 
            "#000099", "#000088", "#000077", "#000055", "#000044", 
            "#000022", "#000011"
        ]
        self.messages_to_delete = []  
        self.admin_file = 'admin.json'  
        self.start_time = datetime.datetime.now()  
        self.banned_words = set([
            "địt", "lồn", "lol", "đm", "cc", "lon", "đmm", "dm", "dmm", "dit", "cac", "cặc",
            "Lmm", "Óc lợn", "Óc bò", "Djtme", "Nguuuuuuu như ch ó", "Lmm", "dái", "bướm",
            "lỗ nhị", "đéo", "đít", "sex", "chịch", "vú", "đụ", "Dog", "Kẹc", "bím",
            "mẹ mày", "mẹ m", "cha m", "cha mày", "dcu", "đcu", "đcm", "đcmm", "dcm",
            "dcmm", "súc vật", "vlon", "vailon", "loz", "iồn", "ioz", "ioi", "xnxx",
            "mả", "buồi", "cmm", "con mẹ", "fuck", "Địt", "Lồn", "Lol", "Đm", "Cc",
            "Lon", "Đmm", "Đm", "Đmm", "Đit", "Cacc", "Cặc", "Dái", "Bướm", "Lỗ nhị",
            "Đéo", "Đít", "Sex", "Chịch", "Vú", "Đụ", "Bím", "Mẹ mày", "Con mẹ mày",
            "con mẹ mày", "Cha m", "địt cụ mày", "dcu", "đcu", "đcm", "Đcmm", "Đcm",
            "Dcmm", "Súc vật", "Vlon", "Vailonn", "Vailon", "vailonn", "loz", "iồn",
            "ioz", "ioi", "xnxx", "mả", "buồi", "cmm", "Con mẹ", "fuck", "cặc",
            "óc lồn", "óc l", "Óc lồnn", "Iồn", "Sút vậc", "Mẹmaybeo", "Cứt", "Cl"
        ])
# ... (ngay sau dòng self.banned_words = set([...])
        self.banned_word_removal_enabled = False # Thêm dòng này nếu chưa có

        # --- PHẦN THÊM MỚI TỪ AI.PY ---
        self.GEMINI_API_KEY = 'AIzaSyCyDpPZPX-RHCyzFPwjRCtdNMGyYNMvvA0' # API Key từ ai.py
        self.chat_histories = {} # Biến lưu lịch sử chat
        self.INITIAL_PERSONA_PROMPT = "(Bạn đóng vai Trường một người rất bố láo với tính cách nóng nảy thích chửi nhau với người khác,đặc biệt là nói chuyện cực kì láo và mất dạy)"
        self.HISTORY_DIR = "data/history" # Thư mục lưu lịch sử

        # Tự động tạo thư mục nếu chưa có
        os.makedirs(self.HISTORY_DIR, exist_ok=True)
        # --- KẾT THÚC PHẦN THÊM MỚI ---

# ... (phần code còn lại giữ nguyên)

    def load_admins(self):
        try:
            with open(self.admin_file, 'r') as admin_file:
                admin_data = json.load(admin_file)
                return set(admin_data.get('idadmin', []))
        except FileNotFoundError:
            return set()
    
    

    def save_admins(self, admins):
        with open(self.admin_file, 'w') as admin_file:
            json.dump({'idadmin': list(admins)}, admin_file)
    def load_registered_users(self):
        try:
            with open(self.dangky_file, 'r', encoding='utf-8') as file:
                return {line.split(',')[0]: (line.strip().split(',')[1], float(line.strip().split(',')[2])) for line in file.readlines() if line.strip()}
        except FileNotFoundError:
            return {}

    def save_registered_user(self, user_id, user_name):
        with open(self.dangky_file, 'a', encoding='utf-8') as file:
            file.write(f"{user_id},{user_name},500000000\n")

    def update_user_balance(self, user_id, new_balance):
        users = self.load_registered_users()
        if user_id in users:
            user_name = users[user_id][0]
            with open(self.dangky_file, 'w', encoding='utf-8') as file:
                for uid, (name, balance) in users.items():
                    if uid == user_id:
                        file.write(f"{uid},{name},{new_balance}\n")  
                    else:
                        file.write(f"{uid},{name},{balance}\n")  
                        
    
    def load_mutenguoidung(self):
        try:
            with open('mute.json', 'r') as mute_file:
                mute_config = json.load(mute_file)
                return set(mute_config.get('mutenguoidung', []))
        except FileNotFoundError:
            return set()

    def save_mutenguoidung(self, mutenguoidung):
        with open('mute.json', 'w') as mute_file:
            json.dump({'mutenguoidung': list(mutenguoidung)}, mute_file)
    
     
    def send_private_message_to_user(self, user_id, random_data):
        try:
            message_text = "thông tin nick:\n" + "\n".join(random_data)
            private_message = Message(text=message_text)
            self.send(private_message, thread_id=user_id, thread_type=ThreadType.USER)
        except Exception as e:
            print(f"🚫 Lỗi khi gửi tin nhắn: {e}")

    def add_id_to_used_list(self, user_id):
        with open('id.txt', 'a') as id_file:
            id_file.write(user_id + "\n")

    

    def send_lq_accounts(self, author_id, so_luong, thread_id, thread_type, message_object):
        try:
            with open('lq.txt', 'r') as file:
                lines = file.readlines()
            if so_luong > len(lines):
                self.replyMessage(Message(text="Không đủ tài khoản trong file."), message_object, thread_id, thread_type)
                return
            random_accounts = random.sample(lines, so_luong)
            self.send_private_message_to_user(author_id, [account.strip() for account in random_accounts])
            remaining_accounts = [line for line in lines if line not in random_accounts]
            with open('lq.txt', 'w') as file:
                file.writelines(remaining_accounts)
            self.replyMessage(Message(text=f"Đã gửi {so_luong} tài khoản liên quân cho bạn."), message_object, thread_id, thread_type)
        except Exception as e:
            self.replyMessage(Message(text=f"Đã xảy ra lỗi: {e}"), message_object, thread_id, thread_type)
    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        print(f"\033[32m{message} \033[39m|\033[31m {author_id} \033[39m|\033[33m {thread_id}\033[0m\n")
        content = message_object.content if message_object and hasattr(message_object, 'content') else ""
        if not isinstance(message, str):
            print(f"{type(message)}")
            return

        message_text = message  
        
        idadmin = self.load_admins()
        
        # ... (Đặt code này bên trong hàm onMessage, bên cạnh các lệnh .kick, .dt, .admin, v.v.)

        if message.startswith(".call"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            parts = message.split()
            target_group_id = "" # ID nhóm mục tiêu

            if len(parts) > 1:
                # Trường hợp 1: Người dùng cung cấp ID (ví dụ: .call 123456789)
                target_group_id = parts[1]
            else:
                # Trường hợp 2: Người dùng không cung cấp ID (chỉ gõ .call)
                if thread_type != ThreadType.GROUP:
                    self.replyMessage(Message(text='🚫 Bạn đang không ở trong nhóm. Cú pháp: .call <id_nhóm>'), message_object, thread_id=thread_id, thread_type=thread_type)
                    return
                # Dùng ID của nhóm hiện tại
                target_group_id = thread_id 

            try:
                # GỌI HÀM VỚI ID NHÓM MỤC TIÊU
                self.sendGroupCall(thread_id=target_group_id)
                
                # Gửi tin nhắn xác nhận (gửi về nơi đã ra lệnh)
                self.replyMessage(Message(text=f'📞 Đã bắt đầu cuộc gọi tại nhóm ID: {target_group_id}'), message_object, thread_id=thread_id, thread_type=thread_type)
                
            except Exception as e:
                print(f"Lỗi khi gọi nhóm: {e}")
                self.replyMessage(Message(text=f'🚫 Có lỗi xảy ra khi gọi nhóm {target_group_id}: {e}'), message_object, thread_id=thread_id, thread_type=thread_type)
            
            return # Dừng xử lý sau khi thực hiện lệnh

        # ... (Các lệnh khác của bạn tiếp tục bên dưới)
        
        if message.startswith(".kick"):
	        if author_id not in idadmin:
	            self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
	            return
	        
	        mentions = message_object.mentions
	        if not mentions:
	            self.replyMessage(Message(text='🚫 Bạn cần đề cập ít nhất một người dùng để kick.'), message_object, thread_id=thread_id, thread_type=thread_type)
	            return
	        
	        kicked_users = []
	        for mention in mentions:
	            mentioned_user_id = mention['uid']
	            
	            if mentioned_user_id not in self.excluded_user_ids:
	                try:
	                    self.kickUsersFromGroup([mentioned_user_id], thread_id)
	                    kicked_users.append(mentioned_user_id)
	                except Exception as e:
	                    self.replyMessage(Message(text=f'🚫 Có lỗi khi kick người dùng {mentioned_user_id}: {str(e)}'), message_object, thread_id=thread_id, thread_type=thread_type)
	            else:
	                self.replyMessage(Message(text=f'🚫 Không thể kick {mentioned_user_id} vì người này nằm trong danh sách loại trừ.'), message_object, thread_id=thread_id, thread_type=thread_type)
	
	        if kicked_users:
	            self.replyMessage(Message(text=f'✅ Đã kick người dùng: {", ".join(kicked_users)}'), message_object, thread_id=thread_id, thread_type=thread_type)
	        else:
	            self.replyMessage(Message(text='🚫 Không có ai bị kick.'), message_object, thread_id=thread_id, thread_type=thread_type)
        if message.startswith(".dt"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            new_group_name = message[4:].strip()  
            if not new_group_name:
                self.replyMessage(Message(text='🚫 Bạn cần cung cấp tên nhóm mới.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            group_id = thread_id  
            result = self.changeGroupName(new_group_name, group_id)
            if result and isinstance(result, Group):
                self.replyMessage(Message(text=f'✅ Đã đổi tên nhóm thành: {new_group_name}'), message_object, thread_id=thread_id, thread_type=thread_type)
            else:
                self.replyMessage(Message(text='🚫 Có lỗi khi đổi tên nhóm.'), message_object, thread_id=thread_id, thread_type=thread_type)
        if message.startswith(".random"):
            if author_id in self.random_users:
                self.replyMessage(Message(text="🚫 Bạn đã sử dụng lệnh random rồi!"), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            parts = message.split()
            
            if len(parts) != 2 or not parts[1].isdigit():
                self.replyMessage(Message(text="🚫 Vui lòng cung cấp số lượng hợp lệ (1-150 )."), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            quantity = int(parts[1])
            if 1 <= quantity <= 50:
                random_data = self.get_random_data(quantity)
                if random_data:
                    
                    self.send_private_message_to_user(author_id, random_data)
                    
                    self.random_users.add(author_id)
                    
                    self.send(Message(text="✅ hãy kiểm tra tin nhắn riêng ."), thread_id=thread_id, thread_type=thread_type)
                else:
                    self.replyMessage(Message(text="🚫 File rỗng hoặc không thể đọc dữ liệu."), message_object, thread_id=thread_id, thread_type=thread_type)
            else:
                self.replyMessage(Message(text="🚫 Số lượng phải nằm trong khoảng 1 or 50"), message_object, thread_id=thread_id, thread_type=thread_type)
        if content.startswith('.acclq'):
            parts = content.split()
            if len(parts) < 2:
                self.replyMessage(Message(text="Vui lòng nhập số lượng tài khoản cần lấy sau lệnh .acclq"), message_object, thread_id, thread_type)
                return
            
            try:
                so_luong = int(parts[1])
                if 1 <= so_luong <= 100:
                    self.add_id_to_used_list(author_id)  
                    self.send_lq_accounts(author_id, so_luong, thread_id, thread_type, message_object)
                else:
                    self.replyMessage(Message(text="Số lượng phải từ 1 đến 100."), message_object, thread_id, thread_type)
            except ValueError:
                self.replyMessage(Message(text="Số lượng không hợp lệ."), message_object, thread_id, thread_type)
        
            
        if isinstance(content, str) and content.lower().startswith(("vip", "sms")):
            
            parts = content.split()
            if len(parts) == 1:
                self.replyMessage(Message(text='🚫 Vui lòng nhập số điện thoại sau lệnh .\n'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            attack_phone_number = parts[1]
            if not attack_phone_number.isnumeric() or len(attack_phone_number) != 10:
                self.replyMessage(Message(text='❌ Số điện thoại không hợp lệ! Vui lòng nhập đúng số.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            if attack_phone_number in ['113', '911', '114', '115']:
                self.replyMessage(Message(text="⛔ Số này không thể spam."), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            current_time = datetime.datetime.now()
            if author_id in self.last_sms_times:
                last_sent_time = self.last_sms_times[author_id]
                elapsed_time = (current_time - last_sent_time).total_seconds()
                if elapsed_time < 120:
                    self.replyMessage(Message(text="⏳ vui lòng chờ 120s và thử lại!"), message_object, thread_id=thread_id, thread_type=thread_type)
                    return
            self.last_sms_times[author_id] = current_time
            file_path1 = os.path.join(os.getcwd(), "smsv2.py")
            process = subprocess.Popen(["python", file_path1, attack_phone_number, "7"])
            now = datetime.datetime.now()
            time_str = now.strftime("%d/%m/%Y %H:%M:%S")
            masked_phone_number = f"{attack_phone_number[:3]}***{attack_phone_number[-3:]}"
            msg_content = f'''@Member

    bot spam sms và call
 
 ᴘʜᴏɴᴇ 📞:
   ├─> {masked_phone_number} 
   ├─────────────⭔
 ᴛɪᴍᴇ ⏰:
   ├─> {time_str} 
   ├─────────────⭔
 ᴄᴏᴏʟᴅᴏᴡɴ 👾:
   ├─> 120
   ├─────────────⭔
 ᴀᴅᴍɪɴ:
   ├─> ʜɴᴛ ᴛᴏᴏʟ
   └─────────────⭔

    '''
            mention = Mention(author_id, length=len("@Member"), offset=0)
            color_green = MessageStyle(style="color", color="#34bdeb", length=300, offset=0, auto_format=False)
            style = MultiMsgStyle([color_green])
            sms_img = "sms.png"
            self.replyMessage(Message(text=msg_content, style=style, mention=mention), message_object, thread_id=thread_id, thread_type=thread_type)
        
        if message.startswith("tb"):
	        if author_id not in idadmin:
	            self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
	            return
	        parts = message.split(' ', 1)
	        if len(parts) < 2:
	            self.replyMessage(Message(text='🚫 Vui lòng cung cấp nội dung.'), message_object, thread_id=thread_id, thread_type=thread_type)
	            return
	
	        success_text = parts[1] 
	        style_success = MultiMsgStyle([
	            MessageStyle(offset=0, length=min(10, len(success_text)), style="color", color="#ffcc00", auto_format=False),  # First 10 characters in yellow
	            MessageStyle(offset=10, length=min(10, len(success_text)-10), style="color", color="#28a745", auto_format=False),  # Next 10 characters in green
	            MessageStyle(offset=20, length=min(7, len(success_text)-20), style="color", color="#007bff", auto_format=False),  # Last 7 characters in blue
	        ])
	
	        
	        mention = Mention(uid='-1', offset=0, length=0)  
	
	        
	        self.send(
	            Message(text=success_text, mention=mention, style=style_success),
	            thread_id=thread_id,
	            thread_type=thread_type
	        )
	        return
        
        
        if message.startswith(".rs"):
        	
            parts = message.split(' ', 1)
            if len(parts) < 2:
                self.replyMessage(Message(text='🚫 Vui lòng cung cấp nội dung để phản hồi!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            content_to_reply = parts[1]          
            mention = Mention(uid=author_id, offset=0, length=len(content_to_reply))
            reply_message = Message(text=content_to_reply, mention=mention)
            self.replyMessage(reply_message, message_object, thread_id=thread_id, thread_type=thread_type)
            return
        if message.startswith(".dltt"):
            parts = message.split(" ")
            if len(parts) != 2:
                self.replyMessage(Message(text='🚫 Vui lòng cung cấp đường dẫn video TikTok.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            video_url = parts[1]
            self.download_tiktok_video(video_url, message_object, thread_id, thread_type)
        if message.startswith(".info"):
            self.replyMessage(Message(text=f'ID của bạn: {author_id}'), message_object, thread_id=thread_id, thread_type=thread_type)
        if message.startswith(".gr"):
            self.replyMessage(Message(text=f'ID nhóm của bạn: {thread_id}'), message_object, thread_id=thread_id, thread_type=thread_type)
        
    
        
        if message.startswith(".ghepdoi"):
            mentions = message_object.mentions
            if len(mentions) < 2:
                self.replyMessage(Message(text='🚫 Vui lòng đề cập đến hai người dùng.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            user_id_1 = mentions[0]['uid']
            user_name_1 = mentions[0]['name']  
            user_id_2 = mentions[1]['uid']
            user_name_2 = mentions[1]['name']  

            
            compatibility_percentage = random.randint(0, 100)

            
            if compatibility_percentage < 50:
                response = f"❤️ {user_name_1} và {user_name_2} không hợp nhau lắm đâu! Tỷ lệ hợp nhau chỉ {compatibility_percentage}%. ❤️"
            elif compatibility_percentage >= 50 and compatibility_percentage < 80:
                response = f"❤️ {user_name_1} và {user_name_2} hợp nhau đấy! Tỷ lệ hợp nhau là {compatibility_percentage}%. ❤️"
            else:  
                response = f"❤️ {user_name_1} và {user_name_2} hoàn hảo cho nhau! Tỷ lệ hợp nhau lên tới {compatibility_percentage}%. ❤️"

            
            private_message_1 = Message(text=response)
            private_message_2 = Message(text=response)

            self.send(private_message_1, thread_id=user_id_1, thread_type=ThreadType.USER)
            self.send(private_message_2, thread_id=user_id_2, thread_type=ThreadType.USER)
        if message.startswith(".gay"):
            if not message_object.mentions:
                self.replyMessage(Message(text='🚫 Vui lòng đề cập đến một người dùng.'), message_object, thread_id=thread_id, thread_type=thread_id)
            else:
                user_id = message_object.mentions[0]['uid']
                probability = random.randint(0, 100)  
                response = f"Khả năng <@{user_id}> bị gay là {probability}%."
                mention = Mention(user_id, length=len(f"<@{user_id}>"), offset=response.index(f"<@{user_id}>"))
                self.replyMessage(Message(text=response, mention=mention), message_object, thread_id=thread_id, thread_type=thread_type)
        if message.startswith(".cannang"):
            if not message_object.mentions:
                self.replyMessage(Message(text='🚫 Vui lòng đề cập đến một người dùng.'), message_object, thread_id=thread_id, thread_type=thread_type)
            else:
                user_id = message_object.mentions[0]['uid']
                weight = random.randint(30, 100)  

                if weight < 50:
                    response = f"Cân nặng của <@{user_id}> là {weight} kg - Gầy."
                else:
                    response = f"Cân nặng của <@{user_id}> là {weight} kg - Mập."

                mention = Mention(user_id, length=len(f"<@{user_id}>"), offset=response.index(f"<@{user_id}>"))
                self.replyMessage(Message(text=response, mention=mention), message_object, thread_id=thread_id, thread_type=thread_type)

            
        if message.startswith(".mau"):
            parts = message.split(' ', 1)
            if len(parts) < 2:
                self.replyMessage(Message(text='🚫 Vui lòng cung cấp nội dung cần tô màu.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            content_to_color = parts[1].strip()
            random_color = random.choice(self.color_list)  
            style = MultiMsgStyle([
                MessageStyle(offset=0, length=len(content_to_color), style="color", color=random_color, auto_format=False),
            ])
            self.replyMessage(Message(text=content_to_color, style=style), message_object, thread_id=thread_id, thread_type=thread_type)
        
        if message.startswith(".reo"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            if self.reo_spamming:  
                self.replyMessage(Message(text='🚫 Reo spam đã chạy!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            mentions = message_object.mentions
            if not mentions:
                self.replyMessage(Message(text='🚫 Bạn cần đề cập một người dùng.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            mentioned_user_id = mentions[0]['uid']

            self.reo_spamming = True
            self.reo_spam_thread = threading.Thread(target=self.reo_spam_message, args=(mentioned_user_id, thread_id, thread_type))
            self.reo_spam_thread.start()

        if message.startswith(".stopreo"):
            if not self.reo_spamming:
                self.replyMessage(Message(text='🚫 Không có spam nào đang chạy!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            self.reo_spamming = False
            if self.reo_spam_thread is not None:
                self.reo_spam_thread.join()
            self.replyMessage(Message(text='✅ Đã dừng spam reo.'), message_object, thread_id=thread_id, thread_type=thread_type)
        
        
        if message.startswith(".anime"):
            #if author_id not in idadmin:
                #self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                #return
            try:
                response = requests.get("https://www.pinterest.com/trangthuthu/%E1%BA%A3nh-anime-%C4%91%E1%BA%B9p/")
                response.raise_for_status()

                image_data = response.json()
                image_url = image_data.get('url', '')

                if image_url:
                    image_response = requests.get(image_url)
                    
                    if image_response.status_code == 200:
                        image_filename = 'temp_anime_image.jpeg'
                        with open(image_filename, 'wb') as image_file:
                            image_file.write(image_response.content)

                        self.sendLocalImage(image_filename, thread_id=thread_id, thread_type=thread_type)

                        success_text = "Tải ảnh thành công!"
                        style_success = MultiMsgStyle([
                            MessageStyle(offset=0, length=len(success_text), style="color", color="#00ff00", auto_format=False), 
                        ])
                        self.replyMessage(Message(text=success_text, style=style_success), message_object, thread_id=thread_id, thread_type=thread_type)

                        os.remove(image_filename)
                    else:
                        error_text = "🚫 Không thể tải hình ảnh, vui lòng thử lại sau."
                        style_error = MultiMsgStyle([
                            MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),  
                        ])
                        self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)
                else:
                    error_text = "🚫 Không tìm thấy hình ảnh."
                    style_error = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),  
                    ])
                    self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)

            except requests.exceptions.RequestException as e:
                error_text = f"🚫 Lỗi khi gọi API: {e}"
                style_error = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),  
                ])
                self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)
            except Exception as e:
                error_text = f"🚫 Đã xảy ra lỗi: {e}"
                style_error = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),  
                ])
                self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)
                
        
            

            
        if message.startswith(".vip"):
            if author_id not in idadmin:
                noquyen = "🚫 Đang updater ."
                self.replyMessage(Message(text=noquyen), message_object, thread_id, thread_type)
                return
            
            try:
                sdt = message.split(" ")[1] 
                for _ in range(5):  
                    self.popeyes(sdt)
                self.replyMessage(Message(text=f"Đang tấn công  {sdt} !"), message_object, thread_id, thread_type)
            except IndexError:
                self.replyMessage(Message(text="Vui lòng nhập số điện thoại hợp lệ sau lệnh .vip"), message_object, thread_id, thread_type)
            return
        
        
        if message.startswith(".reo"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            if self.reo_spamming:  
                self.replyMessage(Message(text='🚫 Reo spam đã chạy!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            mentions = message_object.mentions
            if not mentions:
                self.replyMessage(Message(text='🚫 Bạn cần đề cập một người dùng.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            mentioned_user_id = mentions[0]['uid']

            self.reo_spamming = True
            self.reo_spam_thread = threading.Thread(target=self.reo_spam_message, args=(mentioned_user_id, thread_id, thread_type))
            self.reo_spam_thread.start()

        if message.startswith(".stopreo"):
        	
            if not self.reo_spamming:
                self.replyMessage(Message(text='🚫 Không có spam nào đang chạy!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            self.reo_spamming = False
            if self.reo_spam_thread is not None:
                self.reo_spam_thread.join()
            self.replyMessage(Message(text='✅ Đã dừng spam reo.'), message_object, thread_id=thread_id, thread_type=thread_type)

        if message_text.startswith("checkon"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sài lệnh này.'), message_object, thread_id, thread_type)
                return

            self.banned_word_removal_enabled = True
            self.replyMessage(Message(text="Chức năng đã được bật!"), message_object, thread_id, thread_type)

        elif message_text.startswith("checkoff"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sài lệnh này.'), message_object, thread_id, thread_type)
                return

            self.banned_word_removal_enabled = False
            self.replyMessage(Message(text="Chức năng đã được tắt!"), message_object, thread_id, thread_type)

        if getattr(self, 'banned_word_removal_enabled', False):  
            cleaned_message = self.remove_banned_words(message_text)
            if cleaned_message != message_text:           
                self.replyMessage(Message(text="=)"), message_object, thread_id, thread_type)

                self.deleteGroupMsg(message_object.msgId, message_object.uidFrom, message_object.cliMsgId, thread_id)
                print("Tin nhắn đã bị xóa do chứa từ cấm.")

    



        
        if self.isUndoLoop:
            if author_id in idadmin:
                return
            mutenguoidung = self.load_mutenguoidung()
            if author_id in mutenguoidung:
                self.deleteGroupMsg(msgId=message_object.msgId, clientMsgId=message_object.cliMsgId, ownerId=author_id, groupId=thread_id)

        
        

        
                

            
        
            
            
        
    
    

        if message.startswith("All"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            success_text = "carrot đẹp trai - success - hehe"
            style_success = MultiMsgStyle([
                MessageStyle(offset=0, length=10, style="color", color="#ffcc00", auto_format=False),  
                MessageStyle(offset=10, length=10, style="color", color="#28a745", auto_format=False),  
                MessageStyle(offset=20, length=7, style="color", color="#007bff", auto_format=False),  
            ])

            mention = Mention(uid='-1', offset=0, length=0)
            self.send(Message(text=success_text, mention=mention, style=style_success), thread_id=thread_id, thread_type=thread_type)

        if message.startswith(".ask"):
            parts = message.split(' ', 1)
            if len(parts) < 2:
                error_text = "🚫 Vui Lòng nhập nội dung😒."
                style_error = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(error_text), style="font", size="14", auto_format=False),
                    MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),
                ])
                self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            user_message = parts[1]
            response = self.ask_api(user_message)
            
            style_response = MultiMsgStyle([
                MessageStyle(offset=0, length=6, style="color", color="#00ff00", auto_format=False),
                MessageStyle(offset=6, length=len(response), style="font", size="14", auto_format=False),
            ])

            self.replyMessage(Message(text=f"Response: {response}", style=style_response), message_object, thread_id=thread_id, thread_type=thread_type)
 
        if message.startswith(".uptime"):
            current_time = datetime.datetime.now()
            uptime = current_time - self.start_time
            days, seconds = uptime.days, uptime.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60

            start_time_str = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
            
            uptime_message = (
                f"Bot đã hoạt động được {days} ngày, {hours} giờ, {minutes} phút, {seconds} giây.\n"
                f"Khởi động từ: {start_time_str}"
            )
            
            style_uptime = MultiMsgStyle([
                MessageStyle(offset=0, length=21, style="font", size="14", auto_format=False),
                MessageStyle(offset=21, length=len(uptime_message) - 21, style="color", color="#2196f3", auto_format=False),
            ])

            self.replyMessage(Message(text=uptime_message, style=style_uptime), message_object, thread_id=thread_id, thread_type=thread_type)

                    
                    
             
        if message.startswith(".sexy"):
   
            #if author_id not in idadmin:
                #self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                #return

            try:
                response = requests.get("https://api.sumiproject.net/video/girlsexy")
                response.raise_for_status()

                image_data = response.json()
                image_url = image_data.get('url', '')

                if image_url:
                    image_response = requests.get(image_url)
                    
                    if image_response.status_code == 200:
                        image_filename = 'temp_du_image.jpeg'
                        with open(image_filename, 'wb') as image_file:
                            image_file.write(image_response.content)

                        self.sendLocalImage(image_filename, thread_id=thread_id, thread_type=thread_type)

                        success_text = "Tải ảnh thành công!"
                        style_success = MultiMsgStyle([
                            MessageStyle(offset=0, length=len(success_text), style="color", color="#00ff00", auto_format=False),  
                        ])
                        self.replyMessage(Message(text=success_text, style=style_success), message_object, thread_id=thread_id, thread_type=thread_type)

                        os.remove(image_filename)
                    else:
                        error_text = "🚫 Không thể tải hình ảnh, vui lòng thử lại sau."
                        style_error = MultiMsgStyle([
                            MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),  
                        ])
                        self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)
                else:
                    error_text = "🚫 Không tìm thấy hình ảnh."
                    style_error = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False), 
                    ])
                    self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)

            except requests.exceptions.RequestException as e:
                error_text = f"🚫 Lỗi khi gọi API: {e}"
                style_error = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),  
                ])
                self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)
            except Exception as e:
                error_text = f"🚫 Đã xảy ra lỗi: {e}"
                style_error = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False), 
                ])
                self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)

        if message.startswith(".du"):
            #if author_id not in idadmin:
                #self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                #return
            try:
                response = requests.get("https://api.sumiproject.net/images/du")
                response.raise_for_status()

                image_data = response.json()
                image_url = image_data.get('url', '')

                if image_url:
                    image_response = requests.get(image_url)
                    
                    if image_response.status_code == 200:
                        image_filename = 'temp_du_image.jpeg'
                        with open(image_filename, 'wb') as image_file:
                            image_file.write(image_response.content)

                        self.sendLocalImage(image_filename, thread_id=thread_id, thread_type=thread_type)

                        success_text = "Tải ảnh thành công!"
                        style_success = MultiMsgStyle([
                            MessageStyle(offset=0, length=len(success_text), style="color", color="#00ff00", auto_format=False), 
                        ])
                        self.replyMessage(Message(text=success_text, style=style_success), message_object, thread_id=thread_id, thread_type=thread_type)

                        os.remove(image_filename)
                    else:
                        error_text = "🚫 Không thể tải hình ảnh, vui lòng thử lại sau."
                        style_error = MultiMsgStyle([
                            MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),  
                        ])
                        self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)
                else:
                    error_text = "🚫 Không tìm thấy hình ảnh."
                    style_error = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),  
                    ])
                    self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)

            except requests.exceptions.RequestException as e:
                error_text = f"🚫 Lỗi khi gọi API: {e}"
                style_error = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),  
                ])
                self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)
            except Exception as e:
                error_text = f"🚫 Đã xảy ra lỗi: {e}"
                style_error = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),  
                ])
                self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)

        if message.startswith(".du"):
            #if author_id not in idadmin:
                #self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                #return
            try:
                response = requests.get("https://api.sumiproject.net/images/du")
                response.raise_for_status()

                image_data = response.json()
                image_url = image_data.get('url')

                if image_url:
                    image_response = requests.get(image_url)
                    
                    if image_response.status_code == 200:
                        image_filename = 'temp_du_image.jpeg'
                        with open(image_filename, 'wb') as image_file:
                            image_file.write(image_response.content)

                        self.sendLocalImage(image_filename, thread_id=thread_id, thread_type=thread_type)

                        
                        success_text = "Tải ảnh thành công!"
                        style_success = MultiMsgStyle([
                            MessageStyle(offset=0, length=len(success_text), style="color", color="#00ff00", auto_format=False),  
                        ])
                        self.replyMessage(Message(text=success_text, style=style_success), message_object, thread_id=thread_id, thread_type=thread_type)

                        os.remove(image_filename)
                    else:
                        
                        error_text = "🚫 Không thể tải hình ảnh, vui lòng thử lại sau."
                        style_error = MultiMsgStyle([
                            MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),  
                        ])
                        self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)
                else:
                
                    error_text = "🚫 Không tìm thấy hình ảnh."
                    style_error = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False), 
                    ])
                    self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)

            
                error_text = f"🚫 Lỗi khi gọi API: {e}"
                style_error = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),
                ])
                self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)
            except Exception as e:
                
                error_text = f"🚫 Đã xảy ra lỗi không mong muốn: {e}"
                style_error = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False),  
                ])
                self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)

        if message.startswith(".anh"):
            #if author_id not in idadmin:
                #self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                #return
            try:
                response = requests.get("https://luv.vn/hinh-anh-gai-xinh/")
                response.raise_for_status()

                image_data = response.json()
                image_url = image_data.get('url')

                if image_url:
                    img_response = requests.get(image_url)
                    img_response.raise_for_status()

                    img_filename = 'temp_image.jpg'
                    with open(img_filename, 'wb') as img_file:
                        img_file.write(img_response.content)

                    self.sendLocalImage(img_filename, thread_id=thread_id, thread_type=thread_type)

                    
                    success_text = "Ảnh đã được tải lên!"
                    style_success = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(success_text), style="color", color="#00BFFF", auto_format=False),  
                    ])
                    self.replyMessage(Message(text=success_text, style=style_success), message_object, thread_id=thread_id, thread_type=thread_type)

                    os.remove(img_filename)
                else:
                   
                    error_text = "🚫 Không tìm thấy ảnh."
                    style_error = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(error_text), style="color", color="#ff5555", auto_format=False), 
                    ])
                    self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)

            except requests.exceptions.RequestException as e:
                
                error_text = f"🚫 Lỗi khi gọi API: {e}"
                style_error = MultiMsgStyle([
                ])
                self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)
            except Exception as e:
               
                error_text = f"🚫 Đã xảy ra lỗi: {e}"
                style_error = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(error_text), style="color", color="#00BFFF", auto_format=False),  
                ])
                self.replyMessage(Message(text=error_text, style=style_error), message_object, thread_id=thread_id, thread_type=thread_type)
        if message.startswith("/menu"):
            menu_text = (
                "Danh sách lệnh:\n"
                "• .spam <nội dung>: Bắt đầu spam nội dung.\n"
                "• .nhay: Bắt đầu spam nội dung từ file content.txt.\n"
                "• .stop: Dừng spam.\n"
                "• .del: Xóa các tin nhắn chứa link.\n"
                "• All: Tag ẩn kèm nội dung.\n"
                "• .on : Xóa tất cả tin nhắn sau khi lệnh được sử dụng.\n"
                "• .off: Tắt chế độ xóa tin nhắn.\n"
                "• .admin <user_id>: Thêm người dùng vào admin.\n"
                "• .list: Xem danh sách admin.\n"
                "• .info: Xem ID của người dùng.\n"
                "• .kick @user: Đuổi người dùng khỏi nhóm.\n"
                "• .ask: Trao đổi tin nhắn với bot.\n"
                "• .uptime: Xem thời gian khởi tạo bot.\n"
                "• .anh: Tải ảnh lên.\n"
                "• .anime: Tải ảnh anime.\n"
                "• mute hoăc mu: Mute một thành viên.\n"
                "• un: Gỡ mute.\n"
                "• .du: Xem ảnh du.\n"
                "• .sexy: Xem ảnh sexy.\n"
                "• vip:số điện thoại.\n"
                "• checkon:bật chế độ cấm tục.\n"
                "• checkoff: tắt chế độ cấm tục.\n"
                " • .random + số lượng: random acc golike(newly updated ).\n"
                " • .acclq + số lượng(1>=10): random acc liên quân(newly updated ).\n"
                " • .id + idtiktok: xem thông tin nick (newly updated ).\n"
                " • .reo + @metion:spam metion (newly updated ).\n"
                " • .vip sdt : spamvip (maintenance ).\n"
                "• .reo @metion tag metion liên tục.\n"
                "• .stopreo ngừng spam người đó chỉnh delay để nhận lệnh nhanh hơn.\n"
                "• .cannang @metion xem cân nặng người đó\n"
                "• .gay @metion xem độ gay người đó.\n"
                "• .ghepdoi @metion 1 và @metion:xem độ phụ hợp>\n"
                " • .dltt linkvstiktok\n"
                "• .tb tag all với thông báo.\n"
                "• .rs nội dung tag chính bản thân mình.\n"
                "• game chơi game.,\n"
                "• .dt đổi tên nhóm.\n"
                ".call <id nhóm>:spam call nhóm mình ghét "
            )            
            style_menu = MultiMsgStyle([
                MessageStyle(offset=0, length=15, style="font", size="14", auto_format=False),
                MessageStyle(offset=16, length=len(menu_text) - 16, style="font", size="12", auto_format=False),
                MessageStyle(offset=0, length=len(menu_text), style="color", color="#4caf50", auto_format=False),
            ])          
            self.replyMessage(
                Message(
                    text=menu_text,
                    style=style_menu
                ),
                message_object,
                thread_id=thread_id,
                thread_type=thread_type
            )
        
        elif message.startswith(".id"):
            parts = message.split(maxsplit=1)  
            if len(parts) == 2:
                tiktok_username = parts[1].strip()  
                api_url = f"https://api.sumiproject.net/tiktok?info={tiktok_username}"

                try:
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        data = response.json()

                        if 'data' in data and 'user' in data['data']:
                            
                            user_info = (
                                f"Thông tin TikTok:\n"
                                f"- Nickname: {data['data']['user']['nickname']}\n"
                                f"- Followers: {data['data']['stats']['followerCount']}\n"
                                f"- Following: {data['data']['stats']['followingCount']}\n"
                                f"- Videos: {data['data']['stats']['videoCount']}\n"
                                f"- Heart Count: {data['data']['stats']['heartCount']}\n"
                                f"- Signature: {data['data']['user']['signature']}"
                            )
                            self.replyMessage(
                                Message(text=user_info),
                                message_object,
                                thread_id=thread_id,
                                thread_type=thread_type
                            )
                        else:
                            self.replyMessage(
                                Message(text="Không tìm thấy thông tin cho người dùng TikTok này."),
                                message_object,
                                thread_id=thread_id,
                                thread_type=thread_type
                            )
                    else:
                        self.replyMessage(
                            Message(text="Lỗi khi truy cập API TikTok."),
                            message_object,
                            thread_id=thread_id,
                            thread_type=thread_type
                        )
                except Exception as e:
                    self.replyMessage(
                        Message(text="Đã xảy ra lỗi khi lấy thông tin TikTok."),
                        message_object,
                        thread_id=thread_id,
                        thread_type=thread_type
                    )
                    print(f"Lỗi khi xử lý lệnh .id: {e}")
            else:
                
                self.replyMessage(
                    Message(text="Sai cú pháp! Vui lòng sử dụng: .id <tiktok_username>"),
                    message_object,
                    thread_id=thread_id,
                    thread_type=thread_type
                )
        
        if message.startswith(".admin"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            parts = message.split(' ', 1)
            if len(parts) < 2:
                self.replyMessage(Message(text='🚫 Vui lòng cung cấp user_id để thêm làm admin.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            new_admin_id = parts[1]
            idadmin.add(new_admin_id)
            self.save_admins(idadmin)
            self.replyMessage(Message(text=f'Đã thêm {new_admin_id} vào danh sách admin.'), message_object, thread_id=thread_id, thread_type=thread_type)

        if message.startswith(".list"):
            admin_list = "\n".join(idadmin)
            self.replyMessage(Message(text=f'Danh sách admin:\n{admin_list}'), message_object, thread_id=thread_id, thread_type=thread_type)

        
        if message.startswith(".del"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            self.delete_links = not self.delete_links
            status = "Bật" if self.delete_links else "Tắt"
            self.replyMessage(Message(text=f'✅ Đã {status} chế độ xóa liên kết.'), message_object, thread_id=thread_id, thread_type=thread_type)

        

        if message.startswith(".spam"):
            if author_id not in idadmin:
                self.replyMessage(Message(text=' Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            if self.spamming:
                self.replyMessage(Message(text='🚫 Spam đang chạy!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            parts = message.split(' ', 1)
            if len(parts) < 2:
                self.replyMessage(Message(text='🚫 Vui lòng cung cấp nội dung đi chứ Admin'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            spam_content = parts[1]
            self.spamming = True
            self.spam_thread = threading.Thread(target=self.spam_message, args=(spam_content, thread_id, thread_type))
            self.spam_thread.start()

        if message.startswith(".nhay"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            if self.spamming:
                self.replyMessage(Message(text='🚫 Spam đang chạy!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            try:
                with open('content.txt', 'r', encoding='utf-8') as file:
                    spam_content = file.read()
            except FileNotFoundError:
                self.replyMessage(Message(text='🚫 Không tìm thấy file content.txt.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            self.spamming = True
            self.spam_thread = threading.Thread(target=self.spam_message, args=(spam_content, thread_id, thread_type))
            self.spam_thread.start()

        if message.startswith(".stop"):
            if not self.spamming:
                self.replyMessage(Message(text='🚫 Không có spam nào đang chạy!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            self.spamming = False
            if self.spam_thread is not None:
                self.spam_thread.join()
            self.replyMessage(Message(text='✅ Đã dừng spam.'), message_object, thread_id=thread_id, thread_type=thread_type)

        if message.startswith(".on"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            self.xoatn_mode = True
            self.replyMessage(Message(text='Im lặng là vàng các e đã bị cấm chat!🤫.'), message_object, thread_id=thread_id, thread_type=thread_type)

        if message.startswith(".off"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            self.xoatn_mode = False
            self.messages_to_delete.clear()
            self.replyMessage(Message(text='Đã tắt chế độ xóa tin nhắn.'), message_object, thread_id=thread_id, thread_type=thread_type)

        if message.startswith(".kick"):
            self.handle_kick(message_object, thread_id, author_id, thread_type)
            
        elif message.startswith("Mute") or message.startswith("mu") or message.startswith(" ") or "mute" in message.lower():
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sài lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            mutenguoidung = self.load_mutenguoidung()
            if message_object.mentions and len(message_object.mentions) > 0:
                user_id = message_object.mentions[0]['uid']
                mention = Mention(user_id, length=8, offset=12)
                self.replyMessage(
                    Message(
                        text="Nín Họng Đi @TagName", mention=mention
                    ),
                    message_object,
                    thread_id=thread_id,
                    thread_type=thread_type
                )
            else:
                user_id = author_id
                self.replyMessage(
                    Message(
                        text="Bạn Đã Tự Hủy🗿"
                    ),
                    message_object,
                    thread_id=thread_id,
                    thread_type=thread_type
                )
            if user_id not in mutenguoidung:
                mutenguoidung.add(user_id)
                self.save_mutenguoidung(mutenguoidung)
            self.isUndoLoop = True

        
        elif message.startswith("unmute") or "unmute" in message.lower():
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sài lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            mutenguoidung = self.load_mutenguoidung()
            if message_object.mentions and len(message_object.mentions) > 0:
                user_id = message_object.mentions[0]['uid']
                mention = Mention(user_id, length=8, offset=12)
                self.replyMessage(
                    Message(
                        text="Đã hủy câm lặng cho @TagName", mention=mention
                    ),
                    message_object,
                    thread_id=thread_id,
                    thread_type=thread_type
                )
            else:
                user_id = author_id
                self.replyMessage(
                    Message(
                        text="Bạn đã tự mở khóa câm lặng"
                    ),
                    message_object,
                    thread_id=thread_id,
                    thread_type=thread_type
                )
            if user_id in mutenguoidung:
                mutenguoidung.remove(user_id)
                self.save_mutenguoidung(mutenguoidung)
            self.isUndoLoop = False
        
            
   
        
        if self.xoatn_mode:
            self.messages_to_delete.append(message_object)

        list_link = ["t.me/", "https://", "http://", "https://zalo.me/g/", "zalo.me/g/", "zalo.me", "https://t.me/", "chinhphu.vn", "edu.vn", "gov.vn", "edu.gov.vn", "youtube", "tiktok", "https://www.youtube.com/"]

        if self.delete_links and any(link in message for link in list_link):
            try:
                self.deleteGroupMsg(
                    msgId=message_object.msgId, 
                    clientMsgId=message_object.cliMsgId, 
                    ownerId=author_id, 
                    groupId=thread_id
                )
            except Exception as e:
                print(f'Error deleting message: {e}')
        
        if self.xoatn_mode and self.messages_to_delete:
            for msg_obj in self.messages_to_delete:
                try:
                    self.deleteGroupMsg(
                        msgId=msg_obj.msgId, 
                        clientMsgId=msg_obj.cliMsgId, 
                        ownerId=author_id, 
                        groupId=thread_id
                    )
                except Exception as e:
                    print(f'Error deleting message: {e}')
            self.messages_to_delete.clear()
        if message.startswith("game"):
            menu_text = (
                "ᴅᴀɴʜ ꜱᴀ́ᴄʜ ʟᴇ̣̂ɴʜ:\n"
                        "• .ᴅᴀɴɢᴋʏ ɴᴀᴍᴇ: Đăng ký với tên và nhận 500 triệu.\n"
                        "• .ɢᴀᴍᴇ ᴛ/x/ᴄ/ʟ số tiền: Tham gia game.\n"
                        "• .ᴄᴛ tên số tiền: Chuyển tiền cho người khác.\n"
                        "• .ᴄᴏᴅᴇ mã số tiền: Nhập mã code.\n"
                        "• .ꜱᴏᴅᴜ: Xem số dư.\n"
                        "• .ᴀᴅᴍɪɴ key: Trở thành admin.\n"
                        "• .ʙᴜꜰꜰ tên: Buff vô hạn tiền cho người khác (admin).\n"
                        "• .ɴᴏɴᴇ ɴᴀᴍᴇ ꜱᴏ̂́ ᴛɪᴇ̂̀ɴ:ʙᴜꜰꜰ ᴛɪᴇ̂̀ɴ ɴᴏᴏʙ.\n"
            )            
            style_menu = MultiMsgStyle([
                MessageStyle(offset=0, length=15, style="font", size="14", auto_format=False),
                MessageStyle(offset=16, length=len(menu_text) - 16, style="font", size="12", auto_format=False),
                MessageStyle(offset=0, length=len(menu_text), style="color", color="#4caf50", auto_format=False),
            ])          
            self.replyMessage(
                Message(
                    text=menu_text,
                    style=style_menu
                ),
                message_object,
                thread_id=thread_id,
                thread_type=thread_type
            )
        
        elif message.startswith(".dangky"):
            user_name = message[len(".dangky "):].strip()
            if not user_name:
                self.replyMessage(Message(text='🚫 Bạn cần cung cấp tên để đăng ký.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            registered_users = self.load_registered_users()

            if author_id in registered_users:
                self.replyMessage(Message(text='🚫 Bạn đã đăng ký rồi!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            self.save_registered_user(author_id, user_name)
            self.replyMessage(Message(text=f'✅ Đăng ký thành công! Bạn đã được tặng 500 triệu!'), message_object, thread_id=thread_id, thread_type=thread_type)

        elif message.startswith(".code"):
            args = message.split()
            if len(args) != 3:
                self.replyMessage(Message(text='🚫 Vui lòng nhập đúng cú pháp: .code <mã> <số tiền>'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            code = args[1].upper()
            try:
                amount = int(args[2])
            except ValueError:
                self.replyMessage(Message(text='🚫 Số tiền không hợp lệ!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            if code in self.codes and self.codes[code] == amount:
                registered_users = self.load_registered_users()
                if author_id in registered_users:
                    user_name, balance = registered_users[author_id]
                    new_balance = balance + amount
                    self.update_user_balance(author_id, new_balance)
                    self.replyMessage(Message(text=f'✅ Bạn đã nhập mã {code} thành công và nhận được {amount}! Số dư mới của bạn: {new_balance}'), message_object, thread_id=thread_id, thread_type=thread_type)
                else:
                    self.replyMessage(Message(text='🚫 Bạn cần đăng ký trước khi nhập mã.'), message_object, thread_id=thread_id, thread_type=thread_type)
            else:
                self.replyMessage(Message(text='🚫 Mã không hợp lệ hoặc số tiền không đúng!'), message_object, thread_id=thread_id, thread_type=thread_type)

        elif message.startswith(".game"):
            registered_users = self.load_registered_users()
            if author_id not in registered_users:
                self.replyMessage(Message(text='🚫 Bạn cần đăng ký trước khi chơi game.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            args = message.split()
            if len(args) != 3:
                self.replyMessage(Message(text='🚫 Vui lòng nhập đúng cú pháp: .game <T/X/C/L> <số tiền>'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            bet_type = args[1].upper()
            try:
                bet_amount = int(args[2])
            except ValueError:
                self.replyMessage(Message(text='🚫 Số tiền cược không hợp lệ!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            if bet_amount <= 0:
                self.replyMessage(Message(text='🚫 Số tiền cược phải lớn hơn 0.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            users_balance = registered_users[author_id][1]
            if users_balance < bet_amount:
                self.replyMessage(Message(text='🚫 Bạn không đủ tiền để cược!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            dice_results = [random.randint(1, 6) for _ in range(3)]
            total = sum(dice_results)
            is_even = total % 2 == 0
            win_condition = (bet_type == 'T' and total > 10) or (bet_type == 'X' and total < 11) or \
                            (bet_type == 'C' and is_even) or (bet_type == 'L' and not is_even)

            if win_condition:
                result_text = "chẵn" if is_even else "lẻ"
                self.replyMessage(Message(text=f'🎉 Chúc mừng! Bạn đã thắng! Kết quả: {dice_results} = {total} ({result_text}). Bạn nhận được {bet_amount} tiền!'), message_object, thread_id=thread_id, thread_type=thread_type)
                new_balance = users_balance + bet_amount
            else:
                result_text = "chẵn" if is_even else "lẻ"
                self.replyMessage(Message(text=f'😢 Bạn đã thua! Kết quả: {dice_results} = {total} ({result_text}). Bạn mất {bet_amount} tiền!'), message_object, thread_id=thread_id, thread_type=thread_type)
                new_balance = users_balance - bet_amount

            self.update_user_balance(author_id, new_balance)

        elif message.startswith(".sodu"):
            registered_users = self.load_registered_users()
            if author_id not in registered_users:
                self.replyMessage(Message(text='🚫 Bạn chưa đăng ký!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            user_name, balance = registered_users[author_id]
            self.replyMessage(Message(text=f'💰 Số dư của bạn là: {balance}'), message_object, thread_id=thread_id, thread_type=thread_type)

        elif message.startswith(".ct"):
            registered_users = self.load_registered_users()
            if author_id not in registered_users:
                self.replyMessage(Message(text='🚫 Bạn chưa đăng ký!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            args = message.split()
            if len(args) != 3:
                self.replyMessage(Message(text='🚫 Vui lòng nhập đúng cú pháp: .ct <tên> <số tiền>'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            receiver_name = args[1]
            try:
                transfer_amount = int(args[2])
            except ValueError:
                self.replyMessage(Message(text='🚫 Số tiền không hợp lệ!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            if transfer_amount <= 0:
                self.replyMessage(Message(text='🚫 Số tiền phải lớn hơn 0.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            sender_name, sender_balance = registered_users[author_id]
            if sender_balance < transfer_amount:
                self.replyMessage(Message(text='🚫 Bạn không đủ tiền để chuyển!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            recipient_id = next((uid for uid, (name, _) in registered_users.items() if name == receiver_name), None)
            if not recipient_id:
                self.replyMessage(Message(text='🚫 Người nhận không tồn tại!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            recipient_name, recipient_balance = registered_users[recipient_id]
            new_sender_balance = sender_balance - transfer_amount
            new_recipient_balance = recipient_balance + transfer_amount

            self.update_user_balance(author_id, new_sender_balance)
            self.update_user_balance(recipient_id, new_recipient_balance)
            self.replyMessage(Message(text=f'✅ Chuyển tiền thành công! Bạn đã chuyển {transfer_amount} cho {recipient_name}. Số dư mới của bạn: {new_sender_balance}'), message_object, thread_id=thread_id, thread_type=thread_type)

        elif message.startswith(".key"):
            key = message[len(".key "):].strip()
            if key == self.admin_key:
                self.is_admin = True
                self.replyMessage(Message(text='🔐 Bạn đã trở thành admin!'), message_object, thread_id=thread_id, thread_type=thread_type)
            else:
                self.replyMessage(Message(text='🚫 Sai mật khẩu admin!'), message_object, thread_id=thread_id, thread_type=thread_type)

        elif message.startswith(".none"):
            if not self.is_admin:
                self.replyMessage(Message(text='🚫 Chỉ admin mới có thể sử dụng lệnh này!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            args = message.split()
            if len(args) != 3:
                self.replyMessage(Message(text='🚫 Vui lòng nhập đúng cú pháp: .buff <tên> <số tiền>'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            receiver_name = args[1]
            try:
                buff_amount = int(args[2])
            except ValueError:
                self.replyMessage(Message(text='🚫 Số tiền không hợp lệ!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            if buff_amount <= 0:
                self.replyMessage(Message(text='🚫 Số tiền phải lớn hơn 0.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            registered_users = self.load_registered_users()
            recipient_id = next((uid for uid, (name, _) in registered_users.items() if name == receiver_name), None)
            if not recipient_id:
                self.replyMessage(Message(text='🚫 Người nhận không tồn tại!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            recipient_name, recipient_balance = registered_users[recipient_id]
            new_recipient_balance = recipient_balance + buff_amount
            self.update_user_balance(recipient_id, new_recipient_balance)
            self.replyMessage(Message(text=f'✅ Buff tiền thành công! Bạn đã buff {buff_amount} cho {recipient_name}. Số dư mới của {recipient_name}: {new_recipient_balance}'), message_object, thread_id=thread_id, thread_type=thread_type)


        elif message.startswith(".buff"):
            if not self.is_admin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này!'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            args = message.split()
            if len(args) != 2:
                self.replyMessage(Message(text='🚫 Vui lòng nhập đúng cú pháp: .buff <tên>'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            user_name = args[1].strip()
            registered_users = self.load_registered_users()

            recipient_id = None
            for uid, (name, balance) in registered_users.items():
                if name.lower() == user_name.lower():
                    recipient_id = uid
                    break

            if recipient_id is None:
                self.replyMessage(Message(text=f'🚫 Không tìm thấy người dùng tên {user_name}.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return

            # ... (ngay sau khối lệnh .buff) ...

            self.update_user_balance(recipient_id, float('inf'))
            self.replyMessage(Message(text=f'✅ Đã buff tiền vô hạn cho người dùng {user_name}!'), message_object, thread_id=thread_id, thread_type=thread_type)
        
        
        
      # ... (ngay sau khối lệnh .buff) ...

           
       # ... (ngay sau khối lệnh .buff) ...

            self.update_user_balance(recipient_id, float('inf'))
            self.replyMessage(Message(text=f'✅ Đã buff tiền vô hạn cho người dùng {user_name}!'), message_object, thread_id=thread_id, thread_type=thread_type)
        
        # ==================================================
        # ===== LOGIC KÍCH HOẠT AI TỰ ĐỘNG =====
        # ==================================================
        try:
            # 1. Không trả lời tin nhắn của chính mình
            #    (self.uid được zlapi tự gán sau khi login)
            if author_id == self.uid:
                pass # Bỏ qua tin nhắn của chính bot

            else:
                # 2. Lọc các lệnh để AI không trả lời
                # (Lấy từ các lệnh trong file hhhh.py)
                command_prefixes = [
                    '.', '/', 'tb', 'all', 'mute', 'mu', 'unmute', 'game', 
                    'vip', 'sms', 'checkon', 'checkoff'
                ]
                
                is_command = False
                for prefix in command_prefixes:
                    if message_text.lower().startswith(prefix.lower()):
                        is_command = True
                        break
                
                # 3. Nếu không phải lệnh, gọi AI
                if not is_command:
                    command_content = ""
                    if message_text.lower().startswith("@lynk"): # Vẫn giữ tính năng tag
                        command_content = message_text[5:].strip() # Cắt "@Luynk"
                    else:
                        command_content = message_text # Tin nhắn thường
                    
                    if not command_content:
                        command_content = "Chào bạn" # Trả lời mặc định nếu rỗng
                    
                    # Gọi hàm AI đã thêm vào class
                    self.handle_ai_request(command_content, thread_id, thread_type, author_id, message_object)
                    
                    # Vì đã xử lý bằng AI, nên return để không chạy code xóa link/xóa tn bên dưới
                    return
        
        except Exception as e:
            print(f"Lỗi kích hoạt AI: {e}")
        
        # ==================================================
        # ===== KẾT THÚC LOGIC AI =====
        # ==================================================

       
       
    def send_private_message_to_user(self, user_id, random_data):
        """Gửi nội dung sau khi random từ file riêng tư đến người dùng."""
        try:
            message_text = f"thông tin nick:\n{random_data}"
            private_message = Message(text=message_text)
            self.send(private_message, thread_id=user_id, thread_type=ThreadType.USER)  
        except Exception as e:
            print(f"🚫 Lỗi khi gửi tin nhắn: {e}")
    
    def get_random_data(self, quantity):
        """Lấy ngẫu nhiên một số lượng dòng từ file gl.txt."""
        try:
            with open("gl.txt", "r", encoding="utf-8") as file:
                lines = file.readlines()
                if len(lines) < quantity:
                    return None  
                
                random_lines = random.sample(lines, quantity)
                return ''.join(random_lines)
        except FileNotFoundError:
            print("🚫 File gl.txt không tồn tại.")
            return None
        except Exception as e:
            print(f"🚫 Lỗi khi đọc file: {e}")
            return None
    #admin:Hồ nhật trường (X)
#xoá 3 comment này là chó
#siuuuuu

    def reo_spam_message(self, mentioned_user_id, thread_id, thread_type):
        """Spam mentions of a specific user."""
        while self.reo_spamming:
            mention = Mention(uid=mentioned_user_id, offset=0, length=5)
            spam_message = Message(text="@user", mention=mention)  
            self.send(spam_message, thread_id=thread_id, thread_type=thread_type)
            time.sleep(1)  
    def handle_kick(self, message_object, thread_id, author_id, thread_type):
        """Handle the .kick command to remove a user from the group."""
        idadmin = self.load_admins()
        if author_id not in idadmin:
            self.replyMessage(Message(text="🚫 Bạn không có quyền sử dụng lệnh này."), message_object, thread_id=thread_id, thread_type=thread_type)
            return

        mentions = getattr(message_object, 'mentions', None)
        if mentions:
            mentioned_user_id = mentions[0]['uid']
            if mentioned_user_id not in self.excluded_user_ids:
                try:
                    self.kickUsersFromGroup([mentioned_user_id], thread_id)
                    self.replyMessage(Message(text="thanh niên này qua xam lon nên bị kick."), message_object, thread_id=thread_id, thread_type=thread_type)
                except ZaloAPIException:
                    self.replyMessage(Message(text="🚫 Không thể đuổi người dùng."), message_object, thread_id=thread_id, thread_type=thread_type)
            else:
                self.replyMessage(Message(text="🚫 Không thể đuổi người dùng này."), message_object, thread_id=thread_id, thread_type=thread_type)
        else:
            self.replyMessage(Message(text="Nhập tên thằng gay muốn kick."), message_object, thread_id=thread_id, thread_type=thread_type)
    #admin:Hồ nhật trường (X)
#xoá 3 comment này là chó
#siuuuuu
    def ask_api(self, user_message):
        headers = {
            'Content-Type': 'application/json',
        }
        params = {
            'key': 'AIzaSyBDlktMVCY-M4gvxyw3f1yoQMa1mshgis0',  
        }
        json_data = {
            'contents': [
                {
                    'parts': [
                        {
                            'text': user_message,
                        },
                    ],
                },
            ],
        }

        try:
            response = requests.post(
                'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent',
                params=params,
                headers=headers,
                json=json_data,
            )
            response.raise_for_status()
            result = response.json()
            print("Phản hồi API:", result) 
            
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                content = candidate.get('content', {})
                parts = content.get('parts', [])
                if parts and 'text' in parts[0]:
                    return parts[0]['text']
                else:
                    return 'Không có phần nội dung trong phản hồi.'
            else:
                return 'Không có ứng viên nào trong phản hồi.'
        except requests.exceptions.RequestException as e:
            return f'Lỗi yêu cầu API: {e}'
        except Exception as e:
            return f'Đã xảy ra lỗi: {e}'

    def spam_message(self, spam_content, thread_id, thread_type):
        words = spam_content.split()
        while self.spamming:
            for word in words:
                if not self.spamming:
                    break
                mention = Mention(uid='-1', offset=0, length=len(word))
                spam_message = Message(text=word, mention=mention)
                self.send(spam_message, thread_id=thread_id, thread_type=thread_type)
                time.sleep(1)
    def remove_banned_words(self, message):
        cleaned_message = message
        for word in self.banned_words: 
            cleaned_message = cleaned_message.replace(word, "[censored]")
        return cleaned_message
    def add_to_spam_list(self, phone_number):
       
        url = f"https://thanhphucdev.net/api/thanhphuc.php?sdt={phone_number}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return f"✅ Added phone number {phone_number} to the spam list."
            else:
                return "🚫 Could not add phone number to the spam list."
        except requests.exceptions.RequestException as e:
            return f"🚫 Error: {str(e)}"
    def download_tiktok_video(self, video_url, message_object, thread_id, thread_type):
        """Download TikTok video and send details back to user."""
        api_url = f"https://subhatde.id.vn/tiktok/downloadvideo?url={video_url}"
        
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                self.replyMessage(Message(text='🚫 Không thể tải video. Vui lòng kiểm tra lại đường dẫn.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            
            video_data = data.get("data", {})
            title = video_data.get("title", "Không có tiêu đề")
            duration = video_data.get("duration", 0)
            play_url = video_data.get("play", "")
            cover_url = video_data.get("cover", "")
            music_info = video_data.get("music_info", {})
            music_title = music_info.get("title", "Không có tên nhạc")
            music_author = music_info.get("author", "Không có tác giả")
            download_url = play_url  

            message = (
                f"**Tiêu đề:** {title}\n"
                f"**Thời gian:** {duration} giây\n"
                f"**Link video:** {play_url}\n"
                f"**Đường dẫn tải video:** [Tải tại đây]({download_url})\n"  
                f"**Hình ảnh bìa:** {cover_url}\n"
                f"**Tên nhạc:** {music_title}\n"
                f"**Tác giả nhạc:** {music_author}"
            )
            self.replyMessage(Message(text=message), message_object, thread_id=thread_id, thread_type=thread_type)
        
        except requests.RequestException as e:
            print(f"Error fetching video: {e}")
            self.replyMessage(Message(text="🚫 Có lỗi khi lấy video."), message_object, thread_id=thread_id, thread_type=thread_type)
    # ... (sau hàm download_tiktok_video) ...

    # ... (sau hàm download_tiktok_video) ...

    # ==================================================
    # ===== CÁC HÀM AI ĐƯỢC THÊM TỪ AI.PY =====
    # ==================================================
    
    def get_history_file_path(self, thread_id, author_id):
        return os.path.join(self.HISTORY_DIR, f"{thread_id}_{author_id}.json")

    def load_history_from_file(self, file_path):
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Lỗi đọc file history: {e}")
                return []
        return []

    def save_history_to_file(self, file_path, history):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Lỗi lưu file history: {e}")

    def handle_ai_request(self, user_query, thread_id, thread_type, author_id, message_object):
        """Xử lý yêu cầu AI với lịch sử trò chuyện và persona"""
        
        history_key = (thread_id, author_id)
        file_path = self.get_history_file_path(thread_id, author_id)

        # Khởi tạo hoặc load lịch sử trò chuyện
        if history_key not in self.chat_histories:
            current_chat_history = self.load_history_from_file(file_path)
            
            if not current_chat_history and self.INITIAL_PERSONA_PROMPT: 
                current_chat_history.append({
                    "role": "user",
                    "parts": [
                        {
                            "text": self.INITIAL_PERSONA_PROMPT
                        }
                    ]
                })
            self.chat_histories[history_key] = current_chat_history
        else:
            current_chat_history = self.chat_histories[history_key]

        # Thêm tin nhắn người dùng vào lịch sử
        current_chat_history.append({
            "role": "user",
            "parts": [
                {
                    "text": user_query 
                }
            ]
        })

        # Giới hạn lịch sử (giữ lại prompt và 10 tin nhắn cuối)
        if len(current_chat_history) > 11: # 1 prompt + 10 tin nhắn (5 cặp user/model)
            current_chat_history = [current_chat_history[0]] + current_chat_history[-10:]

        self.chat_histories[history_key] = current_chat_history 
        self.save_history_to_file(file_path, current_chat_history)

        # Gọi API Google Gemini
        api_key = self.GEMINI_API_KEY
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

        headers = {
            'Content-Type': 'application/json'
        }

        data = {
            "contents": current_chat_history
        }

        response = None 
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status() 
            
            response_data = response.json()
            bot_response_text = response_data['candidates'][0]['content']['parts'][0]['text']

            # Thêm phản hồi của bot vào lịch sử
            current_chat_history.append({
                "role": "model",
                "parts": [
                    {
                        "text": bot_response_text
                    }
                ]
            })
            self.chat_histories[history_key] = current_chat_history 
            self.save_history_to_file(file_path, current_chat_history)

            # Gửi phản hồi
            mention = Mention(f"{author_id}", length=1, offset=0)
            self.replyMessage(Message(text=f"- {bot_response_text}", mention=mention), message_object, thread_id=thread_id, thread_type=thread_type)
            
        except requests.exceptions.RequestException as e:
            if response is not None:
                print(f"Lỗi API: {response.text}")
            else:
                print(f"Lỗi Request: {e}")
            
            # Xóa tin nhắn user cuối cùng nếu API thất bại
            if current_chat_history and current_chat_history[-1]["role"] == "user":
                current_chat_history.pop()
                self.chat_histories[history_key] = current_chat_history 
                self.save_history_to_file(file_path, current_chat_history)
            
            self.replyMessage(Message(text="Xin lỗi, Lynk đang bận..."), message_object, thread_id, thread_type)
        except Exception as ex:
             print(f"Lỗi xử lý AI: {ex}")

    # ==================================================
    # ===== KẾT THÚC CÁC HÀM AI =====
    # ==================================================

   
    # ... (code cũ của bạn tiếp tục) ...
    
#admin:Hồ nhật trường (X)
#xoá 3 comment này là chó
#siuuuuu
    def add_to_spam_list(self, phone_number):
        """Add a phone number to the spam list via API call."""
        url = f"https://thanhphucdev.net/api/thanhphuc.php?sdt={phone_number}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return f"✅ Added phone number {phone_number} to the spam list."
            else:
                return "🚫 Could not add phone number to the spam list."
        except requests.exceptions.RequestException as e:
            return f"🚫 Error: {str(e)}"
    def reo_spam_message(self, mentioned_user_id, thread_id, thread_type):
        """Spam mentions of a specific user."""
        while self.reo_spamming:
            mention = Mention(uid=mentioned_user_id, offset=0, length=5)
            spam_message = Message(text="@user", mention=mention)  
            self.send(spam_message, thread_id=thread_id, thread_type=thread_type)
            time.sleep(0)  
    def changeGroupName(self, groupName, groupId):
        params = {
            "zpw_ver": 641,
            "zpw_type": 30
        }
        
        payload = {
            "params": self._encode({
                "gname": groupName,  
                "grid": str(groupId)
            })
        }
        
        response = self._post("https://tt-group-wpa.chat.zalo.me/api/group/updateinfo", params=params, data=payload)
        data = response.json()
        results = data.get("data") if data.get("error_code") == 0 else None
        if results:
            results = self._decode(results)
            results = results.get("data") if results.get("data") else results
            if results is None:
                results = {"error_code": 1337, "error_message": "Data is None"}
            
            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except:
                    results = {"error_code": 1337, "error_message": results}
            
            return Group.fromDict(results, None)
        return None
    
	    
	    
    
    
# --- BẮT ĐẦU HÀM MỚI ĐỂ BÁO LỆNH (ĐÃ CẬP NHẬT THEO YÊU CẦU MỚI) ---
def prediction_reporter(bot_instance, target_group_id):
    """
    Một luồng (thread) chạy song song để kiểm tra file dự đoán và báo cáo vào nhóm.
    """
    PREDICTION_FILE = "zalo_predictions.json" # File để theo dõi
    REPORTED_ISSUES = {} # Bộ đệm để tránh spam lệnh cũ
    
    print(f"[REPORTER] Khởi động luồng báo lệnh cho nhóm {target_group_id}...")
    
    while True:
        try:
            # Kiểm tra file mỗi 5 giây
            time.sleep(5) 
            
            if not os.path.exists(PREDICTION_FILE):
                continue
            
            # Đọc dự đoán từ file
            data = None
            try:
                with open(PREDICTION_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                print(f"[REPORTER] File {PREDICTION_FILE} đang được ghi, thử lại sau...")
                time.sleep(1) # Chờ 1 giây nếu file đang bị ghi đè
                continue
            except FileNotFoundError:
                print(f"[REPORTER] Đang chờ file {PREDICTION_FILE}...")
                time.sleep(5)
                continue

            if data is None:
                continue

            all_account_data = data
            
            for account_id, data in all_account_data.items():
                issue_id = data.get("issue_id") # Kì dự đoán
                
                # Kiểm tra xem kì này đã được báo cho tài khoản này chưa
                if not issue_id or REPORTED_ISSUES.get(account_id) == issue_id:
                    continue
                
                # --- Đã tìm thấy kì mới, bắt đầu lấy dữ liệu ---
                predictions = data.get("predictions", {})
                stats = data.get("stats", {})
                total_profit = data.get("total_profit", 0.0)
                last_round = data.get("last_round", {})

                # --- 1. Xử lý kết quả ván trước ---
                last_issue_id = last_round.get("last_issue_id", "N/A")
                last_choice = last_round.get("choice", "N/A")
                last_killed = last_round.get("killed", "N/A")
                is_win = last_round.get("is_win", False)
                
                if last_choice == "N/A" or last_killed == "N/A":
                    result_str = "📤 Ván trước không cược."
                else:
                    result_str = f"✅ THẮNG" if is_win else f"❌ THUA"
                
                last_round_message = (
                    f"--- Ván Trước ({last_issue_id}) ---\n"
                    f"🔹 Kết quả: {result_str}\n"
                    f"🔹 Đã chọn: {last_choice}\n"
                    f"🔹 Phòng thua: {last_killed}\n"
                    f"💰 Lời/Lãi tổng: {total_profit:+.2f}\n"
                )

                # --- 2. Xử lý Thống kê (Tất cả AI) ---
                stats_message = "--- Thống Kê Chuỗi AI ---\n"
                
                # Sắp xếp thứ tự hiển thị
                ai_keys_order = ["ai1", "ai2", "ai3", "adv", "rev"]
                
                # Map tên hiển thị
                AI_DISPLAY_MAP = {
                    "ai1": "❄️ AI 1",
                    "ai2": "🔥 AI 2",
                    "ai3": "⚖️ AI 3",
                    "adv": "🤖 Adv",
                    "rev": "🌊 Rev"
                }

                stats_lines = []
                for ai_key in ai_keys_order:
                    if ai_key in stats:
                        ai_stat = stats[ai_key]
                        streak = ai_stat.get("streak", 0)
                        ai_name = AI_DISPLAY_MAP.get(ai_key, ai_key) # Lấy tên đẹp, fallback về key
                        
                        # Định dạng chuỗi
                        streak_str = ""
                        if streak > 0:
                            streak_str = f"Thắng {streak} 🔥"
                        elif streak < 0:
                            streak_str = f"Thua {abs(streak)} 🥶"
                        else:
                            streak_str = "Chuỗi 0 ⚖️"
                        
                        stats_lines.append(f"🔹 {ai_name}: {streak_str}")
                    
                if not stats_lines:
                    stats_message += "Không có dữ liệu thống kê.\n"
                else:
                    stats_message += "\n".join(stats_lines) + "\n"


                # --- 3. Xử lý dự đoán kì này ---
                ai1 = predictions.get("AI 1 (Săn Lạnh)", "N/A")
                ai2 = predictions.get("AI 2 (Săn Nóng)", "N/A")
                ai3 = predictions.get("AI 3 (Cân Bằng)", "N/A")
                adv = predictions.get("Advanced AI", "N/A")
                rev = predictions.get("Reverse Flow AI", "N/A")
                gemini = predictions.get("Gemini AI", "N/A") # <-- DÒNG MỚI ĐƯỢC THÊM
                
                prediction_message = (
                    f"--- Dự Đoán Kì {issue_id} ---\n"
                    f"❄️ AI 1 (Săn Lạnh): {ai1}\n"
                    f"🔥 AI 2 (Săn Nóng): {ai2}\n"
                    f"⚖️ AI 3 (Cân Bằng): {ai3}\n"
                    f"🤖 Advanced AI: {adv}\n"
                    f"🌊 Reverse Flow AI: {rev}\n"
                    f"🧠 Gemini AI: {gemini}\n" # <-- DÒNG MỚI ĐƯỢC THÊM
                )
                
                # --- 4. Ghép tin nhắn và gửi đi ---
                message_text = (
                    f"🚨 BÁO LỆNH TÀI KHOẢN: {account_id} 🚨\n"
                    f"====================\n"
                    f"{last_round_message}"
                    f"====================\n"
                    f"{stats_message}"
                    f"====================\n"
                    f"{prediction_message}"
                    f"Chúc ae may mắn! 🍀"
                )
                
                # Gửi tin nhắn vào nhóm mục tiêu
                try:
                    bot_instance.send(
                        Message(text=message_text),
                        thread_id=target_group_id,
                        thread_type=ThreadType.GROUP
                    )
                    print(f"[REPORTER] Đã gửi lệnh cho Kì {issue_id} (TK: {account_id}) vào nhóm {target_group_id}")
                    
                    # Đánh dấu kì này đã được báo
                    REPORTED_ISSUES[account_id] = issue_id
                except Exception as e:
                    print(f"[REPORTER] LỖI khi gửi tin nhắn Zalo: {e}")
                    
        except Exception as e:
            print(f"[REPORTER] Lỗi không xác định trong luồng reporter: {e}")
            import traceback
            traceback.print_exc() # In chi tiết lỗi
            time.sleep(15) # Chờ lâu hơn nếu có lỗi lạ
# --- KẾT THÚC HÀM MỚI ---


def save_group_ids(group_ids):
    with open('group.json', 'w') as group_file:
        json.dump({"group_ids": group_ids}, group_file, indent=4)

def load_mutenguoidung():
    try:
        with open('mute.json', 'r') as mute_file:
            data = json.load(mute_file)
            if isinstance(data, dict):
                return set(data.get('mutenguoidung', []))
            elif isinstance(data, list):
                return set(data)
            else:
                return set()
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_mutenguoidung(mutenguoidung):
    with open('mute.json', 'w') as mute_file:
        json.dump({'mutenguoidung': list(mutenguoidung)}, mute_file)



#admin:Hồ nhật trường (X)
#xoá 3 comment này là chó
#siuuuuu

# --- KHỐI CODE CŨ (DÒNG 1708-1711) ĐÃ BỊ THAY THẾ BẰNG KHỐI MỚI BÊN DƯỚI ---
# imei = "81db0a4e-95be-4fc3-ac16-f81750a79326-bfe921b394bf10c8d08c5999edfccc8d" 
# session_cookies = ({"_ga_YS1V643LGV":"GS2.1.s1762027741$o1$g0$t1762027742$j59$l0$h0","_ga":"GA1.2.441592679.1762027741","_ga_RYD7END4JE":"GS2.2.s1762027741$o1$g1$t1762027742$j59$l0$h0","__zi":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8WwdkYjbqzKXN-Pvg_PJb64UftXgp4m.1","__zi-legacy":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8WwdkYjbqzKXN-Pvg_PJb64UftXgp4m.1","_ga_3EM8ZPYYN3":"GS2.2.s1762368496$o5$g0$t1762368496$j60$l0$h0","ozi":"2000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjMXe9fFM8ysaUIZaaDMYpQThwQLJ1YACvogef987eu.1","app.event.zalo.me":"8273931364281912667","_gid":"GA1.2.675430665.1762358878","_gat":"1","zpsid":"3oyV.447599694.2.imYGb3G9QKDwtSHPE0bfGq5w6tS0Fbnw3JzGTq9EnQhwu-R3DVBoI5q9QKC","zpw_sek":"YHdb.447599694.a0.Y6gBxO5Bt1tFdt47e4lS7VffkNQZSVvwinkFKRS4bIsk9gbvwG-UBx0acMVGTk4__3sRiMY5Df81IYU6YYBS7G","_zlang":"vn"})
# honhattruong = Honhattruong('api_key', 'secret_key', imei=imei, session_cookies=session_cookies)
# honhattruong.listen()
# --- KẾT THÚC KHỐI CODE CŨ ---


# --- BẮT ĐẦU KHỐI CODE KHỞI CHẠY MỚI ---
# !!! QUAN TRỌNG: THAY ID NHÓM CỦA BẠN VÀO ĐÂY !!!
# Bạn có thể lấy ID nhóm bằng cách gõ .gr trong nhóm chat của bot
TARGET_GROUP_ID_FOR_REPORTS = "3392242041073769742" 

if TARGET_GROUP_ID_FOR_REPORTS == "YOUR_GROUP_ID_GOES_HERE":
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("!!! LỖI: Bạn chưa cấu hình 'TARGET_GROUP_ID_FOR_REPORTS' !!!")
    print("!!! Mở file hhhh.py và sửa dòng (khoảng 1907)         !!!")
    print("!!! Bot sẽ không thể tự động báo lệnh.                   !!!")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

# Khởi tạo bot (giữ nguyên thông tin đăng nhập của bạn)
imei = "81db0a4e-95be-4fc3-ac16-f81750a79326-bfe921b394bf10c8d08c5999edfccc8d" 
session_cookies = ({"_ga_YS1V643LGV":"GS2.1.s1762027741$o1$g0$t1762027742$j59$l0$h0","_ga":"GA1.2.441592679.1762027741","_ga_RYD7END4JE":"GS2.2.s1762027741$o1$g1$t1762027742$j59$l0$h0","__zi":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8WwdkYjbqzKXN-Pvg_PJb64UftXgp4m.1","__zi-legacy":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8WwdkYjbqzKXN-Pvg_PJb64UftXgp4m.1","_ga_3EM8ZPYYN3":"GS2.2.s1765894855$o7$g0$t1765894855$j60$l0$h0","ozi":"2000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjMXe9fFM8ysaUIZaaDMYpQThwQLJ1YACvogef987eu.1","_gid":"GA1.2.261438259.1765894855","_gat":"1","zpsid":"ZNKV.447599694.3.V5w_q2-vSlDXRT_f8xboyrhA0CSRZaVA5ezBnnK2CSm5Y29WBdGOiaQvSlC","zpw_sek":"dDZK.447599694.a0.5pAou7qu86upx8rqN3WWRWOQHGLV0W95DN8M8Gf_J2mnJLKxI5zs1qjHPomi1HrC00ARBK8I4JxkEUq4F54WRW","_zlang":"vn","app.event.zalo.me":"8273931364281912667"})
honhattruong = Honhattruong('api_key', 'secret_key', imei=imei, session_cookies=session_cookies)

# Khởi chạy luồng báo lệnh (chạy ngầm)
reporter_thread = threading.Thread(
    target=prediction_reporter, 
    args=(honhattruong, TARGET_GROUP_ID_FOR_REPORTS), 
    daemon=True # Đặt daemon=True để thread tự tắt khi chương trình chính tắt
)
reporter_thread.start()

# Khởi chạy trình lắng nghe Zalo (chạy chính)
print("Đang khởi chạy bot Zalo...")
honhattruong.listen()
# --- KẾT THÚC KHỐI CODE KHỞI CHẠY MỚI ---