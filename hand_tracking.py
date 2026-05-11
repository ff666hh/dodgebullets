"""
hand_tracking.py — 手部追蹤模組
使用 MediaPipe Tasks API (新版) 的 HandLandmarker 進行手部偵測與追蹤。
需要 hand_landmarker.task 模型檔案放在同目錄下。
"""

import os
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandTracker:
    """
    使用 MediaPipe Tasks API (HandLandmarker) 追蹤手部關節點。
    提供三個主要方法：
        - process_frame(): 傳入 OpenCV 影像幀，回傳偵測結果
        - draw_landmarks(): 在影像上繪製手部骨架
        - get_landmark_positions(): 取得 21 個關節點的像素座標
    """

    # 21 個手部關節點之間的連線定義（用於繪圖）
    # 每組 (起點, 終點) 對應 MediaPipe Hand Landmark 的編號
    HAND_CONNECTIONS = [
        # 拇指 (Thumb)
        (0, 1), (1, 2), (2, 3), (3, 4),
        # 食指 (Index Finger)
        (0, 5), (5, 6), (6, 7), (7, 8),
        # 中指 (Middle Finger)
        (5, 9), (9, 10), (10, 11), (11, 12),
        # 無名指 (Ring Finger)
        (9, 13), (13, 14), (14, 15), (15, 16),
        # 小指 (Pinky)
        (13, 17), (17, 18), (18, 19), (19, 20),
        # 手掌底部連線 (Palm base)
        (0, 17),
    ]

    def __init__(self, max_num_hands=1,
                 min_detection_confidence=0.7,
                 min_tracking_confidence=0.7):
        """
        初始化 HandLandmarker（新版 Tasks API）

        參數:
            max_num_hands: 最多偵測幾隻手（預設 1，只偵測單手以提升效能）
            min_detection_confidence: 手部偵測的最低信心值（0~1）
            min_tracking_confidence: 手部存在的最低信心值（0~1）
        """
        # 取得模型檔案路徑（與此腳本放在同一目錄）
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, "hand_landmarker.task")

        # 檢查模型檔是否存在
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"找不到模型檔案: {model_path}\n"
                "請下載 hand_landmarker.task 並放在專案目錄下。"
            )

        # 建立 HandLandmarker 設定（使用 VIDEO 執行模式）
        # 因路徑中可能包含中文，使用 python 預先讀取檔案至記憶體可避免底層 C++ 讀取路徑時發生錯誤
        with open(model_path, "rb") as f:
            model_data = f.read()
        base_options = python.BaseOptions(model_asset_buffer=model_data)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_tracking_confidence,
            running_mode=vision.RunningMode.VIDEO,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)

        # VIDEO 模式需要傳入單調遞增的時間戳記
        # 這裡使用程式啟動後的實際經過時間（毫秒）
        self._start_time = time.time()

    def process_frame(self, frame):
        """
        處理一幀 OpenCV 影像，回傳手部偵測結果 (HandLandmarkerResult)

        參數:
            frame: OpenCV BGR 格式的影像（numpy array）
        回傳:
            HandLandmarkerResult 物件，包含:
                .hand_landmarks — 正規化座標 (0~1)
                .handedness     — 左手/右手判定
        """
        # OpenCV 預設使用 BGR，MediaPipe 需要 RGB 格式
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 將 numpy array 包裝成 MediaPipe Image 物件
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        # 計算當前時間戳（毫秒），必須單調遞增
        timestamp_ms = int((time.time() - self._start_time) * 1000)

        # 使用 detect_for_video 進行偵測（VIDEO 模式專用方法）
        try:
            results = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        except Exception as e:
            print(f"[HandTracker] 偵測時發生錯誤: {e}")
            # 回傳空結果，避免程式崩潰
            return _EmptyResult()

        return results

    def draw_landmarks(self, frame, results):
        """
        在 OpenCV 影像上繪製手部骨架（關節點 + 連線）

        參數:
            frame: OpenCV BGR 影像
            results: process_frame() 回傳的結果
        回傳:
            繪製完成的影像
        """
        if results.hand_landmarks:
            h, w, _ = frame.shape

            for hand_landmarks in results.hand_landmarks:
                # 繪製骨架連線（綠色線條）
                for start_idx, end_idx in self.HAND_CONNECTIONS:
                    x1 = int(hand_landmarks[start_idx].x * w)
                    y1 = int(hand_landmarks[start_idx].y * h)
                    x2 = int(hand_landmarks[end_idx].x * w)
                    y2 = int(hand_landmarks[end_idx].y * h)
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # 繪製每個關節點（紅色圓點）
                for lm in hand_landmarks:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), cv2.FILLED)

        return frame

    def get_landmark_positions(self, frame, results):
        """
        取得第一隻手的 21 個關節點像素座標

        參數:
            frame: OpenCV 影像（用來取得寬高以換算像素座標）
            results: process_frame() 回傳的結果
        回傳:
            list — 格式為 [[id, x, y], [id, x, y], ...] 共 21 個點
                   如果沒有偵測到手則回傳空 list
        """
        landmark_list = []

        if results.hand_landmarks:
            # 取第一隻手的關節點
            hand_landmarks = results.hand_landmarks[0]
            h, w, _ = frame.shape

            for idx, lm in enumerate(hand_landmarks):
                # 將正規化座標 (0~1) 轉換為像素座標
                cx = int(lm.x * w)
                cy = int(lm.y * h)
                landmark_list.append([idx, cx, cy])

        return landmark_list

    def get_two_hands_landmarks(self, frame, results):
        """
        取得兩隻手各自的 21 個關節點像素座標（用於雙手合十等雙手手勢判定）

        參數:
            frame: OpenCV 影像（用來取得寬高以換算像素座標）
            results: process_frame() 回傳的結果
        回傳:
            list of list — 每隻手一個子 list，格式為 [[id, x, y], ...]
                           如果偵測到的手不足兩隻，回傳空 list
        """
        # 必須偵測到至少兩隻手才回傳
        if not results.hand_landmarks or len(results.hand_landmarks) < 2:
            return []

        h, w, _ = frame.shape
        both_hands = []

        # 分別取出前兩隻手的關節座標
        for hand_idx in range(2):
            hand_landmarks = results.hand_landmarks[hand_idx]
            single_hand = []
            for idx, lm in enumerate(hand_landmarks):
                cx = int(lm.x * w)
                cy = int(lm.y * h)
                single_hand.append([idx, cx, cy])
            both_hands.append(single_hand)

        return both_hands


class _EmptyResult:
    """
    當偵測發生錯誤時，回傳的空結果物件。
    模擬 HandLandmarkerResult 的介面，避免後續程式碼出錯。
    """
    def __init__(self):
        self.hand_landmarks = []
        self.hand_world_landmarks = []
        self.handedness = []
