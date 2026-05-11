"""
enemy_system.py — 敵人系統模組
包含雪人 (SnowmanEnemy) 與小幽靈 (GhostEnemy) 兩種敵人，
以及管理所有敵人的 EnemySystem 類別。
"""

import pygame
import random
import math
import numpy as np


# ==============================================================
#  基底敵人類別 (BaseEnemy)
#  定義所有敵人共用的介面與基本屬性
# ==============================================================
class BaseEnemy:
    """所有敵人的基底類別，子類別需實作 draw() 和 get_hitboxes()"""

    def __init__(self, screen_w, screen_h, hp, x, y, radius):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.hp = hp
        self.max_hp = hp
        self.x = x
        self.y = y
        self.radius = radius
        self.is_dead = False

        # 移動設定
        self.speed_y = 2
        self.direction = 1
        self.move_top = 150
        self.move_bottom = screen_h - 150

        # 攻擊
        self.projectiles = []
        self.attack_timer = 0
        self.attack_interval = 120

        # 受傷閃爍
        self.flash_timer = 0

    def update(self, dt=1.0):
        """基本更新邏輯（移動 + 攻擊計時 + 子彈更新）"""
        if self.is_dead:
            return

        # 上下巡邏
        self.y += self.speed_y * self.direction * dt
        if self.y >= self.move_bottom:
            self.y = self.move_bottom
            self.direction = -1
        elif self.y <= self.move_top:
            self.y = self.move_top
            self.direction = 1

        # 攻擊計時
        self.attack_timer += dt
        if self.attack_timer >= self.attack_interval:
            self.attack_timer = random.uniform(0, 30)
            self.shoot_projectile()

        # 受傷閃爍
        if self.flash_timer > 0:
            self.flash_timer -= dt

        # 更新子彈
        for p in self.projectiles[:]:
            p['x'] -= p['vx'] * dt
            if p['x'] < 0:
                self.projectiles.remove(p)

    def shoot_projectile(self):
        """發射子彈（子類別可覆寫以自訂子彈樣式）"""
        self.projectiles.append({
            'x': self.x,
            'y': self.y + random.randint(-30, 30),
            'vx': 8,
            'radius': 15,
            'damage': 10
        })

    def take_damage(self, damage):
        """受到傷害"""
        self.hp -= damage
        self.flash_timer = 10
        if self.hp <= 0:
            self.is_dead = True

    def reset(self):
        """重置敵人狀態"""
        self.hp = self.max_hp
        self.is_dead = False
        self.projectiles = []
        self.y = random.randint(200, self.screen_h - 200)
        self.direction = random.choice([-1, 1])

    def get_hitboxes(self):
        """取得碰撞區域，子類別必須覆寫"""
        return [(self.x, self.y, self.radius)]

    def check_hit(self, px, py, p_radius=0):
        """檢查座標是否碰撞到敵人"""
        for (cx, cy, r) in self.get_hitboxes():
            dist = math.hypot(px - cx, py - cy)
            if dist < (r + p_radius):
                return True
        return False

    def check_beam_hit(self, beam_x, beam_y, beam_width=30):
        """檢查射線武器是否命中"""
        closest_edge_x = None
        hit = False
        for (cx, cy, r) in self.get_hitboxes():
            if beam_x < cx and abs(beam_y - cy) < (r + beam_width):
                hit = True
                edge_x = cx - r
                if closest_edge_x is None or edge_x < closest_edge_x:
                    closest_edge_x = edge_x
        return hit, closest_edge_x

    def draw(self, surface):
        """繪製敵人（子類別必須覆寫）"""
        pass

    def draw_projectiles(self, surface):
        """繪製子彈（子類別可覆寫）"""
        pass


