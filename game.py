# CÁC IMPORT CŨ CỦA HHHH.PY
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

# =================================================================
# ===== CÁC IMPORT MỚI TỪ BUMX.PY =====
# =================================================================
# Đảm bảo bạn đã chạy: pip install numpy scikit-learn pytz websocket-client
import sys
import logging
import math
from collections import deque, Counter
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, Tuple, Optional, List
import numpy as np
import sqlite3
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import pytz
import websocket
import ssl
# =================================================================
# ===== KẾT THÚC IMPORT MỚI =====
# =================================================================


# =================================================================
# ===== CÁC HẰNG SỐ VÀ CONFIG TỪ BUMX.PY =====
# =================================================================
tz = pytz.timezone("Asia/Ho_Chi_Minh")

# Thiết lập logger cho bot game
logger = logging.getLogger("escape_vip_ai_merged")
logger.setLevel(logging.INFO)
logger.addHandler(logging.FileHandler("escape_vip_ai_merged.log", encoding="utf-8"))

BET_API_URL = "https://api.escapemaster.net/escape_game/bet"
WS_URL = "wss://api.escapemaster.net/escape_master/ws"
WALLET_API_URL = "https://wallet.3games.io/api/wallet/user_asset"

# HTTP Session cho bot game
HTTP = requests.Session()
try:
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    adapter = HTTPAdapter(
        pool_connections=20, pool_maxsize=50,
        max_retries=Retry(total=3, backoff_factor=0.2,
                          status_forcelist=(500, 502, 503, 504))
    )
    HTTP.mount("https://", adapter)
    HTTP.mount("http://", adapter)
except Exception:
    pass

ROOM_NAMES = {
    1: "📦 Nhà kho", 2: "🪑 Phòng họp", 3: "👔 Phòng giám đốc", 4: "💬 Phòng trò chuyện",
    5: "🎥 Phòng giám sát", 6: "🏢 Văn phòng", 7: "💰 Phòng tài vụ", 8: "👥 Phòng nhân sự"
}
ROOM_ORDER = [1, 2, 3, 4, 5, 6, 7, 8]
room_names_to_id = {name: num for num, name in ROOM_NAMES.items()}
room_names_map_str = {str(num): name for num, name in ROOM_NAMES.items()} 
room_ids_map_str = {name: str(num) for num, name in ROOM_NAMES.items()} 
CURRENCY_UNITS = ["BUILD", "USDT", "XWORLD"]
_num_re = re.compile(r"-?\d+[\d,]*\.?\d*")

