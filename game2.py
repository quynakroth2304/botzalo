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
import sys
import logging
import math
import ssl
from collections import deque, Counter
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, Tuple, Optional, List

# ==================== NÂNG CẤP AI TỪ BUMX.PY ====================
# Escape Game AI dependencies (Thêm từ bumx.py)
import numpy as np
import sqlite3
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import pytz
import websocket
from rich.console import Console, Group as RichGroup
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.align import Align
from rich.rule import Rule
from rich.text import Text
from rich import box
# ==================== KẾT THÚC NÂNG CẤP ====================

# ==================== ESCAPE GAME AI SETUP ====================
console = Console()
tz = pytz.timezone("Asia/Ho_Chi_Minh")

logger = logging.getLogger("escape_vip_ai_merged")
logger.setLevel(logging.INFO)
logger.addHandler(logging.FileHandler("escape_vip_ai_merged.log", encoding="utf-8"))

BET_API_URL = "https://api.escapemaster.net/escape_game/bet"
WS_URL = "wss://api.escapemaster.net/escape_master/ws"
WALLET_API_URL = "https://wallet.3games.io/api/wallet/user_asset"

HTTP = requests.Session()
ROOM_NAMES = {
    1: "🔦 Nhà kho", 2: "🪑 Phòng họp", 3: "🏢 Phòng giám đốc", 4: "💬 Phòng trò chuyện",
    5: "🎥 Phòng giám sát", 6: "🏢 Văn phòng", 7: "💰 Phòng tài vụ", 8: "👥 Phòng nhân sự"
}
ROOM_ORDER = [1, 2, 3, 4, 5, 6, 7, 8]
room_names_to_id = {name: num for num, name in ROOM_NAMES.items()}
room_names_map_str = {str(num): name for num, name in ROOM_NAMES.items()} # Thêm từ bumx.py
room_ids_map_str = {name: str(num) for num, name in ROOM_NAMES.items()} # Thêm từ bumx.py

# ==================== CẬP NHẬT TRẠNG THÁI AI (TỪ BUMX.PY) ====================
ESCAPE_USER_ID: Optional[int] = None
ESCAPE_SECRET_KEY: Optional[str] = None
escape_issue_id: Optional[int] = None
escape_count_down: Optional[int] = None
escape_killed_room: Optional[int] = None

# *** THAY ĐỔI: Cấu trúc room_state mới từ bumx.py để AI hoạt động ***
room_state: Dict[int, Dict[str, Any]] = {r: {"players": 0, "bet": 0, "player_influx": 0, "last_players": 0} for r in ROOM_ORDER}

escape_predicted_room: Optional[int] = None
escape_current_balance: Optional[float] = None
escape_bet_amount: float = 1.0
escape_use_autobet: bool = False
escape_stop_flag: bool = False
escape_ws: Dict[str, Any] = {"ws": None}

# *** THÊM: Các biến toàn cục mới cho AI từ bumx.py ***
killer_history: List[Dict[str, Any]] = [] # Đổi tên từ escape_killer_history
selected_currency_unit = "BUILD" # Cho AI compatibility
escape_ai_follow: Optional[str] = "5" # Mặc định theo AI Nâng cao (Advanced)

# Biến toàn cục để lưu trữ dự đoán cho lệnh .escape status
ai1_choice: str = "N/A"
ai2_choice: str = "N/A"
ai3_choice: str = "N/A"
advanced_choice: str = "N/A"
advanced_confidence: float = 0.0

is_fallback_mode: bool = False
# (Các biến state phức tạp hơn như stats, scored_issue... được bỏ qua để giữ bot zalo đơn giản,
#  nhưng killer_history và room_state là BẮT BUỘC cho AI)
# ==================== KẾT THÚC CẬP NHẬT TRẠNG THÁI ====================


# ==================== BỘ NÃO AI MỚI TỪ BUMX.PY ====================
# *** THAY THẾ: PatternDetector bằng phiên bản nâng cao ***
class PatternDetector:
    def __init__(self):
        self.pattern_memory = deque(maxlen=100)

    def detect_patterns(self, killer_history):
        if len(killer_history) < 10:
            return {}
        patterns = {
            'alternating': self._detect_alternating(killer_history),
            'clustering': self._detect_clustering(killer_history),
            'cycles': self._detect_cycles(killer_history),
            'avoidance': self._detect_avoidance(killer_history),
            'low_volatility': self._detect_low_volatility(killer_history)
        }
        return patterns

    def _detect_alternating(self, history):
        recent = [h['room'] for h in history[-10:]]
        alternating_score = 0
        for i in range(1, len(recent)):
            if recent[i] != recent[i-1]:
                alternating_score += 1
        return alternating_score / (len(recent) - 1) if len(recent) > 1 else 0

    def _detect_clustering(self, history):
        recent = [h['room'] for h in history[-15:]]
        room_counts = Counter(recent)
        total = len(recent)
        clustering_score = sum((count / total) ** 2 for count in room_counts.values())
        return clustering_score

    def _detect_cycles(self, history):
        recent = [h['room'] for h in history[-20:]]
        best_cycle_score = 0
        best_cycle_length = 0
        for cycle_len in range(2, 9):
            if len(recent) < cycle_len * 2:
                continue
            matches = 0
            comparisons = 0
            for i in range(cycle_len, len(recent)):
                if recent[i] == recent[i - cycle_len]:
                    matches += 1
                comparisons += 1
            if comparisons > 0:
                cycle_score = matches / comparisons
                if cycle_score > best_cycle_score:
                    best_cycle_score = cycle_score
                    best_cycle_length = cycle_len
        return {'score': best_cycle_score, 'length': best_cycle_length}

    def _detect_avoidance(self, history):
        recent = [h['room'] for h in history[-20:]]
        room_counts = Counter(recent)
        avoidance_scores = {}
        for room_name in ROOM_NAMES.values():
            expected = len(recent) / 8
            actual = room_counts.get(room_name, 0)
            avoidance_scores[room_name] = (expected - actual) / expected if expected > 0 else 0
        return avoidance_scores

    def _detect_low_volatility(self, history):
        recent = [h['room'] for h in history[-20:]]
        room_counts = Counter(recent)
        volatility = np.std(list(room_counts.values()))
        return 1 / (volatility + 1)

