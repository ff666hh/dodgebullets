import pygame
import math
import time


class UISystem:
    def __init__(self, screen_width=1280, screen_height=720):
        pygame.font.init()
        # 載入自定義中文字體
        font_path = 'WCL-06.ttf'
        try:
            self.font_large = pygame.font.Font(font_path, 80)
            self.font_medium = pygame.font.Font(font_path, 40)
            self.font_small = pygame.font.Font(font_path, 28)
            print(f"成功載入中文字體: {font_path}")
        except:
            print(f"找不到字體檔 {font_path}，使用系統預設字體")
            self.font_large = pygame.font.SysFont('Arial', 64, bold=True)
            self.font_medium = pygame.font.SysFont('Arial', 36, bold=True)
            self.font_small = pygame.font.SysFont('Arial', 24)
            
        self.w = screen_width
        self.h = screen_height

    # --- 關卡名稱對照表 ---
    LEVEL_NAMES = {
        1: "冰雪之境",
        2: "馬戲團之夜",
    }

    def draw_hud(self, surface, player_hp, score, current_gesture, cooldowns,
                 current_level=1):
        """HUD: 玩家血量, 分數, 當前手勢, 關卡資訊"""
        
        # 繪製玩家血量條 (左上角)
        bar_width = 300
        hp_ratio = max(0, player_hp / 100)
        pygame.draw.rect(surface, (100, 100, 100), (40, 40, bar_width, 30))
        pygame.draw.rect(surface, (0, 255, 0), (40, 40, int(bar_width * hp_ratio), 30))
        hp_text = self.font_medium.render(f"生命值: {player_hp}/100", True, (255, 255, 255))
        surface.blit(hp_text, (40 + bar_width + 10, 35))

        # 分數 (右上角)
        score_text = self.font_medium.render(f"得分: {score}", True, (255, 215, 0)) # 金色
        surface.blit(score_text, (self.w - 250, 35))

        # 關卡資訊 (右上角第二行)
        level_name = self.LEVEL_NAMES.get(current_level, f"第 {current_level} 關")
        level_text = self.font_small.render(
            f"第 {current_level} 關 — {level_name}", True, (200, 220, 255)
        )
        surface.blit(level_text, (self.w - 300, 80))

        # 當前手勢狀態 (左側中間)
        gesture_map = {
            'Fist': '拳頭 (護盾)',
            'Palm': '手掌 (火球)',
            'Peace': '勝利 (閃電)',
            'Index': '食指 (光束)',
            None: '無'
        }
        display_gesture = gesture_map.get(current_gesture, '未知')
        gesture_text = self.font_medium.render(f"目前手勢: {display_gesture}", True, (0, 255, 255))
        surface.blit(gesture_text, (40, 100))

        # 冷卻時間圖示 (左下角)
        y_offset = self.h - 180
        spell_map = {
            'Fireball': '火球術',
            'Shield': '守護盾',
            'Lightning': '連鎖閃電',
            'Magic Beam': '奧術光束'
        }
        for idx, (spell, cd) in enumerate(cooldowns.items()):
            color = (150, 150, 150) if cd > 0 else (255, 255, 255)
            spell_name = spell_map.get(spell, spell)
            status = '就緒' if cd == 0 else f'{cd}s'
            text = self.font_small.render(f"{spell_name}: {status}", True, color)
            surface.blit(text, (40, y_offset + idx * 35))

    def draw_start_screen(self, surface, prayer_progress=0.0):
        """開始遊戲畫面"""
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # 半透明黑色背景
        surface.blit(overlay, (0, 0))

        title = self.font_large.render("手勢魔法大戰", True, (255, 200, 0))
        prompt = self.font_medium.render("按下 空白鍵 開始遊戲", True, (255, 255, 255))
        prompt_prayer = self.font_medium.render("或是 OK 手勢 (👌) 開始", True, (255, 200, 100))
        
        hint1 = self.font_small.render("拳頭 (✊) -> 守護盾", True, (100, 200, 255))
        hint2 = self.font_small.render("手掌 (✋) -> 火球術", True, (255, 100, 100))
        hint3 = self.font_small.render("勝利 (✌) -> 連鎖閃電", True, (255, 255, 100))
        hint4 = self.font_small.render("食指 (👉) -> 奧術光束", True, (0, 255, 255))

        surface.blit(title, (self.w//2 - title.get_width()//2, 100))
        surface.blit(hint1, (self.w//2 - hint1.get_width()//2, 230))
        surface.blit(hint2, (self.w//2 - hint2.get_width()//2, 275))
        surface.blit(hint3, (self.w//2 - hint3.get_width()//2, 320))
        surface.blit(hint4, (self.w//2 - hint4.get_width()//2, 365))

        # 創造跳動效果
        if int(time.time() * 2) % 2 == 0:
            surface.blit(prompt, (self.w//2 - prompt.get_width()//2, 480))
            surface.blit(prompt_prayer, (self.w//2 - prompt_prayer.get_width()//2, 540))

        # 繪製合十進度條
        if prayer_progress > 0:
            self._draw_start_ring(surface, prayer_progress, 620)

    def draw_level_clear(self, surface, level, score, timer, duration):
        """
        過場動畫：顯示「第 X 關 通關！」並倒數進入下一關

        參數:
            surface: Pygame 繪圖表面
            level: 剛通過的關卡編號
            score: 目前分數
            timer: 剩餘倒數幀數
            duration: 總倒數幀數
        """
        # 半透明深藍色背景
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 20, 60, 200))
        surface.blit(overlay, (0, 0))

        # 關卡名稱
        level_name = self.LEVEL_NAMES.get(level, f"第 {level} 關")

        # 「通關！」標題（帶金色光芒效果）
        title = self.font_large.render(f"第 {level} 關 通關！", True, (255, 215, 0))
        surface.blit(title, (self.w // 2 - title.get_width() // 2, 150))

        # 關卡名稱
        name_text = self.font_medium.render(f"— {level_name} —", True, (200, 220, 255))
        surface.blit(name_text, (self.w // 2 - name_text.get_width() // 2, 250))

        # 分數
        score_text = self.font_medium.render(f"目前得分: {score}", True, (255, 255, 255))
        surface.blit(score_text, (self.w // 2 - score_text.get_width() // 2, 320))

        # 下一關預告
        next_level = level + 1
        next_name = self.LEVEL_NAMES.get(next_level, f"第 {next_level} 關")
        next_text = self.font_medium.render(
            f"即將進入 第 {next_level} 關: {next_name}", True, (255, 180, 100)
        )
        surface.blit(next_text, (self.w // 2 - next_text.get_width() // 2, 420))

        # 倒數進度條
        progress = max(0, 1.0 - timer / duration)
        bar_width = 400
        bar_x = self.w // 2 - bar_width // 2
        bar_y = 500
        pygame.draw.rect(surface, (80, 80, 80), (bar_x, bar_y, bar_width, 20),
                         border_radius=10)
        fill_w = int(bar_width * progress)
        if fill_w > 0:
            pygame.draw.rect(surface, (100, 200, 255), (bar_x, bar_y, fill_w, 20),
                             border_radius=10)

        # 倒數秒數
        seconds_left = max(0, int(timer / 60))
        countdown = self.font_small.render(f"{seconds_left} 秒後進入下一關...", True,
                                           (180, 200, 255))
        surface.blit(countdown, (self.w // 2 - countdown.get_width() // 2, 540))

    def draw_victory(self, surface, score, prayer_progress=0.0):
        """
        勝利畫面：全部關卡通關後顯示

        參數:
            surface: Pygame 繪圖表面
            score: 最終分數
            prayer_progress: OK 手勢進度 (0.0 ~ 1.0)
        """
        # 半透明金色背景
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((30, 20, 0, 200))
        surface.blit(overlay, (0, 0))

        # 標題
        title = self.font_large.render("恭喜通關！", True, (255, 215, 0))
        surface.blit(title, (self.w // 2 - title.get_width() // 2, 120))

        # 星星裝飾（用文字模擬）
        star = self.font_large.render("★ ★ ★", True, (255, 200, 50))
        surface.blit(star, (self.w // 2 - star.get_width() // 2, 220))

        # 最終分數
        score_text = self.font_medium.render(f"最終得分: {score}", True, (255, 255, 255))
        surface.blit(score_text, (self.w // 2 - score_text.get_width() // 2, 330))

        # 重新開始提示
        prompt_r = self.font_medium.render("按下 'R' 鍵重新挑戰", True, (200, 200, 200))
        prompt_ok = self.font_medium.render("或是 OK 手勢 (👌) 重新開始", True, (255, 200, 100))

        if int(time.time() * 2) % 2 == 0:
            surface.blit(prompt_r, (self.w // 2 - prompt_r.get_width() // 2, 430))
            surface.blit(prompt_ok, (self.w // 2 - prompt_ok.get_width() // 2, 490))

        # OK 手勢進度環
        if prayer_progress > 0.01:
            self._draw_start_ring(surface, prayer_progress, 580)

    def _draw_start_ring(self, surface, prayer_progress, center_y):
        """繪製環形進度條的私有工具方法（用於 OK 手勢確認進度）"""
        center_x = self.w // 2
        radius = 40
        thickness = 8

        # 底圈（灰色）
        pygame.draw.circle(surface, (80, 80, 80), (center_x, center_y), radius, thickness)

        # 進度弧線
        num_segments = max(2, int(prayer_progress * 60))
        start_angle = -math.pi / 2
        end_angle = start_angle + (2 * math.pi * prayer_progress)

        # 顏色漸變
        r = 255
        g = int(150 + 105 * prayer_progress)
        b = int(50 * (1 - prayer_progress))
        arc_color = (r, g, b)

        points = []
        for i in range(num_segments + 1):
            angle = start_angle + (end_angle - start_angle) * (i / num_segments)
            px = center_x + int(radius * math.cos(angle))
            py = center_y + int(radius * math.sin(angle))
            points.append((px, py))

        if len(points) >= 2:
            pygame.draw.lines(surface, arc_color, False, points, thickness)

        # 百分比文字
        pct_text = self.font_small.render(f"{int(prayer_progress * 100)}%", True, arc_color)
        surface.blit(pct_text, (center_x - pct_text.get_width()//2, center_y + radius + 10))

    def draw_game_over(self, surface, score, prayer_progress=0.0):
        """
        結束遊戲畫面
        
        參數:
            surface: Pygame 繪圖表面
            score: 最終分數
            prayer_progress: 雙手合十進度 (0.0 ~ 1.0)，用於繪製環形進度條
        """
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((100, 0, 0, 180)) # 半透明紅色背景
        surface.blit(overlay, (0, 0))

        title = self.font_large.render("遊戲結束", True, (255, 50, 50))
        score_t = self.font_medium.render(f"最終得分: {score}", True, (255, 255, 255))
        prompt_r = self.font_medium.render("按下 'R' 鍵重新開始", True, (200, 200, 200))
        prompt_prayer = self.font_medium.render("或是 OK 手勢 (👌) 重新開始", True, (255, 200, 100))

        surface.blit(title, (self.w//2 - title.get_width()//2, 180))
        surface.blit(score_t, (self.w//2 - score_t.get_width()//2, 280))
        surface.blit(prompt_r, (self.w//2 - prompt_r.get_width()//2, 370))
        surface.blit(prompt_prayer, (self.w//2 - prompt_prayer.get_width()//2, 430))

        # --- 環形進度條：顯示雙手合十的偵測進度 ---
        if prayer_progress > 0.01:
            self._draw_start_ring(surface, prayer_progress, 540)
