import cv2
import pygame
import sys
import numpy as np

from hand_tracking import HandTracker
from gesture_recognition import GestureRecognizer
from spell_system import SpellSystem
from enemy_system import EnemySystem
from ui_system import UISystem
from sound_system import SoundSystem

# --- 設定常數 ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60
MAX_LEVEL = 2  # 最大關卡數

# --- 遊戲主流程 ---
def main():
    # 初始化 Pygame
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Hand Magic Battle")
    clock = pygame.time.Clock()

    # 初始化攝影機 (OpenCV)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WINDOW_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WINDOW_HEIGHT)
    
    if not cap.isOpened():
        print("無法開啟攝影機，請檢查硬體連線。")
        pygame.quit()
        sys.exit()

    # 讀取一幀來確認攝影機實際解析度
    ret, frame = cap.read()
    if not ret:
        print("無法讀取畫格")
        pygame.quit()
        sys.exit()
    cam_h, cam_w, _ = frame.shape

    # 實例化各模組
    hand_tracker = HandTracker()
    gesture_recognizer = GestureRecognizer()
    spell_system = SpellSystem()
    enemy_system = EnemySystem(WINDOW_WIDTH, WINDOW_HEIGHT)
    ui_system = UISystem(WINDOW_WIDTH, WINDOW_HEIGHT)
    sound_system = SoundSystem()

    # ========== 遊戲狀態與數值 ==========
    # 狀態: 'START', 'PLAYING', 'LEVEL_CLEAR', 'VICTORY', 'GAMEOVER'
    game_state = 'START'
    player_hp = 100
    score = 0
    current_level = 1           # 目前關卡 (1 或 2)
    start_progress = 0.0        # OK 手勢確認進度 (0.0 ~ 1.0)
    level_clear_timer = 0       # 過場動畫倒數計時器 (幀)
    LEVEL_CLEAR_DURATION = 180  # 過場動畫持續 3 秒 (180 幀 @60FPS)
    dt = 1.0                    # Delta Time 乘數

    running = True
    while running:
        # 1. 處理事件 (Pygame)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                if game_state == 'START' and event.key == pygame.K_SPACE:
                    game_state = 'PLAYING'
                elif game_state == 'GAMEOVER' and event.key == pygame.K_r:
                    # 重置遊戲回到第一關
                    game_state = 'PLAYING'
                    player_hp = 100
                    score = 0
                    current_level = 1
                    enemy_system.set_level(1)
                    spell_system.spells.clear()
                    start_progress = 0.0
                elif game_state == 'VICTORY' and event.key == pygame.K_r:
                    # 勝利後重新開始
                    game_state = 'PLAYING'
                    player_hp = 100
                    score = 0
                    current_level = 1
                    enemy_system.set_level(1)
                    spell_system.spells.clear()
                    start_progress = 0.0

        # 2. 擷取攝影機畫面 (OpenCV)
        ret, frame = cap.read()
        if not ret:
            break
        
        # 鏡像翻轉
        frame = cv2.flip(frame, 1)

        current_gesture = None
        
        # 3. 根據狀態處理手勢與遊戲邏輯
        if game_state == 'PLAYING':
            results = hand_tracker.process_frame(frame)
            frame = hand_tracker.draw_landmarks(frame, results)
            
            raw_landmarks = hand_tracker.get_landmark_positions(frame, results)
            landmark_list = []
            for lm in raw_landmarks:
                px = int(lm[1] * (WINDOW_WIDTH / cam_w))
                py = int(lm[2] * (WINDOW_HEIGHT / cam_h))
                landmark_list.append([lm[0], px, py])
            
            # 手勢辨識
            current_gesture = gesture_recognizer.recognize(landmark_list)

            # 根據手勢放魔法
            if current_gesture:
                cast_x = landmark_list[9][1]
                cast_y = landmark_list[9][2]
                
                if current_gesture == 'Fist':
                    if spell_system.cooldowns['Shield'] == 0:
                        sound_system.play_attack('Shield')
                    spell_system.cast_spell('Shield', cast_x, cast_y)
                elif current_gesture == 'Palm':
                    if spell_system.cooldowns['Fireball'] == 0:
                        sound_system.play_attack('Fireball')
                    spell_system.cast_spell('Fireball', cast_x, cast_y)
                elif current_gesture == 'Peace':
                    if spell_system.cooldowns['Lightning'] == 0:
                        sound_system.play_attack('Lightning')
                    spell_system.cast_spell('Lightning', cast_x, cast_y)
                elif current_gesture == 'Index':
                    if spell_system.cooldowns['Magic Beam'] == 0:
                        sound_system.play_attack('Magic Beam')
                    spell_system.cast_spell('Magic Beam', cast_x, cast_y)

            # 更新邏輯 (傳入 dt)
            spell_system.update(dt)
            enemy_system.update(dt)

            # 4. 碰撞判定與物理邏輯
            # --- 玩家法術 vs 敵人子彈 ---
            for spell in spell_system.spells[:]:
                for enemy in enemy_system.enemies:
                    for proj in enemy.projectiles[:]:
                        if spell.get('radius'):
                            dist = np.hypot(spell['x'] - proj['x'], spell['y'] - proj['y'])
                            if dist < (spell['radius'] + proj['radius']):
                                if proj in enemy.projectiles:
                                    enemy.projectiles.remove(proj)
                                if spell in spell_system.spells:
                                    spell_system.spells.remove(spell)
                                break
                        elif spell['type'] in ['Lightning', 'Magic Beam']:
                            beam_half_width = 15
                            if (proj['x'] > spell['x'] and
                                abs(proj['y'] - spell['y']) < (beam_half_width + proj['radius'])):
                                if proj in enemy.projectiles:
                                    enemy.projectiles.remove(proj)

            # --- 法術打中敵人 ---
            for spell in spell_system.spells[:]:
                if spell.get('radius'):
                    # check_hit 回傳被命中的敵人物件（或 None）
                    hit_enemy = enemy_system.check_hit(spell['x'], spell['y'], spell['radius'])
                    if hit_enemy:
                        was_alive = not hit_enemy.is_dead
                        hit_enemy.take_damage(spell['damage'])
                        # 播放音效：擊中 or 擊殺
                        if hit_enemy.is_dead and was_alive:
                            sound_system.play('enemy_death')
                        else:
                            sound_system.play('enemy_hit')
                        if spell in spell_system.spells:
                            spell_system.spells.remove(spell)
                elif spell['type'] in ['Lightning', 'Magic Beam']:
                    spell['end_x'] = 1280
                    hit, edge_x = enemy_system.check_beam_hit(spell['x'], spell['y'])
                    if hit:
                        # 射線傷害：對所有被射線穿過的敵人造成傷害
                        for enemy in enemy_system.enemies:
                            if not enemy.is_dead:
                                e_hit, _ = enemy.check_beam_hit(spell['x'], spell['y'])
                                if e_hit:
                                    enemy.take_damage(spell['damage'] / 10)
                        spell['end_x'] = edge_x

            # ========== 通關判定 ==========
            if enemy_system.is_dead:
                score += 200  # 通關獎勵分數
                spell_system.spells.clear()
                if current_level < MAX_LEVEL:
                    # 還有下一關 → 進入過場動畫
                    game_state = 'LEVEL_CLEAR'
                    level_clear_timer = LEVEL_CLEAR_DURATION
                    sound_system.play('level_clear')
                else:
                    # 最後一關通關 → 進入勝利畫面
                    game_state = 'VICTORY'
                    sound_system.play('victory')

            # --- 敵人子彈打中玩家 ---
            for enemy in enemy_system.enemies:
                for p in enemy.projectiles[:]:
                    player_dist = np.hypot(p['x'] - 300, p['y'] - 360)
                    if spell_system.shield_active_time > 0 and player_dist < 200 + p['radius']:
                        enemy.projectiles.remove(p)
                        continue
                    if player_dist < 100 + p['radius']:
                        player_hp -= p['damage']
                        enemy.projectiles.remove(p)
                        sound_system.play('player_hit')
                        if player_hp <= 0:
                            game_state = 'GAMEOVER'

        # ========== 過場動畫狀態 ==========
        elif game_state == 'LEVEL_CLEAR':
            level_clear_timer -= dt
            if level_clear_timer <= 0:
                # 過場結束，進入下一關
                current_level += 1
                enemy_system.set_level(current_level)
                spell_system.spells.clear()
                game_state = 'PLAYING'

        elif game_state in ['START', 'GAMEOVER', 'VICTORY']:
            # --- 使用 OK 手勢開始/重新開始遊戲（只需要單手） ---
            results = hand_tracker.process_frame(frame)
            frame = hand_tracker.draw_landmarks(frame, results)

            # 取得單手的 21 個關節點座標
            raw_landmarks = hand_tracker.get_landmark_positions(frame, results)
            landmark_list = []
            for lm in raw_landmarks:
                px = int(lm[1] * (WINDOW_WIDTH / cam_w))
                py = int(lm[2] * (WINDOW_HEIGHT / cam_h))
                landmark_list.append([lm[0], px, py])

            # 計算 OK 手勢的確認進度 (0.0 ~ 1.0)
            start_progress = min(
                gesture_recognizer.ok_count / gesture_recognizer.ok_threshold, 1.0
            )

            # 偵測到 OK 手勢後開始/重新開始遊戲
            if gesture_recognizer.recognize_ok(landmark_list):
                game_state = 'PLAYING'
                player_hp = 100
                score = 0
                current_level = 1
                enemy_system.set_level(1)
                spell_system.spells.clear()
                start_progress = 0.0

        # 5. 渲染畫面
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (WINDOW_WIDTH, WINDOW_HEIGHT))
        surface_image = pygame.image.frombuffer(frame_resized.tobytes(), frame_resized.shape[1::-1], "RGB")

        screen.blit(surface_image, (0, 0))

        # 6. 繪製各階層 UI
        if game_state == 'PLAYING':
            enemy_system.draw(screen)
            spell_system.draw(screen)
            ui_system.draw_hud(screen, player_hp, score, current_gesture,
                               spell_system.cooldowns, current_level)
        elif game_state == 'START':
            ui_system.draw_start_screen(screen, start_progress)
        elif game_state == 'LEVEL_CLEAR':
            ui_system.draw_level_clear(screen, current_level, score, level_clear_timer,
                                       LEVEL_CLEAR_DURATION)
        elif game_state == 'VICTORY':
            ui_system.draw_victory(screen, score, start_progress)
        elif game_state == 'GAMEOVER':
            ui_system.draw_game_over(screen, score, start_progress)

        # 7. 更新螢幕與計算 dt
        pygame.display.flip()
        milli = clock.tick(FPS)
        dt = milli / (1000.0 / FPS) # 以 60 FPS 為基準 1.0

    cap.release()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