# ==============================================================
#  雪人敵人 (SnowmanEnemy) — 原有的雪人
# ==============================================================
class SnowmanEnemy(BaseEnemy):
    """雪人敵人：由三個雪球疊起來，戴帽子，有樹枝手臂"""

    def __init__(self, screen_w, screen_h):
        # 雪人出現在畫面右側
        super().__init__(screen_w, screen_h,
                         hp=100,
                         x=screen_w - 200,
                         y=screen_h // 2,
                         radius=50)
        # 冰雪拖尾粒子
        self.ice_particles = []

    def reset(self):
        super().reset()
        self.ice_particles = []

    def update(self, dt=1.0):
        super().update(dt)
        if self.is_dead:
            return

        # 為子彈產生冰雪拖尾粒子
        for p in self.projectiles:
            for _ in range(random.randint(2, 4)):
                self.ice_particles.append({
                    'x': p['x'] + p['radius'] + random.randint(-3, 3),
                    'y': p['y'] + random.randint(-8, 8),
                    'vx': random.uniform(0.5, 2.0),
                    'vy': random.uniform(-1.0, 1.0),
                    'radius': random.randint(2, 5),
                    'life': random.randint(8, 14),
                    'max_life': 14,
                    'color': random.choice([
                        (200, 230, 255), (180, 210, 255),
                        (230, 245, 255), (150, 200, 255), (255, 255, 255),
                    ])
                })

        # 更新冰雪粒子
        for ip in self.ice_particles[:]:
            ip['x'] += ip['vx'] * dt
            ip['y'] += ip['vy'] * dt
            ip['life'] -= dt
            scale_factor = 0.92 ** dt
            ip['radius'] = max(1, int(ip['radius'] * scale_factor))
            if ip['life'] <= 0:
                self.ice_particles.remove(ip)

    def get_hitboxes(self):
        """雪人有三個雪球的碰撞區域"""
        bottom_r = self.radius
        bottom_y = self.y + 50
        body_r = int(self.radius * 0.7)
        body_y = bottom_y - bottom_r - body_r + 10
        head_r = int(self.radius * 0.5)
        head_y = body_y - body_r - head_r + 8
        return [
            (self.x, bottom_y, bottom_r),
            (self.x, body_y, body_r),
            (self.x, head_y, head_r),
        ]

    def draw(self, surface):
        if self.is_dead:
            return

        snow_color = (240, 248, 255)
        outline_color = (180, 200, 220)
        if self.flash_timer > 0:
            snow_color = (150, 200, 255)
            outline_color = (100, 150, 255)

        bottom_r = self.radius
        bottom_y = self.y + 50
        body_r = int(self.radius * 0.7)
        body_y = bottom_y - bottom_r - body_r + 10
        head_r = int(self.radius * 0.5)
        head_y = body_y - body_r - head_r + 8

        # 樹枝手臂
        arm_color = (101, 67, 33)
        left_arm_start = (self.x - body_r, body_y)
        left_arm_end = (self.x - body_r - 40, body_y - 30)
        pygame.draw.line(surface, arm_color, left_arm_start, left_arm_end, 4)
        pygame.draw.line(surface, arm_color, left_arm_end,
                         (left_arm_end[0] - 10, left_arm_end[1] - 15), 3)
        pygame.draw.line(surface, arm_color, left_arm_end,
                         (left_arm_end[0] - 15, left_arm_end[1] - 5), 3)

        right_arm_start = (self.x + body_r, body_y)
        right_arm_end = (self.x + body_r + 40, body_y - 30)
        pygame.draw.line(surface, arm_color, right_arm_start, right_arm_end, 4)
        pygame.draw.line(surface, arm_color, right_arm_end,
                         (right_arm_end[0] + 10, right_arm_end[1] - 15), 3)
        pygame.draw.line(surface, arm_color, right_arm_end,
                         (right_arm_end[0] + 15, right_arm_end[1] - 5), 3)

        # 三個雪球
        pygame.draw.circle(surface, snow_color, (self.x, bottom_y), bottom_r)
        pygame.draw.circle(surface, outline_color, (self.x, bottom_y), bottom_r, 2)
        pygame.draw.circle(surface, snow_color, (self.x, body_y), body_r)
        pygame.draw.circle(surface, outline_color, (self.x, body_y), body_r, 2)
        pygame.draw.circle(surface, snow_color, (self.x, head_y), head_r)
        pygame.draw.circle(surface, outline_color, (self.x, head_y), head_r, 2)

        # 帽子
        hat_brim_y = head_y - head_r + 3
        hat_width = int(head_r * 1.6)
        hat_top_width = int(head_r * 1.0)
        hat_height = int(head_r * 1.2)
        pygame.draw.rect(surface, (30, 30, 30),
                         (self.x - hat_top_width // 2, hat_brim_y - hat_height,
                          hat_top_width, hat_height))
        pygame.draw.rect(surface, (30, 30, 30),
                         (self.x - hat_width // 2, hat_brim_y - 4, hat_width, 6))
        pygame.draw.rect(surface, (200, 50, 50),
                         (self.x - hat_top_width // 2, hat_brim_y - 10,
                          hat_top_width, 5))

        # 眼睛
        eye_y = head_y - 5
        pygame.draw.circle(surface, (0, 0, 0), (self.x - 8, eye_y), 4)
        pygame.draw.circle(surface, (0, 0, 0), (self.x + 8, eye_y), 4)

        # 胡蘿蔔鼻子
        nose_points = [
            (self.x, head_y + 2),
            (self.x + 20, head_y + 5),
            (self.x, head_y + 8)
        ]
        pygame.draw.polygon(surface, (255, 140, 0), nose_points)

        # 嘴巴
        mouth_y = head_y + 12
        for i in range(5):
            mx = self.x - 8 + i * 4
            my = mouth_y + abs(i - 2) * 2
            pygame.draw.circle(surface, (0, 0, 0), (mx, my), 2)

        # 鈕釦
        for i in range(3):
            btn_y = body_y - 12 + i * 12
            pygame.draw.circle(surface, (0, 0, 0), (self.x, btn_y), 4)

        # 血條
        bar_width = 100
        hp_ratio = max(0, self.hp / self.max_hp)
        bar_y = head_y - head_r - hat_height - 20
        pygame.draw.rect(surface, (100, 100, 100),
                         (self.x - 50, bar_y, bar_width, 10))
        pygame.draw.rect(surface, (255, 0, 0),
                         (self.x - 50, bar_y, int(bar_width * hp_ratio), 10))

    def draw_projectiles(self, surface):
        """繪製冰雪粒子與雪球子彈"""
        # 冰雪拖尾粒子
        ice_surface = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        for ip in self.ice_particles:
            alpha = int(200 * (ip['life'] / ip['max_life']))
            color_a = (ip['color'][0], ip['color'][1], ip['color'][2], alpha)
            pygame.draw.circle(ice_surface, color_a,
                               (int(ip['x']), int(ip['y'])), ip['radius'])
        surface.blit(ice_surface, (0, 0))

        # 雪球子彈
        for p in self.projectiles:
            glow_s = pygame.Surface((p['radius'] * 4, p['radius'] * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (150, 210, 255, 50),
                               (p['radius'] * 2, p['radius'] * 2), p['radius'] * 2)
            surface.blit(glow_s,
                         (int(p['x']) - p['radius'] * 2,
                          int(p['y']) - p['radius'] * 2))
            pygame.draw.circle(surface, (180, 220, 255),
                               (int(p['x']), int(p['y'])), p['radius'])
            pygame.draw.circle(surface, (230, 245, 255),
                               (int(p['x']) - 3, int(p['y']) - 3),
                               p['radius'] // 2)


# ==============================================================
#  小幽靈敵人 (GhostEnemy)
# ==============================================================
class GhostEnemy(BaseEnemy):
    """
    小幽靈敵人：半透明、以正弦波軌跡飄動，血量較低但移動較難預測。
    子彈為紫色靈魂火焰。
    """

    def __init__(self, screen_w, screen_h):
        # 小幽靈出現在雪人前方（稍微靠中間）
        super().__init__(screen_w, screen_h,
                         hp=50,
                         x=screen_w - 350,
                         y=screen_h // 3,
                         radius=30)
        # 正弦波飄動用的計數器
        self.wave_timer = 0.0
        self.wave_amplitude = 80   # 飄動幅度（像素）
        self.wave_speed = 0.05     # 飄動速度
        self.base_y = self.y       # 波動的中心 Y 座標

        # 小幽靈攻擊間隔稍快
        self.attack_interval = 150
        self.speed_y = 1.5

        # 幽靈尾巴粒子
        self.trail_particles = []

    def reset(self):
        super().reset()
        self.wave_timer = 0.0
        self.base_y = random.randint(200, self.screen_h - 200)
        self.y = self.base_y
        self.trail_particles = []

    def update(self, dt=1.0):
        if self.is_dead:
            return

        # 正弦波飄動（取代基底的上下巡邏）
        self.wave_timer += self.wave_speed * dt
        self.base_y += self.speed_y * self.direction * dt * 0.5

        # 邊界反彈
        if self.base_y >= self.move_bottom:
            self.base_y = self.move_bottom
            self.direction = -1
        elif self.base_y <= self.move_top:
            self.base_y = self.move_top
            self.direction = 1

        # 用正弦波讓 Y 座標上下波動
        self.y = self.base_y + math.sin(self.wave_timer) * self.wave_amplitude

        # 攻擊計時
        self.attack_timer += dt
        if self.attack_timer >= self.attack_interval:
            self.attack_timer = random.uniform(0, 40)
            self.shoot_projectile()

        # 受傷閃爍
        if self.flash_timer > 0:
            self.flash_timer -= dt

        # 更新子彈
        for p in self.projectiles[:]:
            p['x'] -= p['vx'] * dt
            if p['x'] < 0:
                self.projectiles.remove(p)

        # 產生幽靈尾巴粒子
        for _ in range(random.randint(1, 3)):
            self.trail_particles.append({
                'x': self.x + random.randint(-10, 10),
                'y': self.y + self.radius + random.randint(0, 15),
                'vy': random.uniform(0.5, 1.5),
                'radius': random.randint(3, 7),
                'life': random.randint(10, 20),
                'max_life': 20,
            })

        # 更新尾巴粒子
        for tp in self.trail_particles[:]:
            tp['y'] += tp['vy'] * dt
            tp['life'] -= dt
            tp['radius'] = max(1, int(tp['radius'] * (0.95 ** dt)))
            if tp['life'] <= 0:
                self.trail_particles.remove(tp)

    def shoot_projectile(self):
        """發射紫色靈魂火焰子彈"""
        self.projectiles.append({
            'x': self.x,
            'y': self.y + random.randint(-20, 20),
            'vx': 6,        # 速度比雪球稍慢
            'radius': 12,
            'damage': 8      # 傷害比雪球稍低
        })

    def get_hitboxes(self):
        """小幽靈只有一個圓形碰撞區"""
        return [(self.x, int(self.y), self.radius)]

    def draw(self, surface):
        if self.is_dead:
            return

        # 半透明繪製層
        ghost_surface = pygame.Surface(
            (self.screen_w, self.screen_h), pygame.SRCALPHA
        )

        # 幽靈主體顏色（受傷時閃爍）
        base_alpha = 160
        if self.flash_timer > 0:
            body_color = (200, 100, 255, base_alpha)
            outline_color = (255, 150, 255, 200)
        else:
            body_color = (180, 200, 255, base_alpha)
            outline_color = (150, 170, 255, 200)

        gx = self.x
        gy = int(self.y)

        # --- 幽靈尾巴粒子（在主體下方） ---
        for tp in self.trail_particles:
            alpha = int(120 * (tp['life'] / tp['max_life']))
            pygame.draw.circle(ghost_surface, (180, 200, 255, alpha),
                               (int(tp['x']), int(tp['y'])), tp['radius'])

        # --- 幽靈身體（橢圓形 + 波浪底部） ---
        # 主體圓形
        pygame.draw.circle(ghost_surface, body_color, (gx, gy), self.radius)
        # 裙擺（用三個小半圓模擬波浪底部）
        skirt_y = gy + self.radius
        for i in range(3):
            sx = gx - self.radius + 10 + i * 20
            pygame.draw.circle(ghost_surface, body_color, (sx, skirt_y), 10)

        # 輪廓
        pygame.draw.circle(ghost_surface, outline_color, (gx, gy), self.radius, 2)

        # --- 眼睛（大大的可愛眼睛） ---
        eye_y = gy - 5
        # 白色眼框
        pygame.draw.circle(ghost_surface, (255, 255, 255, 220),
                           (gx - 10, eye_y), 8)
        pygame.draw.circle(ghost_surface, (255, 255, 255, 220),
                           (gx + 10, eye_y), 8)
        # 黑色瞳孔
        pygame.draw.circle(ghost_surface, (30, 30, 80, 255),
                           (gx - 10, eye_y), 4)
        pygame.draw.circle(ghost_surface, (30, 30, 80, 255),
                           (gx + 10, eye_y), 4)

        # --- 嘴巴（小小的 O 形） ---
        pygame.draw.circle(ghost_surface, (100, 120, 200, 200),
                           (gx, gy + 10), 5)
        pygame.draw.circle(ghost_surface, (180, 200, 255, base_alpha),
                           (gx, gy + 10), 3)

        surface.blit(ghost_surface, (0, 0))

        # --- 血條 ---
        bar_width = 60
        hp_ratio = max(0, self.hp / self.max_hp)
        bar_y = gy - self.radius - 15
        pygame.draw.rect(surface, (100, 100, 100),
                         (gx - 30, bar_y, bar_width, 8))
        pygame.draw.rect(surface, (180, 100, 255),
                         (gx - 30, bar_y, int(bar_width * hp_ratio), 8))

    def draw_projectiles(self, surface):
        """繪製紫色靈魂火焰子彈"""
        for p in self.projectiles:
            # 外層光暈
            glow_s = pygame.Surface((p['radius'] * 4, p['radius'] * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (180, 100, 255, 40),
                               (p['radius'] * 2, p['radius'] * 2), p['radius'] * 2)
            surface.blit(glow_s,
                         (int(p['x']) - p['radius'] * 2,
                          int(p['y']) - p['radius'] * 2))
            # 外層紫色
            pygame.draw.circle(surface, (160, 80, 220),
                               (int(p['x']), int(p['y'])), p['radius'])
            # 內核亮色
            pygame.draw.circle(surface, (220, 180, 255),
                               (int(p['x']) - 2, int(p['y']) - 2),
                               p['radius'] // 2)


# ==============================================================
#  小丑敵人 (ClownEnemy) — 第二關
# ==============================================================
class ClownEnemy(BaseEnemy):
    """
    小丑敵人：會不規則瞬移，發射彩色氣球炸彈。
    瞬移機制讓玩家難以瞄準，增加挑戰性。
    """

    def __init__(self, screen_w, screen_h):
        super().__init__(screen_w, screen_h,
                         hp=80,
                         x=screen_w - 300,
                         y=screen_h // 2,
                         radius=35)
        # 瞬移計時器
        self.teleport_timer = 0
        self.teleport_interval = 180  # 每 180 幀瞬移一次 (~3秒)
        self.teleport_flash = 0       # 瞬移閃光效果

        # 攻擊間隔比幽靈快
        self.attack_interval = 100

        # 氣球顏色列表
        self.balloon_colors = [
            (255, 80, 80),    # 紅
            (80, 255, 80),    # 綠
            (80, 80, 255),    # 藍
            (255, 255, 80),   # 黃
            (255, 80, 255),   # 粉紅
            (80, 255, 255),   # 青
        ]

    def reset(self):
        super().reset()
        self.teleport_timer = 0
        self.teleport_flash = 0

    def update(self, dt=1.0):
        if self.is_dead:
            return

        # 基本上下移動（比較快）
        self.y += self.speed_y * self.direction * dt * 1.5
        if self.y >= self.move_bottom:
            self.y = self.move_bottom
            self.direction = -1
        elif self.y <= self.move_top:
            self.y = self.move_top
            self.direction = 1

        # 瞬移邏輯
        self.teleport_timer += dt
        if self.teleport_timer >= self.teleport_interval:
            self.teleport_timer = random.uniform(0, 30)
            self.y = random.randint(self.move_top, self.move_bottom)
            self.teleport_flash = 15  # 瞬移閃光持續 15 幀

        if self.teleport_flash > 0:
            self.teleport_flash -= dt

        # 攻擊計時
        self.attack_timer += dt
        if self.attack_timer >= self.attack_interval:
            self.attack_timer = random.uniform(0, 30)
            self.shoot_projectile()

        # 受傷閃爍
        if self.flash_timer > 0:
            self.flash_timer -= dt

        # 更新子彈
        for p in self.projectiles[:]:
            p['x'] -= p['vx'] * dt
            if p['x'] < 0:
                self.projectiles.remove(p)

    def shoot_projectile(self):
        """發射彩色氣球炸彈"""
        color = random.choice(self.balloon_colors)
        self.projectiles.append({
            'x': self.x,
            'y': self.y + random.randint(-20, 20),
            'vx': 7,
            'radius': 14,
            'damage': 10,
            'color': color,
        })

    def get_hitboxes(self):
        """小丑有頭部和身體兩個碰撞區"""
        body_y = self.y + 10
        head_y = self.y - 30
        return [
            (self.x, body_y, self.radius),
            (self.x, head_y, int(self.radius * 0.6)),
        ]

    def draw(self, surface):
        if self.is_dead:
            return

        gx = self.x
        gy = self.y

        # 瞬移閃光效果
        if self.teleport_flash > 0:
            flash_s = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            alpha = int(150 * (self.teleport_flash / 15))
            pygame.draw.circle(flash_s, (255, 255, 100, alpha), (gx, gy), 60)
            surface.blit(flash_s, (0, 0))

        # 顏色設定
        if self.flash_timer > 0:
            body_color = (255, 150, 150)
            outline = (255, 80, 80)
        else:
            body_color = (255, 230, 200)
            outline = (200, 150, 100)

        # --- 身體（梯形衣服） ---
        body_top = gy - 10
        body_bottom = gy + 40
        body_points = [
            (gx - 25, body_top),
            (gx + 25, body_top),
            (gx + 35, body_bottom),
            (gx - 35, body_bottom),
        ]
        # 彩色條紋衣服
        pygame.draw.polygon(surface, (255, 80, 80), body_points)
        pygame.draw.polygon(surface, outline, body_points, 2)
        # 條紋裝飾
        for i in range(3):
            stripe_y = body_top + 10 + i * 12
            stripe_colors = [(80, 80, 255), (255, 255, 80), (80, 255, 80)]
            left_x = gx - 25 - int((stripe_y - body_top) * 0.2)
            right_x = gx + 25 + int((stripe_y - body_top) * 0.2)
            pygame.draw.line(surface, stripe_colors[i],
                             (left_x, stripe_y), (right_x, stripe_y), 3)

        # --- 頭部 ---
        head_y = gy - 30
        head_r = int(self.radius * 0.6)
        pygame.draw.circle(surface, body_color, (gx, head_y), head_r)
        pygame.draw.circle(surface, outline, (gx, head_y), head_r, 2)

        # --- 小丑帽（三角錐+球） ---
        hat_points = [
            (gx - 15, head_y - head_r + 5),
            (gx + 15, head_y - head_r + 5),
            (gx + 5, head_y - head_r - 30),
        ]
        pygame.draw.polygon(surface, (80, 80, 255), hat_points)
        pygame.draw.polygon(surface, (60, 60, 200), hat_points, 2)
        pygame.draw.circle(surface, (255, 255, 0),
                           (gx + 5, head_y - head_r - 30), 6)

        # --- 眼睛 ---
        eye_y = head_y - 3
        pygame.draw.circle(surface, (255, 255, 255), (gx - 8, eye_y), 6)
        pygame.draw.circle(surface, (255, 255, 255), (gx + 8, eye_y), 6)
        pygame.draw.circle(surface, (0, 0, 0), (gx - 8, eye_y), 3)
        pygame.draw.circle(surface, (0, 0, 0), (gx + 8, eye_y), 3)

        # --- 紅鼻子 ---
        pygame.draw.circle(surface, (255, 0, 0), (gx, head_y + 5), 7)
        pygame.draw.circle(surface, (255, 100, 100), (gx - 2, head_y + 3), 3)

        # --- 大笑的嘴巴 ---
        mouth_rect = pygame.Rect(gx - 12, head_y + 10, 24, 10)
        pygame.draw.arc(surface, (200, 0, 0), mouth_rect, 3.14, 6.28, 3)

        # --- 血條 ---
        bar_width = 80
        hp_ratio = max(0, self.hp / self.max_hp)
        bar_y = head_y - head_r - 40
        pygame.draw.rect(surface, (100, 100, 100),
                         (gx - 40, bar_y, bar_width, 8))
        pygame.draw.rect(surface, (255, 200, 0),
                         (gx - 40, bar_y, int(bar_width * hp_ratio), 8))

    def draw_projectiles(self, surface):
        """繪製彩色氣球子彈"""
        for p in self.projectiles:
            color = p.get('color', (255, 80, 80))
            # 氣球光暈
            glow_s = pygame.Surface((p['radius'] * 4, p['radius'] * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (*color, 40),
                               (p['radius'] * 2, p['radius'] * 2), p['radius'] * 2)
            surface.blit(glow_s,
                         (int(p['x']) - p['radius'] * 2,
                          int(p['y']) - p['radius'] * 2))
            # 氣球主體（橢圓）
            balloon_rect = pygame.Rect(
                int(p['x']) - p['radius'],
                int(p['y']) - int(p['radius'] * 1.3),
                p['radius'] * 2,
                int(p['radius'] * 2.6)
            )
            pygame.draw.ellipse(surface, color, balloon_rect)
            # 氣球高光
            pygame.draw.circle(surface, (255, 255, 255),
                               (int(p['x']) - 3, int(p['y']) - 4),
                               p['radius'] // 3)
            # 氣球繩子
            pygame.draw.line(surface, (150, 150, 150),
                             (int(p['x']), int(p['y']) + int(p['radius'] * 1.3)),
                             (int(p['x']) + 3, int(p['y']) + int(p['radius'] * 1.8)),
                             2)


# ==============================================================
#  大象敵人 (ElephantEnemy) — 第二關
# ==============================================================
class ElephantEnemy(BaseEnemy):
    """
    大象敵人：高血量的坦克型角色，移動緩慢但攻擊力強。
    用鼻子噴出水柱子彈，子彈大顆但速度慢。
    """

    def __init__(self, screen_w, screen_h):
        super().__init__(screen_w, screen_h,
                         hp=150,
                         x=screen_w - 180,
                         y=screen_h // 2,
                         radius=55)
        # 大象移動較慢
        self.speed_y = 1.0
        # 攻擊間隔稍長，但傷害高
        self.attack_interval = 90

        # 鼻子擺動動畫
        self.trunk_angle = 0.0
        self.trunk_speed = 0.03

        # 水花粒子
        self.water_particles = []

    def reset(self):
        super().reset()
        self.trunk_angle = 0.0
        self.water_particles = []

    def update(self, dt=1.0):
        super().update(dt)
        if self.is_dead:
            return

        # 鼻子擺動
        self.trunk_angle += self.trunk_speed * dt

        # 為水柱子彈產生水花粒子
        for p in self.projectiles:
            for _ in range(random.randint(1, 3)):
                self.water_particles.append({
                    'x': p['x'] + random.randint(-5, 5),
                    'y': p['y'] + random.randint(-8, 8),
                    'vx': random.uniform(0.3, 1.5),
                    'vy': random.uniform(-1.0, 1.0),
                    'radius': random.randint(2, 4),
                    'life': random.randint(6, 12),
                    'max_life': 12,
                })

        # 更新水花粒子
        for wp in self.water_particles[:]:
            wp['x'] += wp['vx'] * dt
            wp['y'] += wp['vy'] * dt
            wp['life'] -= dt
            if wp['life'] <= 0:
                self.water_particles.remove(wp)

    def shoot_projectile(self):
        """發射水柱子彈（大顆、慢速、高傷害）"""
        self.projectiles.append({
            'x': self.x - self.radius,
            'y': self.y + random.randint(-15, 15),
            'vx': 5,       # 速度較慢
            'radius': 20,  # 子彈較大
            'damage': 15,  # 傷害較高
        })

    def get_hitboxes(self):
        """大象有頭部和身體兩個碰撞區"""
        body_r = self.radius
        head_r = int(self.radius * 0.55)
        head_x = self.x - body_r + 10
        head_y = self.y - 20
        return [
            (self.x, self.y, body_r),
            (head_x, head_y, head_r),
        ]

    def draw(self, surface):
        if self.is_dead:
            return

        gx = self.x
        gy = self.y

        # 顏色
        if self.flash_timer > 0:
            body_color = (180, 180, 220)
            dark_color = (140, 140, 180)
        else:
            body_color = (160, 160, 170)
            dark_color = (120, 120, 130)

        # --- 尾巴 ---
        tail_x = gx + self.radius - 5
        tail_points = [
            (tail_x, gy),
            (tail_x + 15, gy - 10),
            (tail_x + 20, gy - 20),
        ]
        pygame.draw.lines(surface, dark_color, False, tail_points, 3)
        pygame.draw.circle(surface, dark_color,
                           (tail_x + 20, gy - 20), 4)

        # --- 腿（四條粗短腿） ---
        leg_color = dark_color
        leg_w = 14
        leg_h = 30
        for lx_offset in [-30, -10, 10, 30]:
            leg_rect = pygame.Rect(
                gx + lx_offset - leg_w // 2,
                gy + self.radius - 15,
                leg_w, leg_h
            )
            pygame.draw.rect(surface, leg_color, leg_rect, border_radius=4)
            # 腳趾甲
            pygame.draw.rect(surface, (200, 200, 210),
                             (leg_rect.x + 2, leg_rect.bottom - 6,
                              leg_w - 4, 6), border_radius=3)

        # --- 身體（大橢圓） ---
        body_rect = pygame.Rect(
            gx - self.radius, gy - int(self.radius * 0.7),
            self.radius * 2, int(self.radius * 1.4)
        )
        pygame.draw.ellipse(surface, body_color, body_rect)
        pygame.draw.ellipse(surface, dark_color, body_rect, 2)

        # --- 頭部 ---
        head_r = int(self.radius * 0.55)
        head_x = gx - self.radius + 10
        head_y = gy - 20
        pygame.draw.circle(surface, body_color, (head_x, head_y), head_r)
        pygame.draw.circle(surface, dark_color, (head_x, head_y), head_r, 2)

        # --- 耳朵（大大的扇形） ---
        ear_color = (190, 140, 160)
        # 左耳
        ear_rect_l = pygame.Rect(head_x - head_r - 20, head_y - 25, 30, 45)
        pygame.draw.ellipse(surface, body_color, ear_rect_l)
        inner_ear_l = pygame.Rect(head_x - head_r - 15, head_y - 18, 20, 32)
        pygame.draw.ellipse(surface, ear_color, inner_ear_l)

        # --- 眼睛 ---
        eye_y = head_y - 5
        pygame.draw.circle(surface, (255, 255, 255),
                           (head_x - 8, eye_y), 7)
        pygame.draw.circle(surface, (30, 30, 30),
                           (head_x - 8, eye_y), 4)
        pygame.draw.circle(surface, (255, 255, 255),
                           (head_x - 10, eye_y - 2), 2)

        # --- 鼻子（長鼻子，帶擺動） ---
        trunk_swing = math.sin(self.trunk_angle) * 10
        trunk_points = [
            (head_x - head_r + 5, head_y + 5),
            (head_x - head_r - 15, head_y + 15 + trunk_swing),
            (head_x - head_r - 25, head_y + 30 + trunk_swing * 0.5),
            (head_x - head_r - 20, head_y + 40),
        ]
        pygame.draw.lines(surface, body_color, False, trunk_points, 12)
        pygame.draw.lines(surface, dark_color, False, trunk_points, 2)

        # --- 象牙 ---
        tusk_start = (head_x - head_r + 8, head_y + 10)
        tusk_end = (head_x - head_r - 5, head_y + 25)
        pygame.draw.line(surface, (255, 255, 240), tusk_start, tusk_end, 4)

        # --- 血條 ---
        bar_width = 110
        hp_ratio = max(0, self.hp / self.max_hp)
        bar_y = head_y - head_r - 20
        pygame.draw.rect(surface, (100, 100, 100),
                         (gx - 55, bar_y, bar_width, 10))
        pygame.draw.rect(surface, (80, 180, 255),
                         (gx - 55, bar_y, int(bar_width * hp_ratio), 10))

    def draw_projectiles(self, surface):
        """繪製水柱子彈與水花粒子"""
        # 水花粒子
        water_s = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        for wp in self.water_particles:
            alpha = int(180 * (wp['life'] / wp['max_life']))
            pygame.draw.circle(water_s, (100, 180, 255, alpha),
                               (int(wp['x']), int(wp['y'])), wp['radius'])
        surface.blit(water_s, (0, 0))

        # 水柱子彈
        for p in self.projectiles:
            # 光暈
            glow_s = pygame.Surface((p['radius'] * 4, p['radius'] * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (80, 160, 255, 50),
                               (p['radius'] * 2, p['radius'] * 2), p['radius'] * 2)
            surface.blit(glow_s,
                         (int(p['x']) - p['radius'] * 2,
                          int(p['y']) - p['radius'] * 2))
            # 主體
            pygame.draw.circle(surface, (80, 160, 255),
                               (int(p['x']), int(p['y'])), p['radius'])
            # 高光
            pygame.draw.circle(surface, (200, 230, 255),
                               (int(p['x']) - 4, int(p['y']) - 4),
                               p['radius'] // 2)


# ==============================================================
#  敵人管理器 (EnemySystem)
#  統一管理所有敵人，提供與 main.py 相容的介面
# ==============================================================
class EnemySystem:
    """
    管理所有敵人的系統。
    支援關卡切換：第 1 關為雪人+幽靈，第 2 關為小丑+大象。
    """

    def __init__(self, screen_width=1280, screen_height=720):
        self.screen_w = screen_width
        self.screen_h = screen_height
        self.current_level = 1

        # 初始為第一關敵人
        self.enemies = []
        self.set_level(1)

    def set_level(self, level):
        """
        根據關卡編號設定敵人陣容。
        第 1 關：雪人 + 幽靈
        第 2 關：小丑 + 大象
        """
        self.current_level = level
        if level == 1:
            self.enemies = [
                SnowmanEnemy(self.screen_w, self.screen_h),
                GhostEnemy(self.screen_w, self.screen_h),
            ]
        elif level == 2:
            self.enemies = [
                ClownEnemy(self.screen_w, self.screen_h),
                ElephantEnemy(self.screen_w, self.screen_h),
            ]
        else:
            # 預設回到第一關
            self.enemies = [
                SnowmanEnemy(self.screen_w, self.screen_h),
                GhostEnemy(self.screen_w, self.screen_h),
            ]

    @property
    def projectiles(self):
        """合併所有敵人的子彈列表（供碰撞偵測使用）"""
        all_proj = []
        for enemy in self.enemies:
            all_proj.extend(enemy.projectiles)
        return all_proj

    @property
    def is_dead(self):
        """所有敵人都死亡時才算通關"""
        return all(e.is_dead for e in self.enemies)

    def update(self, dt=1.0):
        """更新所有敵人"""
        for enemy in self.enemies:
            enemy.update(dt)

    def check_hit(self, px, py, p_radius=0):
        """檢查攻擊是否命中任一存活的敵人，回傳被命中的敵人或 None"""
        for enemy in self.enemies:
            if not enemy.is_dead and enemy.check_hit(px, py, p_radius):
                return enemy
        return None

    def check_beam_hit(self, beam_x, beam_y, beam_width=30):
        """檢查射線是否命中任一敵人，回傳 (是否命中, 最近邊緣X)"""
        closest_edge_x = None
        hit_enemy = None
        for enemy in self.enemies:
            if enemy.is_dead:
                continue
            h, ex = enemy.check_beam_hit(beam_x, beam_y, beam_width)
            if h:
                if closest_edge_x is None or ex < closest_edge_x:
                    closest_edge_x = ex
                    hit_enemy = enemy
        if hit_enemy:
            return True, closest_edge_x
        return False, None

    def take_damage(self, damage):
        """向第一個存活的敵人施加傷害（向後相容用）"""
        for enemy in self.enemies:
            if not enemy.is_dead:
                enemy.take_damage(damage)
                return

    def reset_enemy(self):
        """重置當前關卡的所有敵人"""
        for enemy in self.enemies:
            enemy.reset()

    def draw(self, surface):
        """繪製所有敵人及其子彈"""
        for enemy in self.enemies:
            enemy.draw(surface)
            enemy.draw_projectiles(surface)