# *** THAY THẾ: AdvancedAISystem bằng phiên bản nâng cao ***
class AdvancedAISystem:
    def __init__(self):
        self.models = {
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'logistic': LogisticRegression(random_state=42, max_iter=1000)
        }
        self.scaler = StandardScaler()
        self.is_trained = False
        self.pattern_detector = PatternDetector()
        self.win_history = {room: deque(maxlen=50) for room in ROOM_NAMES.values()} # Use int-keyed ROOM_NAMES

    def extract_features(self, rates_10, rates_100, trends, killer_history, current_time):
        features = []
        # --- SỬA ĐỔI: Sử dụng biến toàn cục `room_state` (đã được đổi tên) ---
        for i in ROOM_ORDER:
            room_name = ROOM_NAMES[i]
            # Get live data from global room_state
            state = room_state.get(i, {}) # <--- SỬ DỤNG BIẾN TOÀN CỤC MỚI
            players = state.get("players", 0)
            total_bet = state.get("bet", 0)
            avg_bet = total_bet / players if players > 0 else 0
            influx = state.get("player_influx", 0) # Use live influx
            features.extend([
                rates_10.get(room_name, 100),
                rates_100.get(room_name, 100),
                trends.get(room_name, (0, False, 0))[0],
                1 if trends.get(room_name, (0, False, 0))[1] else 0,
                trends.get(room_name, (0, False, 0))[2],
                avg_bet,
                influx
            ])
        # --- KẾT THÚC SỬA ĐỔI ---
        
        hour = current_time.hour
        minute = current_time.minute
        features.extend([hour, minute, hour * 60 + minute])
        
        if len(killer_history) >= 5:
            recent_kills = [h['room'] for h in killer_history[-5:]]
            for room_name in ROOM_NAMES.values():
                features.append(recent_kills.count(room_name))
        else:
            features.extend([0] * 8)
            
        if killer_history:
            last_room = killer_history[-1]['room']
            streak_count = 0
            for h in reversed(killer_history):
                if h['room'] == last_room:
                    streak_count += 1
                else:
                    break
            features.append(streak_count)
        else:
            features.append(0)
            
        if len(killer_history) >= 10:
            room_counts = Counter([h['room'] for h in killer_history[-10:]])
            volatility = np.std(list(room_counts.values()))
            features.append(volatility)
        else:
            features.append(0)
            
        for room_name in ROOM_NAMES.values():
            wins = sum(self.win_history[room_name]) if self.win_history[room_name] else 0
            games = len(self.win_history[room_name])
            win_rate = wins / games if games > 0 else 0.5
            features.append(win_rate)
            
        return np.array(features).reshape(1, -1)

    def train_models(self, training_data):
        if len(training_data) < 50:
            logger.warning("Not enough data to train AI models (< 50).")
            return False
        try:
            X = []
            y = []
            room_name_list = list(ROOM_NAMES.values())
            for data in training_data:
                features = self.extract_features(
                    data['rates_10'], data['rates_100'], data['trends'],
                    data['history'], data['timestamp']
                )
                X.append(features.flatten())
                y.append(room_name_list.index(data['actual_room']))
            
            X = np.array(X)
            y = np.array(y)
            X_scaled = self.scaler.fit_transform(X)
            
            for name, model in self.models.items():
                try:
                    model.fit(X_scaled, y)
                except Exception as e:
                    logger.error(f"Error training model {name}: {e}")
            
            self.is_trained = True
            logger.info("AI models trained successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to prepare training data: {e}")
            return False

    def predict_advanced(self, rates_10, rates_100, trends, killer_history):
        if not self.is_trained:
            return self.fallback_prediction(rates_10, rates_100, trends)
        
        current_time = datetime.now(tz)
        features = self.extract_features(rates_10, rates_100, trends, killer_history, current_time)
        features_scaled = self.scaler.transform(features)
        
        predictions = {}
        confidences = {}
        room_name_list = list(ROOM_NAMES.values())

        for name, model in self.models.items():
            try:
                pred_proba = model.predict_proba(features_scaled)[0]
                pred_class = np.argmax(pred_proba)
                confidence = np.max(pred_proba)
                room_name = room_name_list[pred_class]
                predictions[name] = room_name
                confidences[name] = confidence
            except Exception as e:
                logger.error(f"Error in {name} prediction: {e}")

        room_votes = {}
        for model_name, room in predictions.items():
            weight = confidences.get(model_name, 0.1)
            hist_win_rate = sum(self.win_history.get(room, [])) / len(self.win_history.get(room, [1])) if self.win_history.get(room) else 1.0
            room_votes[room] = room_votes.get(room, 0) + weight * hist_win_rate
            
        if room_votes:
            best_room = max(room_votes, key=room_votes.get)
            total_votes = sum(room_votes.values())
            confidence = (room_votes[best_room] / total_votes) if total_votes > 0 else 0
            return best_room, confidence, predictions
        
        return self.fallback_prediction(rates_10, rates_100, trends)

    def fallback_prediction(self, rates_10, rates_100, trends):
        room_scores = {}
        for room_name in ROOM_NAMES.values():
            base_score = (rates_10.get(room_name, 100) * 0.4 + rates_100.get(room_name, 100) * 0.6)
            trend_data = trends.get(room_name, (0, False, 0))
            trend_diff, is_overdue, _ = trend_data
            if trend_diff > 0.1:
                base_score -= (trend_diff * 20)
            if is_overdue:
                base_score += 5.0
            
            # --- SỬA ĐỔI: Sử dụng biến toàn cục `room_state` (đã được đổi tên) ---
            rid = room_names_to_id.get(room_name)
            if rid:
                state = room_state.get(rid, {}) # <--- SỬ DỤNG BIẾN TOÀN CỤC MỚI
                players = state.get("players", 0)
                total_bet = state.get("bet", 0)
                avg_bet = total_bet / players if players > 0 else 0
                influx = state.get("player_influx", 0)
                base_score -= avg_bet * 0.05 # Keep bot.py's avg_bet penalty
                base_score += influx * 0.02
            # --- KẾT THÚC SỬA ĐỔI ---
            
            hist_win_rate = sum(self.win_history.get(room_name, [])) / len(self.win_history.get(room_name, [1])) if self.win_history.get(room_name) else 1.0
            base_score *= hist_win_rate
            room_scores[room_name] = base_score
            
        best_room = max(room_scores, key=room_scores.get)
        total_score = sum(room_scores.values())
        confidence = (room_scores[best_room] / total_score) if total_score > 0 else 0
        return best_room, confidence, {"fallback": best_room}

    def update_win_history(self, room, is_win):
        if room in self.win_history:
            self.win_history[room].append(1 if is_win else 0)
        else:
            logger.warning(f"Attempted to update win history for unknown room: {room}")

