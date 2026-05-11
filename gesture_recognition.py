import numpy as np


class GestureRecognizer:
    def __init__(self):
        # MediaPipe 指尖的 ID
        self.tip_ids = [4, 8, 12, 16, 20]
        self.current_gesture = None
        self.gesture_history = []
        self.history_length = 5  # 用於平滑化 (Smoothing)

        # --- OK 手勢偵測用的穩定計數器 ---
        # 避免短暫的誤判就觸發開始遊戲，需要連續偵測到多幀才算成立
        self.ok_count = 0
        self.ok_threshold = 15  # 連續 15 幀 (~0.25 秒) 才算確認 OK 手勢

    def recognize(self, landmark_list):
        """
        根據手部特徵點判斷手勢
        回傳: 'Fist', 'Palm', 'Peace', 'Index', 或 None
        """
        if len(landmark_list) == 0:
            return None

        fingers_up = []

        # 拇指：比較 x 座標 (適用於右手，若要適用雙手可用更嚴謹的角度計算)
        # 這裡用簡單的 x 座標比較，若指尖在關節外側則視為伸出
        if landmark_list[self.tip_ids[0]][1] > landmark_list[self.tip_ids[0] - 1][1]:
            fingers_up.append(1)
        else:
            fingers_up.append(0)

        # 其他四指：比較 y 座標，指尖 y 小於下一個關節 y (以畫面來說上方 y 比較小)
        for id in range(1, 5):
            if landmark_list[self.tip_ids[id]][2] < landmark_list[self.tip_ids[id] - 2][2]:
                fingers_up.append(1)
            else:
                fingers_up.append(0)

        total_fingers = fingers_up.count(1)
        
        # 判定邏輯
        detected = None
        if total_fingers == 0:
            detected = 'Fist' # 石頭 => 護盾
        elif total_fingers == 5:
            detected = 'Palm' # 布 => 火球
        elif fingers_up == [0, 1, 1, 0, 0]:
            detected = 'Peace' # YA => 閃電
        elif fingers_up == [0, 1, 0, 0, 0]:
            detected = 'Index' # 食指 => 發射光束

        # 防連發與平滑化機制
        self.gesture_history.append(detected)
        if len(self.gesture_history) > self.history_length:
            self.gesture_history.pop(0)

        # 找出歷史中最常出現的手勢，避免偵測閃爍
        if self.gesture_history.count(detected) > (self.history_length // 2):
            self.current_gesture = detected
        else:
            self.current_gesture = None

        return self.current_gesture

    def recognize_ok(self, landmark_list):
        """
        判定「OK 手勢 (👌)」—— 拇指指尖與食指指尖靠近形成圓圈，其餘三指伸直

        判定原理：
            1. 計算拇指指尖(4)與食指指尖(8)的距離 → 靠近代表形成「O」
            2. 檢查中指(12)、無名指(16)、小指(20) 是否伸直
            3. 使用連續幀計數器避免誤觸

        參數:
            landmark_list: 單手的 21 個關節座標
                          格式為 [[id, x, y], [id, x, y], ...]
                          如果為空 list 代表沒有偵測到手
        回傳:
            bool — True 表示確認 OK 手勢，False 表示尚未確認
        """
        # 如果沒有偵測到手，重置計數器
        if len(landmark_list) < 21:
            self.ok_count = 0
            return False

        # --- 步驟 1：檢查拇指指尖(4)與食指指尖(8)的距離 ---
        # 兩者靠近表示形成「O」的圓圈
        thumb_tip = landmark_list[4]   # 拇指指尖 [id, x, y]
        index_tip = landmark_list[8]   # 食指指尖 [id, x, y]

        # 計算兩個指尖之間的歐幾里得距離（像素）
        tip_dist = np.hypot(
            thumb_tip[1] - index_tip[1],  # x 距離
            thumb_tip[2] - index_tip[2]   # y 距離
        )

        # 拇指與食指靠近的閾值（像素），太遠就不算 OK
        OK_TIP_THRESHOLD = 60

        if tip_dist > OK_TIP_THRESHOLD:
            self.ok_count = 0
            return False

        # --- 步驟 2：檢查中指、無名指、小指是否伸直 ---
        # 伸直的判定：指尖的 y 座標小於（畫面上方）其對應的 PIP 關節 y 座標
        straight_count = 0
        # 中指(12 vs 10)、無名指(16 vs 14)、小指(20 vs 18)
        for tip_id, pip_id in [(12, 10), (16, 14), (20, 18)]:
            if landmark_list[tip_id][2] < landmark_list[pip_id][2]:
                straight_count += 1

        # 至少 2 根手指伸直才算 OK 手勢（容許一根偵測誤差）
        if straight_count >= 2:
            self.ok_count += 1
        else:
            self.ok_count = 0

        # --- 步驟 3：連續幀計數達到閾值才確認 ---
        if self.ok_count >= self.ok_threshold:
            self.ok_count = 0  # 確認後重置，避免連續觸發
            return True

        return False