# =================================================================
# ===== CÁC LỚP AI VÀ LOGIC TỪ BUMX.PY =====
# =================================================================

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
        self.win_history = {room: deque(maxlen=50) for room in ROOM_NAMES.values()} 

    def extract_features(self, room_state_data, rates_10, rates_100, trends, killer_history, current_time):
        features = []
        for i in ROOM_ORDER:
            room_name = ROOM_NAMES[i]
            # Sử dụng dữ liệu room_state được truyền vào
            state = room_state_data.get(i, {})
            players = state.get("players", 0)
            total_bet = state.get("bet", 0)
            avg_bet = total_bet / players if players > 0 else 0
            influx = state.get("player_influx", 0) 
            features.extend([
                rates_10.get(room_name, 100),
                rates_100.get(room_name, 100),
                trends.get(room_name, (0, False, 0))[0],
                1 if trends.get(room_name, (0, False, 0))[1] else 0,
                trends.get(room_name, (0, False, 0))[2],
                avg_bet,
                influx
            ])
        
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

    def train_models(self, training_data, room_state_data): # Thêm room_state_data
        if len(training_data) < 50:
            logger.warning("Not enough data to train AI models (< 50).")
            return False
        try:
            X = []
            y = []
            room_name_list = list(ROOM_NAMES.values())
            for data in training_data:
                features = self.extract_features(
                    room_state_data, # Dùng room_state_data hiện tại
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

    def predict_advanced(self, room_state_data, rates_10, rates_100, trends, killer_history):
        if not self.is_trained:
            return self.fallback_prediction(room_state_data, rates_10, rates_100, trends)
        
        current_time = datetime.now(tz)
        features = self.extract_features(room_state_data, rates_10, rates_100, trends, killer_history, current_time)
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
        
        return self.fallback_prediction(room_state_data, rates_10, rates_100, trends)

    def fallback_prediction(self, room_state_data, rates_10, rates_100, trends):
        room_scores = {}
        for room_name in ROOM_NAMES.values():
            base_score = (rates_10.get(room_name, 100) * 0.4 + rates_100.get(room_name, 100) * 0.6)
            trend_data = trends.get(room_name, (0, False, 0))
            trend_diff, is_overdue, _ = trend_data
            if trend_diff > 0.1:
                base_score -= (trend_diff * 20)
            if is_overdue:
                base_score += 5.0
            
            rid = room_names_to_id.get(room_name)
            if rid:
                state = room_state_data.get(rid, {})
                players = state.get("players", 0)
                total_bet = state.get("bet", 0)
                avg_bet = total_bet / players if players > 0 else 0
                influx = state.get("player_influx", 0)
                base_score -= avg_bet * 0.05 
                base_score += influx * 0.02
            
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

# =================================================================
# ===== LỚP BOT GAME (CHỨA TOÀN BỘ LOGIC BUMX.PY) =====
# =================================================================

class GameBot(threading.Thread):
    def __init__(self, zalo_bot_instance, user_id, secret_key, bet_amount, asset_type="BUILD", ai_to_follow="5"):
        super().__init__(daemon=True)
        
        # --- Cầu nối về Zalo Bot ---
        self.zalo_bot = zalo_bot_instance 
        
        # --- Config từ Zalo ---
        self.USER_ID = int(user_id)
        self.SECRET_KEY = str(secret_key)
        self.base_bet = float(bet_amount) # Đổi tên từ bet_amount
        self.selected_currency_unit = asset_type
        self.ai_to_follow = str(ai_to_follow)
        
        # --- Cờ kiểm soát thread ---
        self.stop_flag = False
        
        # --- Toàn bộ "globals" từ bumx.py được chuyển thành "self" ---
        self.issue_id: Optional[int] = None
        self.issue_start_ts: Optional[float] = None
        self.count_down: Optional[int] = None
        self.killed_room: Optional[int] = None
        self.round_index: int = 0
        self.total_rounds_played: int = 0
        
        self.room_state: Dict[int, Dict[str, Any]] = {r: {"players": 0, "bet": 0, "player_influx": 0, "last_players": 0} for r in ROOM_ORDER}
        self.room_stats: Dict[int, Dict[str, Any]] = {r: {"kills": 0, "survives": 0, "last_kill_round": None, "last_players": 0, "last_bet": 0} for r in ROOM_ORDER}

        self.predicted_room: Optional[int] = None 
        self.last_killed_room: Optional[int] = None
        self.prediction_locked: bool = False

        self.current_balance: Optional[float] = None
        self.starting_balance: Optional[float] = None
        self.total_profit: float = 0.0
        self.last_balance_ts: Optional[float] = None
        self.last_balance_val: Optional[float] = None

        self.win_streak: int = 0
        self.lose_streak: int = 0
        self.max_win_streak: int = 0
        self.max_lose_streak: int = 0

        self.use_autobet: bool = True # Bot này luôn tự cược
        self.stop_loss: float = 0.0 # Có thể set qua Zalo nếu muốn
        self.capital_preservation_threshold: float = 0.0
        self.auto_bet_paused: bool = False
        self.max_bet_multiplier: float = 2.0  
        self.min_confidence_for_bet_increase: float = 0.7 

        self.bet_history: deque = deque(maxlen=500)
        self.bet_sent_for_issue: set = set()
        self.bet_pending_for_issue: set = set()

        self.last_msg_ts: float = time.time()
        self.BALANCE_POLL_INTERVAL: float = 4.0
        self._ws: Dict[str, Any] = {"ws": None} # Chứa instance WebSocket

        self.killer_history: List[Dict[str, Any]] = []
        self.stats = {
            'ai1': {'games': 0, 'wins': 0, 'streak': 0},
            'ai2': {'games': 0, 'wins': 0, 'streak': 0},
            'ai3': {'games': 0, 'wins': 0, 'streak': 0},
            'adv': {'games': 0, 'wins': 0, 'streak': 0}
        }
        self.scored_issue: set = set()
        self.pending_choices: Dict[str, Optional[str]] = {'ai1': None, 'ai2': None, 'ai3': None, 'adv': None, 'user_choice': None}
        self.is_fallback_mode: bool = False

        # --- AI Instance ---
        self.ai_system = AdvancedAISystem()

    # --- Các hàm (hàm global) từ bumx.py giờ là method của GameBot ---
    
    def log_debug(self, msg: str):
        try:
            logger.debug(msg)
        except Exception:
            pass

    def _parse_number(self, x: Any) -> Optional[float]:
        # (Giữ nguyên logic từ bumx.py)
        if x is None: return None
        if isinstance(x, (int, float)): return float(x)
        s = str(x)
        m = _num_re.search(s)
        if not m: return None
        token = m.group(0).replace(",", "")
        try:
            return float(token)
        except Exception:
            return None

    def human_ts(self) -> str:
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    def api_headers(self) -> Dict[str, str]:
        return {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0", 
            "user-id": str(self.USER_ID) if self.USER_ID else "",
            "user-secret-key": self.SECRET_KEY if self.SECRET_KEY else ""
        }

    def fetch_data(self, url, headers, silent=False):
        try:
            response = HTTP.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                j = response.json()
                if j.get('code') == 0:
                    return j.get('data')
            if not silent:
                logger.warning(f"Fetch_data error {url}: HTTP {response.status_code} {response.text}")
            return None
        except Exception as e:
            if not silent:
                logger.error(f"Fetch_data exception {url}: {e}")
            return None

    def _parse_balance_from_json(self, j: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        # (Giữ nguyên logic từ bumx.py)
        if not isinstance(j, dict): return None, None, None
        build, world, usdt = None, None, None
        data = j.get("data") if isinstance(j.get("data"), dict) else j
        if isinstance(data, dict):
            cwallet = data.get("cwallet") if isinstance(data.get("cwallet"), dict) else None
            if cwallet:
                for key in ("ctoken_contribute", "ctoken", "build", "balance", "amount"):
                    if key in cwallet and build is None: build = self._parse_number(cwallet.get(key))
            for k in ("build", "ctoken", "ctoken_contribute"):
                if build is None and k in data: build = self._parse_number(data.get(k))
            for k in ("usdt", "kusdt", "usdt_balance"):
                if usdt is None and k in data: usdt = self._parse_number(data.get(k))
            for k in ("world", "xworld"):
                if world is None and k in data: world = self._parse_number(data.get(k))
        return build, world, usdt

    def balance_headers_for(self, uid: Optional[int] = None, secret: Optional[str] = None) -> Dict[str, str]:
        # (Giữ nguyên logic từ bumx.py)
        h = {
            "accept": "*/*", "accept-language": "vi,en;q=0.9", "cache-control": "no-cache",
            "country-code": "vn", "origin": "https://xworld.info", "pragma": "no-cache",
            "referer": "https://xworld.info/",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
            "user-login": "login_v2", "xb-language": "vi-VN",
        }
        if uid is not None: h["user-id"] = str(uid)
        if secret: h["user-secret-key"] = str(secret)
        return h

    def fetch_balances_3games(self, retries=2, timeout=6, params=None, uid=None, secret=None):
        uid = uid or self.USER_ID
        secret = secret or self.SECRET_KEY
        payload = {"user_id": int(uid) if uid is not None else None, "source": "home"}
        
        current_val = None
        if self.selected_currency_unit == "BUILD": current_val = self.current_balance
        # (Need to add USDT/WORLD if used)

        attempt = 0
        while attempt <= retries:
            attempt += 1
            try:
                r = HTTP.post(
                    WALLET_API_URL,
                    json=payload,
                    headers=self.balance_headers_for(uid, secret),
                    timeout=timeout,
                )
                r.raise_for_status()
                j = r.json()

                build, world, usdt = self._parse_balance_from_json(j)
                
                new_val = None
                if self.selected_currency_unit == "BUILD": new_val = build
                elif self.selected_currency_unit == "USDT": new_val = usdt
                elif self.selected_currency_unit == "XWORLD": new_val = world

                if new_val is not None:
                    if self.last_balance_val is None:
                        self.starting_balance = new_val
                        self.last_balance_val = new_val
                    else:
                        delta = float(new_val) - float(self.last_balance_val)
                        if abs(delta) > 0.0001: 
                            self.total_profit += delta
                            self.last_balance_val = new_val
                    self.current_balance = new_val
                
                self.last_balance_ts = time.time()
                return self.current_balance

            except Exception as e:
                self.log_debug(f"wallet fetch attempt {attempt} error: {e}")
                time.sleep(min(0.6 * attempt, 2))

        return self.current_balance

    def place_bet_http(self, issue: int, room_id: int, amount: float) -> dict:
        payload = {"asset_type": self.selected_currency_unit, "user_id": self.USER_ID, "room_id": int(room_id), "bet_amount": float(amount)}
        try:
            r = HTTP.post(BET_API_URL, headers=self.api_headers(), json=payload, timeout=6)
            try:
                return r.json()
            except Exception:
                return {"raw": r.text, "http_status": r.status_code}
        except Exception as e:
            return {"error": str(e)}

    def record_bet(self, issue: int, room_id: int, amount: float, resp: dict, algo_used: Optional[str] = None) -> dict:
        now = datetime.now(tz).strftime("%H:%M:%S")
        success = False
        if isinstance(resp, dict) and (resp.get("msg") == "ok" or resp.get("code") == 0 or resp.get("status") in ("ok", 1)):
            success = True
        
        rec = {
            "issue": issue, "room": room_id, "amount": float(amount), "time": now, 
            "resp": resp, "result": "Đang", "algo": algo_used, "delta": 0.0, 
            "win_streak": self.win_streak, "lose_streak": self.lose_streak, "placed": success
        }
        self.bet_history.append(rec)
        if success:
            try:
                self.bet_sent_for_issue.add(issue)
            except Exception:
                pass
        return rec

    def place_bet_async(self, issue: int, room_id: int, amount: float, algo_used: Optional[str] = None, jitter: float = 0.25):
        try:
            self.bet_pending_for_issue.add(issue)
        except Exception:
            pass
        
        def worker():
            try:
                # Gửi thông báo đặt cược qua Zalo
                prediction_message = (
                    f"🤖[GameBot] Ván {issue}\n"
                    f"🔥 Đang cược: {amount:.4f} {self.selected_currency_unit} -> {ROOM_NAMES.get(room_id, room_id)}\n"
                    f"📈 Thuật toán: {algo_used}"
                )
                self.zalo_bot.broadcast_game_message(prediction_message)

                time.sleep(random.uniform(0.02, jitter))
                res = self.place_bet_http(issue, room_id, amount)
                rec = self.record_bet(issue, room_id, amount, res, algo_used=algo_used)
                
                if isinstance(res, dict) and (res.get("msg") == "ok" or res.get("code") == 0 or res.get("status") in ("ok", 1)):
                    logger.info(f"✅ Đặt thành công {amount} {self.selected_currency_unit} vào {ROOM_NAMES.get(room_id, room_id)} (v{issue}).")
                else:
                    logger.error(f"❌ Đặt lỗi v{issue}: {res}")
                    self.zalo_bot.broadcast_game_message(f"🤖[GameBot] ❌ Đặt cược ván {issue} THẤT BẠI. Lỗi: {res}")
            
            except Exception as e:
                logger.error(f"Lỗi khi đặt cược: {e}")
                self.zalo_bot.broadcast_game_message(f"🤖[GameBot] ❌ Lỗi nghiêm trọng khi đặt cược: {e}")
            finally:
                try:
                    self.bet_pending_for_issue.discard(issue)
                except Exception:
                    pass
        threading.Thread(target=worker, daemon=True).start()

    def analyze_data(self, headers, asset_mode):
        TREND_MULTIPLIER = 15
        OVERDUE_THRESHOLD = 20
        OVERDUE_PENALTY = 4.0

        url_10 = f"https://api.escapemaster.net/escape_game/recent_10_issues?asset={asset_mode}"
        url_100_stats = f"https://api.escapemaster.net/escape_game/recent_100_issues?asset={asset_mode}"
        url_100_list = f"https://api.escapemaster.net/escape_game/recent_issues?asset={asset_mode}&page=1&limit=100"
        
        data_10 = self.fetch_data(url_10, headers, silent=True)
        data_100_stats = self.fetch_data(url_100_stats, headers, silent=True)
        data_100_list = self.fetch_data(url_100_list, headers, silent=True)
        
        if not all([data_10, data_100_stats]):
            logger.warning("Failed to fetch critical AI data (10 or 100 stats).")
            return None, [], "N/A", {}, "N/A", "N/A", "N/A", "N/A", 0, {}
        
        self.is_fallback_mode = data_100_list is None
        if self.is_fallback_mode:
            logger.warning("Falling back, 100 issue list not available.")

        current_issue = data_10[0]
        current_issue_id = current_issue.get('issue_id')
        try:
            killed_room_id = int(current_issue.get('killed_room_id'))
        except Exception:
            killed_room_id = 0
        current_killed_room_name = ROOM_NAMES.get(killed_room_id, "N/A")
        
        if current_issue_id and current_issue_id not in [h['issue'] for h in self.killer_history]:
            self.killer_history.append({'issue': current_issue_id, 'room': current_killed_room_name})
            if len(self.killer_history) > 100:
                self.killer_history.pop(0)

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
        if not self.is_fallback_mode:
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
            is_overdue = (rounds_since_kill.get(room_name, 0) > OVERDUE_THRESHOLD) if not self.is_fallback_mode else False
            trends[room_name] = (trend_diff, is_overdue, rounds_since_kill.get(room_name, 0) if not self.is_fallback_mode else 0)
        
        if not self.ai_system.is_trained and not self.is_fallback_mode and len(data_100_list) > 50:
            self.zalo_bot.broadcast_game_message("🤖[GameBot] Đang huấn luyện AI với dữ liệu lịch sử...")
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
            self.ai_system.train_models(training_data, self.room_state) # Truyền self.room_state
        
        best_room, confidence, model_predictions = self.ai_system.predict_advanced(self.room_state, rates_10, rates_100, trends, self.killer_history)
        
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
        
        def prioritize_low_bet_amount(choices: List[str]) -> str:
            if not choices or (len(choices) == 1 and choices[0] == "N/A"):
                return "N/A"
            
            valid_choices = [c for c in choices if c != "N/A"]
            if not valid_choices: return "N/A"
            if len(valid_choices) == 1: return valid_choices[0]

            bets = {}
            for room_name in valid_choices:
                rid = room_names_to_id.get(room_name)
                if rid and rid in self.room_state:
                    bets[room_name] = self.room_state[rid].get("bet", float('inf')) 
                else:
                    bets[room_name] = float('inf')
            
            if not bets: return valid_choices[0] 
            return min(bets, key=bets.get)
        
        ai1_choice = prioritize_low_bet_amount([ai1_choice])
        ai2_choice = prioritize_low_bet_amount([ai2_choice])
        ai3_choice = prioritize_low_bet_amount([ai3_choice])
        advanced_choice = prioritize_low_bet_amount([advanced_choice])

        patterns = self.ai_system.pattern_detector.detect_patterns(self.killer_history)
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
            logger.error(f"Database save error: {e}")

        return current_issue_id, sorted_rates, current_killed_room_name, trends, ai1_choice, ai2_choice, ai3_choice, advanced_choice, confidence, patterns

    # --- Các hàm Callback của WebSocket ---
    
    def _extract_issue_id(self, d: Dict[str, Any]) -> Optional[int]:
        # (Giữ nguyên logic từ bumx.py)
        if not isinstance(d, dict): return None
        possible = []
        for key in ("issue_id", "issueId", "issue", "id"):
            v = d.get(key)
            if v is not None: possible.append(v)
        if isinstance(d.get("data"), dict):
            for key in ("issue_id", "issueId", "issue", "id"):
                v = d["data"].get(key)
                if v is not None: possible.append(v)
        for p in possible:
            try: return int(p)
            except Exception:
                try: return int(str(p))
                except Exception: continue
        return None

    def on_ws_open(self, ws):
        self._ws["ws"] = ws
        self.zalo_bot.broadcast_game_message("🤖[GameBot] ĐÃ KẾT NỐI DỮ LIỆU GAME.")
        try:
            payload = {"msg_type": "handle_enter_game", "asset_type": self.selected_currency_unit, "user_id": self.USER_ID, "user_secret_key": self.SECRET_KEY}
            ws.send(json.dumps(payload))
        except Exception as e:
            logger.error(f"on_open send error: {e}")

    def _background_fetch_balance_after_result(self):
        try:
            self.fetch_balances_3games()
        except Exception:
            pass

    def _mark_bet_result_from_issue(self, res_issue: Optional[int], krid: int):
        if res_issue is None:
            return None
        rec = None
        for b in reversed(self.bet_history):
            try:
                if int(b.get("issue")) == int(res_issue) and b.get("placed"):
                    rec = b
                    break
            except Exception:
                continue
        if rec is None:
            self.log_debug(f"No placed bet found for issue {res_issue} — skip result marking.")
            return None

        try:
            placed_room = int(rec.get("room"))
            if placed_room == int(krid):
                rec["result"] = "Thua"
                self.lose_streak += 1
                self.win_streak = 0
                if self.lose_streak > self.max_lose_streak:
                    self.max_lose_streak = self.lose_streak
            else:
                rec["result"] = "Thắng"
                rec["delta"] = (float(rec.get("amount", 0)) * 7) 
                self.win_streak += 1
                self.lose_streak = 0
                if self.win_streak > self.max_win_streak:
                    self.max_win_streak = self.win_streak
            return rec # Trả về record để thông báo
        except Exception as e:
            self.log_debug(f"_mark_bet_result_from_issue err: {e}")
            return None

    def on_ws_message(self, ws, message):
        self.last_msg_ts = time.time()
        try:
            if isinstance(message, bytes):
                try: message = message.decode("utf-8", errors="replace")
                except Exception: message = str(message)
            data = None
            try: data = json.loads(message)
            except Exception:
                try: data = json.loads(message.replace("'", '"'))
                except Exception:
                    self.log_debug(f"on_message non-json: {str(message)[:200]}")
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
            new_issue = self._extract_issue_id(data)
            
            message_asset_type = (data.get("asset_type") or "").upper()
            if message_asset_type and message_asset_type != self.selected_currency_unit:
                logger.debug(f"Ignored WS message: asset_type ({message_asset_type}) != {self.selected_currency_unit}")
                return

            if msg_type == "notify_issue_stat" or "issue_stat" in msg_type:
                rooms = data.get("rooms") or []
                if not rooms and isinstance(data.get("data"), dict):
                    rooms = data["data"].get("rooms", [])
                
                for rm in (rooms or []):
                    try:
                        rid = int(rm.get("room_id") or rm.get("roomId") or rm.get("id"))
                        if rid not in ROOM_ORDER: continue
                        
                        last_players = self.room_state[rid].get("last_players", 0)
                        players = int(rm.get("user_cnt") or rm.get("userCount") or 0) or 0
                        bet = float(rm.get("total_bet_amount") or rm.get("totalBet") or rm.get("bet") or 0) or 0
                        
                        self.room_state[rid] = {
                            "players": players, 
                            "bet": bet, 
                            "player_influx": players - last_players, 
                            "last_players": players
                        }
                        
                        self.room_stats[rid]["last_players"] = players
                        self.room_stats[rid]["last_bet"] = bet
                    except Exception as e:
                        logger.warning(f"Error processing room stat: {e} | data: {rm}")
                        
                if new_issue is not None and new_issue != self.issue_id:
                    self.issue_id = new_issue
                    self.issue_start_ts = time.time()
                    self.round_index += 1
                    self.killed_room = None
                    self.prediction_locked = False
                    self.predicted_room = None
                    self.pending_choices = {'ai1': None, 'ai2': None, 'ai3': None, 'adv': None, 'user_choice': None}
                    
                    # Thông báo ván mới cho Zalo
                    self.zalo_bot.broadcast_game_message(f"--- 🤖[GameBot] Ván mới: {self.issue_id} ---")
                    
            elif msg_type == "notify_count_down" or "count_down" in msg_type:
                self.count_down = data.get("count_down") or data.get("countDown") or data.get("count") or self.count_down
                try:
                    count_val = int(self.count_down)
                except Exception:
                    count_val = None
                
                if count_val is not None:
                    if count_val <= 10 and not self.prediction_locked:
                        self.prediction_locked = True 

            elif msg_type == "notify_result" or "result" in msg_type:
                kr = data.get("killed_room") if data.get("killed_room") is not None else data.get("killed_room_id")
                if kr is None and isinstance(data.get("data"), dict):
                    kr = data["data"].get("killed_room") or data["data"].get("killed_room_id")
                
                if kr is not None:
                    try: krid = int(kr)
                    except Exception: krid = 0 
                    
                    if krid in ROOM_ORDER:
                        self.killed_room = krid
                        self.last_killed_room = krid

                        for rid in ROOM_ORDER:
                            if rid == krid:
                                self.room_stats[rid]["kills"] += 1
                                self.room_stats[rid]["last_kill_round"] = self.round_index
                            else:
                                self.room_stats[rid]["survives"] += 1
                        
                        try: self.total_rounds_played += 1
                        except Exception: pass

                        res_issue = new_issue if new_issue is not None else self.issue_id
                        killed_room_name = ROOM_NAMES.get(krid, "N/A")

                        if res_issue and res_issue not in self.scored_issue:
                            logger.info(f"Scoring result for issue {res_issue}. Killed: {killed_room_name}. Pending: {self.pending_choices}")
                            
                            for ai_key, choice in self.pending_choices.items():
                                if ai_key == 'user_choice' or not choice or choice == "N/A":
                                    continue
                                
                                self.stats[ai_key]['games'] += 1
                                is_win = (killed_room_name != choice)
                                if is_win:
                                    self.stats[ai_key]['wins'] += 1
                                    self.stats[ai_key]['streak'] += 1
                                else:
                                    self.stats[ai_key]['streak'] = 0
                                
                                self.ai_system.update_win_history(choice, is_win) 
                                logger.info(f"AI {ai_key} predicted {choice}, actual {killed_room_name}, result {'Win' if is_win else 'Loss'}")
                            
                            self.scored_issue.add(res_issue)
                        
                        # Xử lý kết quả cược VÀ lấy record
                        bet_record = self._mark_bet_result_from_issue(res_issue, krid)
                        
                        # --- GỬI THÔNG BÁO KẾT QUẢ QUA ZALO ---
                        self.fetch_balances_3games() # Cập nhật số dư/lãi lỗ
                        
                        result_message = (
                            f"--- 🤖[GameBot] Kết quả ván {res_issue} ---\n"
                            f"☠️ Sát thủ: {killed_room_name}\n"
                        )
                        if bet_record and bet_record.get('placed'):
                            result_message += f"🎯 Kết quả cược: {bet_record.get('result', 'N/A')}\n"
                        else:
                            result_message += "🎯 Kết quả cược: (Không cược)\n"
                        
                        result_message += f"💰 Lãi/Lỗ hiện tại: {self.total_profit:+.4f}\n"
                        result_message += f"💵 Số dư mới: {self.current_balance:.4f}"
                        
                        self.zalo_bot.broadcast_game_message(result_message)
                        # --- KẾT THÚC THÔNG BÁO ---

                        # (Không cần check stop_flag ở đây nữa, vòng lặp chính sẽ check)
        except Exception as e:
            self.log_debug(f"on_ws_message err: {e}")

    def on_ws_close(self, ws, code, reason):
        self.log_debug(f"WS closed: {code} {reason}")
        self._ws["ws"] = None 

    def on_ws_error(self, ws, err):
        self.log_debug(f"WS error: {err}")

    def _on_ws_ping(self, wsapp, message):
        self.log_debug("Received ping")

    def _on_ws_pong(self, wsapp, message):
        self.log_debug("Received pong")

    def start_ws(self):
        backoff = 0.8
        while not self.stop_flag:
            try:
                ws_app = websocket.WebSocketApp(
                    WS_URL,
                    on_open=self.on_ws_open,
                    on_message=self.on_ws_message,
                    on_close=self.on_ws_close,
                    on_error=self.on_ws_error,
                    on_ping=self._on_ws_ping,
                    on_pong=self._on_ws_pong,
                )
                self._ws["ws"] = ws_app 

                def heartbeat():
                    while True:
                        if self.stop_flag: break
                        ws_inner = self._ws.get("ws")
                        try:
                            if ws_inner and hasattr(ws_inner, "send"):
                                try:
                                    ws_inner.send(json.dumps({"msg_type": "ping_keepalive"}))
                                except Exception as e:
                                    self.log_debug(f"HB send error: {e}")
                                    break 
                        except Exception as e:
                            self.log_debug(f"HB check error: {e}")
                        
                        for _ in range(8):
                            if self.stop_flag: break
                            time.sleep(1)

                hb_thread = threading.Thread(target=heartbeat, daemon=True)
                hb_thread.start()

                ws_app.run_forever(ping_interval=10, ping_timeout=5, sslopt={"cert_reqs": ssl.CERT_NONE})
            
            except Exception as e:
                self.log_debug(f"start_ws exception: {e}")

            self._ws["ws"] = None 
            if self.stop_flag: break
            
            t = min(backoff + random.random() * 0.6, 30)
            self.log_debug(f"Reconnect WS after {t}s")
            time.sleep(t)
            backoff = min(backoff * 1.6, 30)

    def monitor_loop(self):
        while not self.stop_flag:
            now = time.time()
            
            # Tự động cập nhật số dư
            if (now - (self.last_balance_ts or 0)) > self.BALANCE_POLL_INTERVAL:
                self.fetch_balances_3games()
            
            if now - self.last_msg_ts > 15:
                self.log_debug("No ws msg >15s, send enter_game")
                try:
                    payload = {"msg_type": "handle_enter_game", "asset_type": self.selected_currency_unit, "user_id": self.USER_ID, "user_secret_key": self.SECRET_KEY}
                    wsobj = self._ws.get("ws")
                    if wsobj and hasattr(wsobj, "send"):
                        wsobj.send(json.dumps(payload))
                    else:
                        self.log_debug("monitor_loop: ws object not found or no send method.")
                except Exception as e:
                    self.log_debug(f"monitor send err: {e}")
            
            if now - self.last_msg_ts > 30:
                self.log_debug("No ws msg >30s, force reconnect")
                try:
                    wsobj = self._ws.get("ws")
                    if wsobj:
                        wsobj.close() 
                except Exception as e:
                    self.log_debug(f"monitor close err: {e}")
            
            time.sleep(2.0)

    def init_database(self):
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

    def stop(self):
        """Hàm này được gọi từ Zalo bot để dừng thread"""
        self.stop_flag = True
        try:
            wsobj = self._ws.get("ws")
            if wsobj:
                wsobj.close()
        except Exception:
            pass

    def run(self):
        """Đây là hàm main() của bumx.py, giờ nó là hàm run() của thread"""
        try:
            self.init_database()
            self.zalo_bot.broadcast_game_message("🤖[GameBot] Đang khởi động... Lấy số dư ban đầu.")
            
            self.fetch_balances_3games() # Lấy số dư lần đầu
            self.zalo_bot.broadcast_game_message(f"🤖[GameBot] Số dư ban đầu: {self.current_balance:.4f} {self.selected_currency_unit}")

            # Khởi động WS và Monitor trong các thread con
            threading.Thread(target=self.start_ws, daemon=True).start()
            threading.Thread(target=self.monitor_loop, daemon=True).start()
            
            self.zalo_bot.broadcast_game_message("🤖[GameBot] ĐÃ KHỞI ĐỘNG. Chờ ván mới...")

            # Vòng lặp chính của AI (thay thế cho vòng lặp UI `rich`)
            while not self.stop_flag:
                # 1. Chạy phân tích
                api_hdrs = self.api_headers()
                
                (
                    new_issue_id, sorted_rates, killed_room_name, trends, 
                    ai1_choice, ai2_choice, ai3_choice, advanced_choice, 
                    advanced_confidence, patterns
                ) = self.analyze_data(api_hdrs, self.selected_currency_unit)
                
                self.pending_choices['ai1'] = ai1_choice
                self.pending_choices['ai2'] = ai2_choice
                self.pending_choices['ai3'] = ai3_choice
                self.pending_choices['adv'] = advanced_choice

                target_choice_name = {"1": ai1_choice, "2": ai2_choice, "3": ai3_choice, "5": advanced_choice}.get(self.ai_to_follow)
                
                if not self.prediction_locked:
                    self.predicted_room = room_names_to_id.get(target_choice_name)

                # 2. Kiểm tra thời gian cược
                elapsed = time.time() - (self.issue_start_ts or 0)
                bet_window_open = (elapsed >= 30 and (self.count_down is None or self.count_down > 10))
                
                if (self.use_autobet and bet_window_open and not self.prediction_locked
                    and not self.auto_bet_paused and self.issue_id 
                    and self.issue_id not in self.bet_sent_for_issue
                    and self.issue_id not in self.bet_pending_for_issue):
                    
                    if self.stop_loss > 0 and self.current_balance is not None and self.current_balance <= self.stop_loss:
                        self.zalo_bot.broadcast_game_message(f"🤖[GameBot] ⚠️ ĐÃ CHẠM NGƯỠNG DỪNG LỖ ({self.stop_loss}). DỪNG TOOL.")
                        self.stop() # Dừng thread
                        continue
                        
                    elif self.capital_preservation_threshold < 0 and self.total_profit <= self.capital_preservation_threshold:
                        self.auto_bet_paused = True
                        self.zalo_bot.broadcast_game_message(f"🤖[GameBot] ⚠️ TỔNG LỖ ĐÃ VƯỢT NGƯỠNG BẢO TOÀN VỐN ({self.capital_preservation_threshold}). TẠM DỪNG AUTO-BET.")
                    
                    else:
                        if target_choice_name and target_choice_name != "N/A":
                            target_room_id = room_names_to_id.get(target_choice_name)
                            
                            adjusted_bet = self.base_bet
                            if advanced_confidence >= self.min_confidence_for_bet_increase:
                                adjusted_bet = min(self.base_bet * self.max_bet_multiplier, self.base_bet * (1 + (advanced_confidence - self.min_confidence_for_bet_increase) * self.max_bet_multiplier))

                            if target_room_id and adjusted_bet > 0:
                                self.prediction_locked = True
                                self.predicted_room = target_room_id
                                
                                # GỌI HÀM CƯỢC (Hàm này sẽ tự gửi thông báo Zalo)
                                self.place_bet_async(
                                    self.issue_id, 
                                    target_room_id, 
                                    float(round(adjusted_bet, 4)), 
                                    algo_used=f"AI_{self.ai_to_follow} (conf: {advanced_confidence:.1%})"
                                )
                                
                                self.pending_choices['user_choice'] = target_choice_name
                        else:
                            logger.warning(f"[GameBot] AI không đưa ra lựa chọn, bỏ qua cược ván {self.issue_id}.")
                            self.prediction_locked = True
                
                # Giảm tải CPU, không cần lặp nhanh như UI
                time.sleep(0.5) 
                
        except Exception as e:
            logger.error(f"Lỗi nghiêm trọng trong GameBot run(): {e}", exc_info=True)
            self.zalo_bot.broadcast_game_message(f"🤖[GameBot] ❌ Lỗi nghiêm trọng: {e}. Thread đã dừng.")
        finally:
            self.zalo_bot.broadcast_game_message("🤖[GameBot] Đã dừng.")


# =================================================================
# ===== LỚP BOT ZALO (HHHH.PY) ĐÃ NÂNG CẤP =====
# =================================================================

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
            # ... (giữ nguyên list màu của bạn) ...
            "#000022", "#000011"
        ]
        self.messages_to_delete = []  
        self.admin_file = 'admin.json'  
        self.start_time = datetime.datetime.now()  
        self.banned_words = set([
            "địt", "lồn", "lol", "đm", "cc", "lon", "đmm", "dm", "dmm", "dit", "cac", "cặc",
            # ... (giữ nguyên list từ cấm của bạn) ...
            "óc lồn", "óc l", "Óc lồnn", "Iồn", "Sút vậc", "Mẹmaybeo", "Cứt", "Cl"
        ])
        self.banned_word_removal_enabled = False 

        # --- PHẦN THÊM MỚI TỪ AI.PY ---
        self.GEMINI_API_KEY = 'AIzaSyCLaCkwaIjv-tk4Z8qKMRn3GxhnJV_Z1lY' 
        self.chat_histories = {} 
        self.INITIAL_PERSONA_PROMPT = "Bạn đóng vai Lynk,là con gái, tính cách của luynk là dâm đãng nói chuyện k có chút ý tứ nào rất dâm và hư hỏng và nói rất ngọt ngào,mỗi tin nhắn của luynk sẽ thả 1 icon tùy theo tâm trạng của luynk ), luynk xưng hô với người khác ngoài Duy Trường thì gọi là anh,đặc biệt là Lynk có thể nhắn dài hết câu)"
        self.HISTORY_DIR = "data/history"
        os.makedirs(self.HISTORY_DIR, exist_ok=True)
        self.ai_allowed_groups = ['ID_NHOM_1', 'ID_NHOM_2'] 

        # ============================================
        # ===== BIẾN TRẠNG THÁI CHO GAMEBOT =====
        # ============================================
        self.game_bot_thread = None
        self.game_bot_instance: Optional[GameBot] = None
        self.game_broadcast_group_id: Optional[str] = None # ID Nhóm Zalo để bot game thông báo
        # ============================================
        
    def load_admins(self):
        try:
            with open(self.admin_file, 'r') as admin_file:
                admin_data = json.load(admin_file)
                return set(admin_data.get('idadmin', []))
        except FileNotFoundError:
            return set()
            
    # ... (TẤT CẢ CÁC HÀM CŨ CỦA BẠN: save_admins, load_registered_users, v.v... GIỮ NGUYÊN) ...
    # ... (Tôi sẽ bỏ qua chúng để tiết kiệm không gian, nhưng chúng vẫn ở đó) ...
    
    def changeGroupName(self, groupName, groupId):
        # (Hàm changeGroupName của bạn)
        params = { "zpw_ver": 641, "zpw_type": 30 }
        payload = { "params": self._encode({ "gname": groupName, "grid": str(groupId) }) }
        response = self._post("https://tt-group-wpa.chat.zalo.me/api/group/updateinfo", params=params, data=payload)
        # (Phần còn lại của hàm)
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

    # ============================================
    # ===== HÀM MỚI ĐỂ NHẬN THÔNG BÁO TỪ GAMEBOT =====
    # ============================================
    def broadcast_game_message(self, text_message: str):
        """Hàm này được gọi từ thread GameBot để gửi tin nhắn Zalo"""
        if self.game_broadcast_group_id:
            try:
                # Gửi tin nhắn với định dạng màu mè (ví dụ)
                style = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(text_message), style="color", color="#00BFFF", auto_format=False), # Màu xanh
                    MessageStyle(offset=0, length=len(text_message), style="font", size="14", auto_format=False),
                ])
                self.send(Message(text=text_message, style=style), thread_id=self.game_broadcast_group_id, thread_type=ThreadType.GROUP)
                print(f"[GameBot -> Zalo]: {text_message}")
            except Exception as e:
                print(f"Lỗi broadcast game: {e}")
        else:
            # Nếu admin chưa set nhóm, chỉ in ra console
            print(f"[GameBot -> Console]: {text_message} (Chưa set nhóm Zalo, dùng lệnh .setgamegroup)")
    # ============================================

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        print(f"\033[32m{message} \033[39m|\033[31m {author_id} \033[39m|\033[33m {thread_id}\033[0m\n")
        content = message_object.content if message_object and hasattr(message_object, 'content') else ""
        if not isinstance(message, str):
            print(f"{type(message)}")
            return

        message_text = message  
        
        idadmin = self.load_admins()

        # ============================================
        # ===== CÁC LỆNH MỚI ĐIỀU KHIỂN GAMEBOT =====
        # ============================================
        
        if message.startswith(".setgamegroup"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền.'), message_object, thread_id, thread_type)
                return
            self.game_broadcast_group_id = thread_id
            self.replyMessage(Message(text=f'✅ Bot game sẽ thông báo tại nhóm này (ID: {thread_id}).'), message_object, thread_id, thread_type)
            return # Dừng xử lý

        if message.startswith(".startgame"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền.'), message_object, thread_id, thread_type)
                return
            if self.game_bot_thread and self.game_bot_thread.is_alive():
                self.replyMessage(Message(text='🚫 Bot game đã chạy rồi.'), message_object, thread_id, thread_type)
                return
                
            parts = message.split()
            if len(parts) != 4:
                self.replyMessage(Message(text='🚫 Sai cú pháp. Dùng: .startgame <game_user_id> <game_secret_key> <bet_amount>'), message_object, thread_id, thread_type)
                return
            
            try:
                game_user_id = int(parts[1])
                game_secret_key = parts[2]
                game_bet_amount = float(parts[3])
                
                # Set nhóm broadcast là nhóm hiện tại nếu chưa set
                if self.game_broadcast_group_id is None:
                    self.game_broadcast_group_id = thread_id
                    self.replyMessage(Message(text=f'⏳ Nhóm thông báo được tự động đặt là nhóm này. Đang khởi động Bot game...'), message_object, thread_id, thread_type)
                else:
                    self.replyMessage(Message(text='⏳ Đang khởi động Bot game...'), message_object, thread_id, thread_type)

                
                # Khởi tạo và chạy thread
                # 'self' (chính là instance Honhattruong) được truyền vào làm cầu nối
                self.game_bot_instance = GameBot(self, game_user_id, game_secret_key, game_bet_amount)
                self.game_bot_thread = self.game_bot_instance
                self.game_bot_thread.start()
                
            except Exception as e:
                self.replyMessage(Message(text=f'🚫 Lỗi khởi động: {e}'), message_object, thread_id, thread_type)
            return # Dừng xử lý

        if message.startswith(".stopgame"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền.'), message_object, thread_id, thread_type)
                return
            if not self.game_bot_thread or not self.game_bot_thread.is_alive():
                self.replyMessage(Message(text='🚫 Bot game không chạy.'), message_object, thread_id, thread_type)
                return
            
            if self.game_bot_instance:
                self.game_bot_instance.stop() # Gửi tín hiệu dừng
                self.replyMessage(Message(text='✅ Đã gửi tínHiệu dừng cho Bot game. Sẽ mất vài giây để dừng hẳn.'), message_object, thread_id, thread_type)
            
            self.game_bot_thread = None
            self.game_bot_instance = None
            return # Dừng xử lý
            
        # ============================================
        # ===== KẾT THÚC LỆNH GAMEBOT =====
        # ============================================

        
        # ... (TẤT CẢ CÁC LỆNH CŨ CỦA BẠN: .kick, .dt, .random, .acclq, vip, tb, .rs, ...) ...
        # ... (Chúng vẫn nằm ở đây, tôi chỉ ẩn đi cho gọn) ...
        
        if message.startswith(".call"):
            if author_id not in idadmin:
                self.replyMessage(Message(text='🚫 Bạn không có quyền sử dụng lệnh này.'), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            # ... (code .call của bạn) ...
            return 

        if message.startswith(".kick"):
            # ... (code .kick của bạn) ...
            return # Thêm return để tránh xung đột
            
        # ... (Thêm return ở cuối mỗi khối lệnh if/elif của bạn) ...

        if message.startswith(".dt"):
            # ... (code .dt của bạn) ...
            return

        # (v.v... cho tất cả các lệnh của bạn)
        
        # ...
        
        # --- PHẦN LOGIC AI CỦA BẠN (LYNK) ---
        # (Phần này phải nằm GẦN CUỐI, sau tất cả các lệnh)
        try:
            if author_id == self.uid:
                pass 
            else:
                command_prefixes = [
                    '.', '/', 'tb', 'all', 'mute', 'mu', 'unmute', 'game', 
                    'vip', 'sms', 'checkon', 'checkoff'
                ]
                
                is_command = False
                for prefix in command_prefixes:
                    if message_text.lower().startswith(prefix.lower()):
                        is_command = True
                        break
                
                if not is_command:
                    command_content = ""
                    if message_text.lower().startswith("@lynk"): 
                        command_content = message_text[5:].strip() 
                    else:
                        command_content = message_text 
                    
                    if not command_content:
                        command_content = "Chào bạn" 
                    
                    # Gọi hàm AI (Lynk)
                    self.handle_ai_request(command_content, thread_id, thread_type, author_id, message_object)
                    
                    return # Đã xử lý bằng AI, dừng
        
        except Exception as e:
            print(f"Lỗi kích hoạt AI: {e}")
        
        # ... (Các logic cuối cùng của bạn như xóa link, xóa tn) ...

    # ... (TẤT CẢ CÁC HÀM CŨ CÒN LẠI CỦA BẠN: send_private_message_to_user, get_random_data, reo_spam_message, handle_kick, ask_api, spam_message, remove_banned_words, add_to_spam_list, download_tiktok_video, và các hàm AI của Lynk ...) ...
    # ... (Tất cả chúng đều được giữ nguyên) ...

# ... (Hàm save_group_ids, load_mutenguoidung, save_mutenguoidung) ...
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

# --- Phần chạy bot ---
if __name__ == "__main__":
    # (Bạn cần điền thông tin đăng nhập Zalo của mình vào đây)
    imei = "81db0a4e-95be-4fc3-ac16-f81750a79326-bfe921b394bf10c8d08c5999edfccc8d" 
    session_cookies = ({"_ga_YS1V643LGV":"GS2.1.s1762027741$o1$g0$t1762027742$j59$l0$h0","_ga":"GA1.2.441592679.1762027741","_ga_RYD7END4JE":"GS2.2.s1762027741$o1$g1$t1762027742$j59$l0$h0","_zlang":"vn","__zi":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8yscUwdaqPRY7kGwQBTHrw9VfJkfZ4m.1","__zi-legacy":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8yscUwdaqPRY7kGwQBTHrw9VfJkfZ4m.1","_ga_3EM8ZPYYN3":"GS2.2.s1762358900$o4$g0$t1762358900$j60$l0$h0","ozi":"2000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjMXe9fFM8ysaUIZaaDMYpQThwQLJ1YACvogef987eu.1","app.event.zalo.me":"1697436733231772679","_gid":"GA1.2.675430665.1762358878","_gat":"1","zpsid":"iS7r.380341803.12.BAeC42onSVi7Fzhj8B5n-rd20yWKWKBF7Ob1o2s6rWxYM_vxBSi7y4MnSVi","zpw_sek":"PL4Q.380341803.a0.2txMtwifzd-0frrfYYdsVz0BanI94zGtvHk35T4QeJdS78uKqbgrAyfucJNg5CjTrYZ1s5xd7F0hA8m9e43sVm"})
    if imei == "YOUR_IMEI_HERE":
        print("VUI LÒNG MỞ FILE HHHH.PY VÀ CHỈNH SỬA imei, session_cookies ở cuối file")
    else:
        honhattruong = Honhattruong('api_key', 'secret_key', imei=imei, session_cookies=session_cookies)
        honhattruong.listen()