escape_ai_system = AdvancedAISystem() # Khởi tạo AI mới

# *** THÊM: Hàm khởi tạo DB từ bumx.py ***
def init_database():
    try:
        conn = sqlite3.connect('escape_master.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id TEXT,
                killed_room_id INTEGER,
                room_rates TEXT,
                trends TEXT,
                timestamp DATETIME,
                asset_type TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id TEXT,
                predicted_room TEXT,
                actual_room TEXT,
                ai_type TEXT,
                confidence REAL,
                result TEXT,
                timestamp DATETIME
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database init error: {e}")
        console.print(f"[red]Lỗi khởi tạo Database: {e}[/]")

# *** THAY THẾ: escape_fetch_data bằng phiên bản nâng cao ***
def escape_fetch_data(url, headers, silent=False):
    try:
        response = HTTP.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            j = response.json()
            if j.get('code') == 0:
                return j.get('data')
        if not silent:
            console.print(f"[red]Lỗi tải dữ liệu từ {url}: HTTP {response.status_code}[/]")
            logger.warning(f"Fetch_data error {url}: HTTP {response.status_code} {response.text}")
        return None
    except Exception as e:
        if not silent:
            console.print(f"[red]Lỗi tải dữ liệu từ {url}: {e}[/]")
            logger.error(f"Fetch_data exception {url}: {e}")
        return None

# *** THAY THẾ: escape_analyze_data bằng phiên bản AI nâng cao ***
def escape_analyze_data(asset_mode):
    global is_fallback_mode
    TREND_MULTIPLIER = 15
    OVERDUE_THRESHOLD = 20
    OVERDUE_PENALTY = 4.0

    url_10 = f"https://api.escapemaster.net/escape_game/recent_10_issues?asset={asset_mode}"
    url_100_stats = f"https://api.escapemaster.net/escape_game/recent_100_issues?asset={asset_mode}"
    url_100_list = f"https://api.escapemaster.net/escape_game/recent_issues?asset={asset_mode}&page=1&limit=100"
    
    headers = {
        "content-type": "application/json",
        "user-id": str(ESCAPE_USER_ID) if ESCAPE_USER_ID else "",
        "user-secret-key": ESCAPE_SECRET_KEY if ESCAPE_SECRET_KEY else ""
    }
    
    data_10 = escape_fetch_data(url_10, headers, silent=True)
    data_100_stats = escape_fetch_data(url_100_stats, headers, silent=True)
    data_100_list = escape_fetch_data(url_100_list, headers, silent=True)
    
    if not all([data_10, data_100_stats]):
        logger.warning("Failed to fetch critical AI data (10 or 100 stats).")
        return None, [], "N/A", {}, "N/A", "N/A", "N/A", "N/A", 0, {}
    
    is_fallback_mode = data_100_list is None
    if is_fallback_mode:
        logger.warning("Falling back, 100 issue list not available.")

    current_issue = data_10[0]
    current_issue_id = current_issue.get('issue_id')
    try:
        killed_room_id = int(current_issue.get('killed_room_id'))
    except Exception:
        killed_room_id = 0
    current_killed_room_name = ROOM_NAMES.get(killed_room_id, "N/A")
    
    if current_issue_id and current_issue_id not in [h['issue'] for h in killer_history]:
        killer_history.append({'issue': current_issue_id, 'room': current_killed_room_name})
        if len(killer_history) > 100:
            killer_history.pop(0)

    killed_counts_10 = {r: 0 for r in ROOM_ORDER}
    for item in data_10:
        try:
            kr_id = int(item.get('killed_room_id'))
            if kr_id in killed_counts_10:
                killed_counts_10[kr_id] += 1
        except Exception:
            pass
    rates_10 = {ROOM_NAMES.get(k): 100 - (v * 10) for k, v in killed_counts_10.items()}
    
    stats_100 = data_100_stats.get('room_id_2_killed_times', {})
    rates_100 = {ROOM_NAMES.get(rid): 100 - stats_100.get(str(rid), 0) for rid in ROOM_ORDER}
    
    trends = {}
    rounds_since_kill = {name: 100 for name in ROOM_NAMES.values()}
    if not is_fallback_mode:
        for i, issue in enumerate(data_100_list):
            try:
                room_id = int(issue.get('killed_room_id'))
                room_name = ROOM_NAMES.get(room_id)
                if room_name and rounds_since_kill[room_name] == 100:
                    rounds_since_kill[room_name] = i
            except Exception:
                pass
                
    for rid, room_name in ROOM_NAMES.items():
        freq_10 = killed_counts_10.get(rid, 0) / 10.0
        freq_100 = stats_100.get(str(rid), 0) / 100.0
        trend_diff = freq_10 - freq_100
        is_overdue = (rounds_since_kill.get(room_name, 0) > OVERDUE_THRESHOLD) if not is_fallback_mode else False
        trends[room_name] = (trend_diff, is_overdue, rounds_since_kill.get(room_name, 0) if not is_fallback_mode else 0)
    
    if not escape_ai_system.is_trained and not is_fallback_mode and len(data_100_list) > 50:
        console.print("[yellow]Đang huấn luyện AI với dữ liệu lịch sử...[/]")
        training_data = []
        history_for_training = []
        for issue in reversed(data_100_list):
            try:
                room_id = int(issue.get('killed_room_id'))
                room_name = ROOM_NAMES.get(room_id)
                if room_name:
                    training_data.append({
                        'rates_10': rates_10,
                        'rates_100': rates_100,
                        'trends': trends,
                        'history': history_for_training.copy(),
                        'timestamp': datetime.fromtimestamp(issue.get('create_time', time.time()), tz),
                        'actual_room': room_name
                    })
                    history_for_training.append({'issue': issue.get('issue_id'), 'room': room_name})
            except Exception:
                pass
        escape_ai_system.train_models(training_data)
    
    best_room, confidence, model_predictions = escape_ai_system.predict_advanced(rates_10, rates_100, trends, killer_history)
    
    final_rates = {}
    for name in ROOM_NAMES.values():
        base_rate = (rates_10.get(name, 100) * 0.4 + rates_100.get(name, 100) * 0.6)
        trend_diff, is_overdue, since_kill = trends.get(name, (0, False, 0))
        if trend_diff > 0.05:
            base_rate -= (trend_diff * TREND_MULTIPLIER)
        if is_overdue:
            base_rate += OVERDUE_PENALTY
        final_rates[name] = base_rate
    
    cold_rooms = [r for r, (td, iso, _) in trends.items() if td < -0.05]
    ai1_choice = max([(room, final_rates[room]) for room in cold_rooms], key=lambda x: x[1])[0] if cold_rooms else "N/A"
    
    hot_rooms = [r for r, (td, iso, _) in trends.items() if td > 0.05]
    ai2_choice = max([(room, final_rates[room]) for room in hot_rooms], key=lambda x: x[1])[0] if hot_rooms else "N/A"
    
    stable_rooms = [r for r, (td, iso, _) in trends.items() if not iso and -0.05 <= td <= 0.05]
    ai3_choice = max([(room, final_rates[room]) for room in stable_rooms], key=lambda x: x[1])[0] if stable_rooms else "N/A"
    
    advanced_choice = best_room
    
    # --- Ưu tiên phòng cược thấp (Logic từ bumx.py) ---
    def prioritize_low_bet_amount(choices: List[str]) -> str:
        if not choices or (len(choices) == 1 and choices[0] == "N/A"):
            return "N/A"
        
        valid_choices = [c for c in choices if c != "N/A"]
        if not valid_choices:
            return "N/A"
        if len(valid_choices) == 1:
            return valid_choices[0]

        bets = {}
        for room_name in valid_choices:
            rid = room_names_to_id.get(room_name)
            if rid and rid in room_state:
                # Sử dụng `room_state` toàn cục
                bets[room_name] = room_state[rid].get("bet", float('inf')) 
            else:
                bets[room_name] = float('inf')
        
        if not bets:
            return valid_choices[0] # Fallback
            
        # Chọn phòng có cược thấp nhất
        return min(bets, key=bets.get)
    
    ai1_choice = prioritize_low_bet_amount([ai1_choice])
    ai2_choice = prioritize_low_bet_amount([ai2_choice])
    ai3_choice = prioritize_low_bet_amount([ai3_choice])
    advanced_choice = prioritize_low_bet_amount([advanced_choice])
    # --- Kết thúc logic ưu tiên ---

    patterns = escape_ai_system.pattern_detector.detect_patterns(killer_history)
    sorted_rates = sorted(final_rates.items(), key=lambda x: x[1], reverse=True)
    
    try:
        conn = sqlite3.connect('escape_master.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM game_history WHERE issue_id = ?", (current_issue_id,))
        if cursor.fetchone() is None:
            cursor.execute('''
                INSERT INTO game_history (issue_id, killed_room_id, room_rates, trends, timestamp, asset_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (current_issue_id, killed_room_id, json.dumps({**rates_10, **rates_100}), json.dumps(trends), datetime.now(tz), asset_mode))
            conn.commit()
        conn.close()
    except Exception as e:
        console.print(f"[red]Lỗi database: {e}[/]")
        logger.error(f"Database save error: {e}")

    # Trả về tất cả các lựa chọn AI
    return current_issue_id, sorted_rates, current_killed_room_name, trends, ai1_choice, ai2_choice, ai3_choice, advanced_choice, confidence, patterns
# ==================== KẾT THÚC BỘ NÃO AI MỚI ====================


# *** CẬP NHẬT: escape_on_message để nuôi AI mới ***
def escape_on_message(ws, message):
    # Sử dụng các biến global của game2.py
    global escape_issue_id, escape_count_down, escape_killed_room, escape_predicted_room
    # Sử dụng các biến AI mới
    global room_state, killer_history
    
    try:
        if isinstance(message, bytes):
            message = message.decode("utf-8", errors="replace")
        
        data = None
        try: data = json.loads(message)
        except Exception:
            try: data = json.loads(message.replace("'", '"'))
            except Exception:
                logger.debug(f"on_message non-json: {str(message)[:200]}")
                return
        if isinstance(data, dict) and isinstance(data.get("data"), str):
            try:
                inner = json.loads(data.get("data"))
                merged = dict(data)
                merged.update(inner)
                data = merged
            except Exception: pass
        
        msg_type = data.get("msg_type") or data.get("type") or ""
        msg_type = str(msg_type)
        
        # Lấy issue_id (copy từ _extract_issue_id của bumx.py)
        new_issue = None
        possible = []
        for key in ("issue_id", "issueId", "issue", "id"):
            v = data.get(key)
            if v is not None: possible.append(v)
        if isinstance(data.get("data"), dict):
            for key in ("issue_id", "issueId", "issue", "id"):
                v = data["data"].get(key)
                if v is not None: possible.append(v)
        for p in possible:
            try: new_issue = int(p); break
            except Exception:
                try: new_issue = int(str(p)); break
                except Exception: continue

        # Kiểm tra tiền tệ
        message_asset_type = (data.get("asset_type") or "").upper()
        if message_asset_type and message_asset_type != selected_currency_unit:
            logger.debug(f"Ignored WS message: asset_type ({message_asset_type}) != {selected_currency_unit}")
            return
        
        if "issue_stat" in msg_type:
            rooms = data.get("rooms") or []
            if not rooms and isinstance(data.get("data"), dict):
                rooms = data["data"].get("rooms", [])

            for rm in (rooms or []):
                try:
                    rid = int(rm.get("room_id") or rm.get("roomId") or rm.get("id"))
                    if rid not in ROOM_ORDER: continue
                    
                    # --- CẬP NHẬT: Ghi dữ liệu cho cấu trúc room_state mới ---
                    last_players = room_state[rid].get("last_players", 0)
                    players = int(rm.get("user_cnt") or rm.get("userCount") or 0) or 0
                    bet = float(rm.get("total_bet_amount") or rm.get("totalBet") or rm.get("bet") or 0) or 0
                    
                    room_state[rid] = {
                        "players": players, 
                        "bet": bet, 
                        "player_influx": players - last_players, # AI cần cái này
                        "last_players": players # AI cần cái này
                    }
                    # --- KẾT THÚC CẬP NHẬT ---
                except Exception as e:
                    logger.warning(f"Error processing room stat: {e} | data: {rm}")
            
            if new_issue is not None and new_issue != escape_issue_id:
                escape_issue_id = new_issue
                escape_predicted_room = None
                
        elif "count_down" in msg_type:
            escape_count_down = data.get("count_down") or data.get("countDown") or data.get("count") or escape_count_down
            
        elif "result" in msg_type:
            kr = data.get("killed_room") if data.get("killed_room") is not None else data.get("killed_room_id")
            if kr is None and isinstance(data.get("data"), dict):
                kr = data["data"].get("killed_room") or data["data"].get("killed_room_id")

            if kr is not None:
                try:
                    krid = int(kr)
                    if krid in ROOM_ORDER:
                        escape_killed_room = krid
                        
                        # --- CẬP NHẬT: Nuôi dữ liệu killer_history cho AI ---
                        res_issue = new_issue if new_issue is not None else escape_issue_id
                        killed_room_name = ROOM_NAMES.get(krid, "N/A")
                        
                        if res_issue and krid:
                            # Thêm vào lịch sử
                            killer_history.append({'issue': res_issue, 'room': killed_room_name})
                            if len(killer_history) > 100:
                                killer_history.pop(0)
                            logger.info(f"Ván {res_issue} kết thúc. Sát thủ: {killed_room_name}. Cập nhật killer_history.")
                        # --- KẾT THÚC CẬP NHẬT ---
                except Exception:
                    pass
                
    except Exception as e:
        logger.error(f"Escape WS error: {e}")


def escape_on_open(ws):
    escape_ws["ws"] = ws
    try:
        # Sử dụng biến tiền tệ mới
        payload = {"msg_type": "handle_enter_game", "asset_type": selected_currency_unit, "user_id": ESCAPE_USER_ID, "user_secret_key": ESCAPE_SECRET_KEY}
        ws.send(json.dumps(payload))
    except Exception:
        pass

def escape_start_ws():
    while not escape_stop_flag:
        try:
            ws_app = websocket.WebSocketApp(
                WS_URL,
                on_open=escape_on_open,
                on_message=escape_on_message,
            )
            escape_ws["ws"] = ws_app
            ws_app.run_forever(ping_interval=10, sslopt={"cert_reqs": ssl.CERT_NONE})
        except Exception:
            pass
        time.sleep(5)

# ==================== ZALO BOT (ORIGINAL HHHH.PY) ====================

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
            "#FFFFFF", "#00FF00", "#FF0000", "#0000FF", "#FFFF00", "#FF00FF", 
            "#00FFFF", "#FFA500", "#800080", "#FFC0CB"
        ]
        self.messages_to_delete = []  
        self.admin_file = 'admin.json'  
        self.start_time = datetime.datetime.now()  
        self.banned_words = set([
            "địt", "lồn", "lol", "đm", "cc", "lon", "đmm", "dm", "dmm", "dit"
        ])
        self.banned_word_removal_enabled = False
        
        # AI Chat
        self.GEMINI_API_KEY = ''
        self.chat_histories = {}
        self.INITIAL_PERSONA_PROMPT = "Bạn đóng vai Lynk, là con gái, tính cách dâm đãng nói chuyện không có chút ý tứ nào"
        self.HISTORY_DIR = "data/history"
        os.makedirs(self.HISTORY_DIR, exist_ok=True)
        self.ai_allowed_groups = []

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
                return {line.split(',')[0]: (line.strip().split(',')[1], float(line.strip().split(',')[2])) 
                        for line in file.readlines() if line.strip()}
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

    def reo_spam_message(self, mentioned_user_id, thread_id, thread_type):
        while self.reo_spamming:
            mention = Mention(uid=mentioned_user_id, offset=0, length=5)
            spam_message = Message(text="@user", mention=mention)
            self.send(spam_message, thread_id=thread_id, thread_type=thread_type)
            time.sleep(0)

    def handle_ai_request(self, user_query, thread_id, thread_type, author_id, message_object):
        history_key = (thread_id, author_id)
        file_path = os.path.join(self.HISTORY_DIR, f"{thread_id}_{author_id}.json")

        if history_key not in self.chat_histories:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        current_chat_history = json.load(f)
                except:
                    current_chat_history = []
            else:
                current_chat_history = []
                
            if not current_chat_history and self.INITIAL_PERSONA_PROMPT:
                current_chat_history.append({
                    "role": "user",
                    "parts": [{"text": self.INITIAL_PERSONA_PROMPT}]
                })
            self.chat_histories[history_key] = current_chat_history
        else:
            current_chat_history = self.chat_histories[history_key]

        current_chat_history.append({
            "role": "user",
            "parts": [{"text": user_query}]
        })

        if len(current_chat_history) > 11:
            current_chat_history = [current_chat_history[0]] + current_chat_history[-10:]

        self.chat_histories[history_key] = current_chat_history
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(current_chat_history, f, indent=2, ensure_ascii=False)
        except:
            pass

        api_key = self.GEMINI_API_KEY
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        data = {"contents": current_chat_history}

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            
            response_data = response.json()
            bot_response_text = response_data['candidates'][0]['content']['parts'][0]['text']

            current_chat_history.append({
                "role": "model",
                "parts": [{"text": bot_response_text}]
            })
            self.chat_histories[history_key] = current_chat_history
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(current_chat_history, f, indent=2, ensure_ascii=False)
            except:
                pass

            mention = Mention(f"{author_id}", length=1, offset=0)
            self.replyMessage(Message(text=f"- {bot_response_text}", mention=mention), 
                            message_object, thread_id=thread_id, thread_type=thread_type)
            
        except Exception as ex:
            if current_chat_history and current_chat_history[-1]["role"] == "user":
                current_chat_history.pop()
                self.chat_histories[history_key] = current_chat_history
            
            self.replyMessage(Message(text="Xin lỗi, Lynk đang bận..."), 
                            message_object, thread_id, thread_type)

    # *** CẬP NHẬT: onMessage (Zalo) để điều khiển AI mới ***
    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        print(f"\033[32m{message} \033[39m|\033[31m {author_id} \033[39m|\033[33m {thread_id}\033[0m\n")
        
        # Khai báo các biến global
        global escape_use_autobet, escape_bet_amount, escape_ai_follow
        # Khai báo các biến dự đoán AI để hiển thị
        global ai1_choice, ai2_choice, ai3_choice, advanced_choice, advanced_confidence

        if not isinstance(message, str):
            return

        message_text = message
        idadmin = self.load_admins()

        # ============ ESCAPE GAME COMMANDS (ĐÃ NÂNG CẤP) ============
        if message.startswith(".escape"):
            parts = message.split()
            if len(parts) == 1:
                # --- CẬP NHẬT: Hiển thị trạng thái AI mới ---
                ai_follow_map = {
                    "1": "AI 1 (Lạnh)",
                    "2": "AI 2 (Nóng)",
                    "3": "AI 3 (Cân Bằng)",
                    "5": "AI Nâng cao"
                }
                current_ai_follow = ai_follow_map.get(escape_ai_follow, f"Không rõ ({escape_ai_follow})")
                
                status_text = f"""🎮 TRẠNG THÁI GAME THOÁT HIỂM:
                
Phiên: {escape_issue_id or 'N/A'}
Countdown: {escape_count_down or 'N/A'}s
Auto-bet: {'BẬT' if escape_use_autobet else 'TẮT'}
Đang theo: [ {current_ai_follow} ]

DỰ ĐOÁN AI (refresh liên tục):
❄️ AI 1 (Lạnh): {ai1_choice}
🔥 AI 2 (Nóng): {ai2_choice}
⚖️ AI 3 (Cân bằng): {ai3_choice}
🤖 AI Nâng cao: {advanced_choice} ({advanced_confidence:.1%})

Lệnh:
.escape start/stop - Bật/Tắt Auto-bet
.escape bet <số tiền> - Đặt số tiền cược
.escape ai <số> - Chọn AI (1, 2, 3, hoặc 5)"""
                # --- KẾT THÚC CẬP NHẬT ---
                self.replyMessage(Message(text=status_text), message_object, 
                                thread_id=thread_id, thread_type=thread_type)
                
            elif parts[1] == "start":
                escape_use_autobet = True
                self.replyMessage(Message(text="✅ Đã bật Auto-bet Escape Game!"), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
                
            elif parts[1] == "stop":
                escape_use_autobet = False
                self.replyMessage(Message(text="⏹️ Đã tắt Auto-bet Escape Game!"), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
                
            elif parts[1] == "bet" and len(parts) >= 3:
                try:
                    escape_bet_amount = float(parts[2])
                    self.replyMessage(Message(text=f"✅ Đã đặt số tiền cược: {escape_bet_amount} BUILD"), 
                                    message_object, thread_id=thread_id, thread_type=thread_type)
                except:
                    self.replyMessage(Message(text="❌ Số tiền không hợp lệ!"), 
                                    message_object, thread_id=thread_id, thread_type=thread_type)
            
            # --- THÊM: Lệnh chọn AI ---
            elif parts[1] == "ai" and len(parts) >= 3:
                chosen_ai = parts[2]
                if chosen_ai in ["1", "2", "3", "5"]:
                    escape_ai_follow = chosen_ai
                    ai_follow_map = {
                        "1": "AI 1 (Lạnh)",
                        "2": "AI 2 (Nóng)",
                        "3": "AI 3 (Cân Bằng)",
                        "5": "AI Nâng cao"
                    }
                    self.replyMessage(Message(text=f"✅ Bot sẽ đi theo: [ {ai_follow_map.get(escape_ai_follow)} ]"), 
                                    message_object, thread_id=thread_id, thread_type=thread_type)
                else:
                    self.replyMessage(Message(text="❌ AI không hợp lệ. Chỉ chọn 1, 2, 3, hoặc 5."), 
                                    message_object, thread_id=thread_id, thread_type=thread_type)
            # --- KẾT THÚC THÊM ---
            return

        # ============ ORIGINAL HHHH.PY COMMANDS ============
        
        if message.startswith(".call"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
                return
            parts = message.split()
            target_group_id = parts[1] if len(parts) > 1 else thread_id
            try:
                self.sendGroupCall(thread_id=target_group_id)
                self.replyMessage(Message(text=f'📞 Đã bắt đầu cuộc gọi tại nhóm ID: {target_group_id}'), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
            except Exception as e:
                self.replyMessage(Message(text=f'🚫 Có lỗi xảy ra: {e}'), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
            return

        if message.startswith(".kick"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
                return
            mentions = message_object.mentions
            if not mentions:
                self.replyMessage(Message(text='🚫 Bạn cần đề cập ít nhất một người dùng để kick.'), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
                return
            kicked_users = []
            for mention in mentions:
                mentioned_user_id = mention['uid']
                if mentioned_user_id not in self.excluded_user_ids:
                    try:
                        self.kickUsersFromGroup([mentioned_user_id], thread_id)
                        kicked_users.append(mentioned_user_id)
                    except Exception as e:
                        self.replyMessage(Message(text=f'🚫 Có lỗi khi kick người dùng {mentioned_user_id}: {str(e)}'), 
                                        message_object, thread_id=thread_id, thread_type=thread_type)
            if kicked_users:
                self.replyMessage(Message(text=f'✅ Đã kick người dùng: {", ".join(kicked_users)}'), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
            return

        if message.startswith("/menu"):
            menu_text = """📋 DANH SÁCH LỆNH:

🎮 ESCAPE GAME:
.escape - Xem trạng thái game & AI
.escape start - Bắt đầu auto-bet
.escape stop - Dừng auto-bet
.escape bet <số> - Đặt tiền cược
.escape ai <số> - Chọn AI (1, 2, 3, 5)

🤖 ZALO BOT:
.spam <nội dung> - Spam tin nhắn
.stop - Dừng spam
.kick @user - Kick user
.admin <id> - Thêm admin
.info - Xem ID của bạn
.ask <câu hỏi> - Chat với AI
/menu - Xem menu này"""
            self.replyMessage(Message(text=menu_text), message_object, 
                            thread_id=thread_id, thread_type=thread_type)
            return

        if message.startswith(".spam"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
                return
            if self.spamming:
                self.replyMessage(Message(text='🚫 Spam đang chạy!'), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
                return
            parts = message.split(' ', 1)
            if len(parts) < 2:
                self.replyMessage(Message(text='🚫 Vui lòng cung cấp nội dung đi chứ Admin'), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
                return
            spam_content = parts[1]
            self.spamming = True
            self.spam_thread = threading.Thread(target=self.spam_message, 
                                               args=(spam_content, thread_id, thread_type))
            self.spam_thread.start()
            return

        if message.startswith(".stop"):
            if not self.spamming:
                self.replyMessage(Message(text='🚫 Không có spam nào đang chạy!'), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
                return
            self.spamming = False
            if self.spam_thread is not None:
                self.spam_thread.join()
            self.replyMessage(Message(text='✅ Đã dừng spam.'), 
                            message_object, thread_id=thread_id, thread_type=thread_type)
            return

        if message.startswith(".admin"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
                return
            parts = message.split(' ', 1)
            if len(parts) < 2:
                self.replyMessage(Message(text='🚫 Vui lòng cung cấp user_id để thêm làm admin.'), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
                return
            new_admin_id = parts[1]
            idadmin.add(new_admin_id)
            self.save_admins(idadmin)
            self.replyMessage(Message(text=f'✅ Đã thêm {new_admin_id} vào danh sách admin.'), 
                            message_object, thread_id=thread_id, thread_type=thread_type)
            return

        if message.startswith(".info"):
            self.replyMessage(Message(text=f'ID của bạn: {author_id}'), 
                            message_object, thread_id=thread_id, thread_type=thread_type)
            return

        if message.startswith(".ask"):
            parts = message.split(' ', 1)
            if len(parts) < 2:
                self.replyMessage(Message(text='🚫 Vui lòng nhập nội dung😒.'), 
                                message_object, thread_id=thread_id, thread_type=thread_type)
                return
            user_message = parts[1]
            self.handle_ai_request(user_message, thread_id, thread_type, author_id, message_object)
            return

        # Auto AI response for non-command messages
        try:
            if author_id == self.uid:
                pass
            else:
                command_prefixes = ['.', '/', 'tb', 'all', 'mute', 'mu', 'unmute', 
                                  'game', 'vip', 'sms', 'checkon', 'checkoff']
                is_command = any(message_text.lower().startswith(prefix.lower()) 
                               for prefix in command_prefixes)
                
                if not is_command:
                    command_content = message_text[5:].strip() if message_text.lower().startswith("@lynk") else message_text
                    if not command_content:
                        command_content = "Chào bạn"
                    self.handle_ai_request(command_content, thread_id, thread_type, author_id, message_object)
                    return
        except Exception as e:
            print(f"Lỗi kích hoạt AI: {e}")

        # Mute/Unmute logic
        if self.xoatn_mode and self.messages_to_delete:
            for msg_obj in self.messages_to_delete:
                try:
                    self.deleteGroupMsg(msgId=msg_obj.msgId, clientMsgId=msg_obj.cliMsgId, 
                                      ownerId=author_id, groupId=thread_id)
                except Exception as e:
                    print(f'Error deleting message: {e}')
            self.messages_to_delete.clear()

        if self.isUndoLoop:
            if author_id not in idadmin:
                mutenguoidung = self.load_mutenguoidung()
                if author_id in mutenguoidung:
                    self.deleteGroupMsg(msgId=message_object.msgId, 
                                      clientMsgId=message_object.cliMsgId, 
                                      ownerId=author_id, groupId=thread_id)


# ==================== ESCAPE GAME AUTO-BET THREAD (ĐÃ NÂNG CẤP) ====================

def escape_autobet_loop(bot_instance):
    """Background thread for Escape Game auto-betting"""
    # Khai báo các biến global
    global escape_predicted_room, escape_use_autobet, escape_issue_id, escape_count_down
    global escape_ai_follow, escape_bet_amount, selected_currency_unit
    # Khai báo các biến để cập nhật status
    global ai1_choice, ai2_choice, ai3_choice, advanced_choice, advanced_confidence
    
    last_bet_issue = None
    
    while True:
        try:
            # 1. Phân tích dữ liệu (Chạy liên tục để cập nhật status cho Zalo)
            (
                new_issue_id, sorted_rates, killed_room_name, trends, 
                temp_ai1, temp_ai2, temp_ai3, temp_adv, 
                temp_conf, patterns
            ) = escape_analyze_data(selected_currency_unit)
            
            # Cập nhật biến toàn cục để lệnh .escape status có thể thấy
            ai1_choice = temp_ai1
            ai2_choice = temp_ai2
            ai3_choice = temp_ai3
            advanced_choice = temp_adv
            advanced_confidence = temp_conf

            # 2. Kiểm tra điều kiện auto-bet
            if not escape_use_autobet:
                time.sleep(1) # Nếu không bật auto-bet, nghỉ 1s rồi phân tích lại
                continue
            
            # 3. Logic Auto-bet
            if escape_issue_id and escape_issue_id != last_bet_issue:
                
                # Chọn phòng dựa trên AI
                target_choice_name = {
                    "1": ai1_choice,
                    "2": ai2_choice,
                    "3": ai3_choice,
                    "5": advanced_choice
                }.get(escape_ai_follow, advanced_choice) # Mặc định là AI Nâng cao nếu cài đặt sai
                
                if target_choice_name and target_choice_name != "N/A":
                    # Cập nhật dự đoán toàn cục (cho lệnh .escape)
                    escape_predicted_room = room_names_to_id.get(target_choice_name)
                    
                    # Chờ đến cửa sổ cược (giữ nguyên logic cũ)
                    if escape_count_down and 10 < escape_count_down <= 40:
                        room_id = escape_predicted_room
                        
                        if room_id and ESCAPE_USER_ID and ESCAPE_SECRET_KEY:
                            try:
                                payload = {
                                    "asset_type": selected_currency_unit, # Sử dụng biến tiền tệ
                                    "user_id": ESCAPE_USER_ID,
                                    "room_id": room_id,
                                    "bet_amount": escape_bet_amount
                                }
                                headers = {
                                    "content-type": "application/json",
                                    "user-id": str(ESCAPE_USER_ID),
                                    "user-secret-key": ESCAPE_SECRET_KEY
                                }
                                response = HTTP.post(BET_API_URL, headers=headers, 
                                                   json=payload, timeout=6)
                                
                                if response.status_code == 200:
                                    print(f"✅ (AI {escape_ai_follow}) Đã đặt cược {escape_bet_amount} {selected_currency_unit} vào {target_choice_name}")
                                    last_bet_issue = escape_issue_id
                                else:
                                    print(f"❌ Lỗi đặt cược: {response.text}")
                            except Exception as e:
                                print(f"❌ Exception khi đặt cược: {e}")
            
            time.sleep(2) # Nghỉ 2s rồi phân tích lại
            
        except Exception as e:
            print(f"Lỗi trong escape_autobet_loop: {e}")
            time.sleep(5)


# ==================== MAIN EXECUTION ====================

def start_escape_game():
    """Initialize Escape Game AI"""
    global ESCAPE_USER_ID, ESCAPE_SECRET_KEY
    
    print("🎮 KHỞI ĐỘNG ESCAPE GAME AI")
    print("Nhập thông tin đăng nhập Escape Game:")
    
    try:
        user_input = input("User ID: ").strip()
        ESCAPE_USER_ID = int(user_input)
        ESCAPE_SECRET_KEY = input("Secret Key: ").strip()
        
        print("✅ Đã lưu thông tin Escape Game")
        
        # Start WebSocket
        ws_thread = threading.Thread(target=escape_start_ws, daemon=True)
        ws_thread.start()
        
        print("✅ Đã kết nối WebSocket Escape Game")
        
    except Exception as e:
        print(f"❌ Lỗi khởi động Escape Game: {e}")


if __name__ == "__main__":
    # *** THÊM: Khởi tạo DB cho AI mới ***
    init_database()

    print("="*60)
    print("🤖 ZALO BOT + ESCAPE GAME AI (NÂNG CẤP) - MERGED VERSION")
    print("="*60)
    
    # Ask user if they want to enable Escape Game
    enable_escape = input("\nBật chức năng Escape Game AI? (y/n): ").strip().lower()
    
    if enable_escape == 'y':
        start_escape_game()
        time.sleep(2)  # Give WS time to connect
    
    print("\n🚀 Khởi động Zalo Bot...")
    
    # Zalo Bot credentials
    imei = "81db0a4e-95be-4fc3-ac16-f81750a79326-bfe921b394bf10c8d08c5999edfccc8d"  # Nhập IMEI của bạn
    session_cookies = ({"_ga_YS1V643LGV":"GS2.1.s1762027741$o1$g0$t1762027742$j59$l0$h0","_ga":"GA1.2.441592679.1762027741","_ga_RYD7END4JE":"GS2.2.s1762027741$o1$g1$t1762027742$j59$l0$h0","_zlang":"vn","__zi":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8WwdkYjbqzKXN-Pvg_PJb64UftXgp4m.1","__zi-legacy":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8WwdkYjbqzKXN-Pvg_PJb64UftXgp4m.1","_ga_3EM8ZPYYN3":"GS2.2.s1762368496$o5$g0$t1762368496$j60$l0$h0","ozi":"2000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjMXe9fFM8ysaUIZaaDMYpQThwQLJ1YACvogef987eu.1","app.event.zalo.me":"8273931364281912667","_gid":"GA1.2.675430665.1762358878","_gat":"1","zpsid":"3oyV.447599694.2.imYGb3G9QKDwtSHPE0bfGq5w6tS0Fbnw3JzGTq9EnQhwu-R3DVBoI5q9QKC","zpw_sek":"YHdb.447599694.a0.Y6gBxO5Bt1tFdt47e4lS7VffkNQZSVvwinkFKRS4bIsk9gbvwG-UBx0acMVGTk4__3sRiMY5Df81IYU6YYBS7G"})  # Nhập session cookies
    
    # Create bot instance
    honhattruong = Honhattruong('api_key', 'secret_key', imei=imei, 
                                session_cookies=session_cookies)
    
    # Start Escape Game auto-bet thread if enabled
    if enable_escape == 'y':
        autobet_thread = threading.Thread(target=escape_autobet_loop, 
                                         args=(honhattruong,), daemon=True)
        autobet_thread.start()
        print("✅ Đã khởi động Auto-bet (với AI nâng cao)")
    
    print("\n✅ Bot đã sẵn sàng!")
    print("📱 Các lệnh Escape Game (Nâng cấp):")
    print("   .escape - Xem trạng thái & 4 dự đoán AI")
    print("   .escape start/stop - Bật/tắt auto-bet")
    print("   .escape bet <số> - Đặt số tiền cược")
    print("   .escape ai <số> - Chọn AI để theo (1, 2, 3, hoặc 5)")
    print("\n💬 Gõ /menu trong Zalo để xem tất cả lệnh!")
    print("="*60)
    
    # Start Zalo bot
    honhattruong.listen()