import pygame
import math
import random

class SpellSystem:
    def __init__(self):
        self.spells = []  # active spells on screen
        self.particles = []  # 火焰拖尾粒子列表
        self.cooldowns = {
            'Fireball': 0,
            'Shield': 0,
            'Lightning': 0,
            'Magic Beam': 0
        }
        self.max_cooldowns = {
            'Fireball': 30,      # frames (約 0.5s @ 60 FPS)
            'Shield': 120,       # 護盾冷卻較久
            'Lightning': 180,    # 閃電冷卻更久，傷害高
            'Magic Beam': 10     # 光束幾乎無冷卻，傷害低
        }
        self.shield_active_time = 0  # 現存護盾的剩餘時間

    def update(self, dt=1.0):
        # 更新冷卻時間 (乘以 dt)
        for spell in self.cooldowns:
            if self.cooldowns[spell] > 0:
                self.cooldowns[spell] = max(0, self.cooldowns[spell] - dt)

        # 更新護盾狀態
        if self.shield_active_time > 0:
            self.shield_active_time = max(0, self.shield_active_time - dt)

        # 更新魔法位置與生命週期
        for spell in self.spells[:]:
            if spell['type'] == 'Fireball':
                spell['x'] += spell['vx'] * dt
                if spell['x'] > 1280 or spell['x'] < 0:
                    self.spells.remove(spell)
                else:
                    # --- 產生火焰粒子 ---
                    for _ in range(random.randint(3, 5)):
                        self.particles.append({
                            'x': spell['x'] - spell['radius'] + random.randint(-5, 5),
                            'y': spell['y'] + random.randint(-10, 10),
                            'vx': random.uniform(-2, -0.5),
                            'vy': random.uniform(-1.5, 1.5),
                            'radius': random.randint(3, 8),
                            'life': random.randint(8, 15),
                            'max_life': 15,
                            'color': random.choice([
                                (255, 80, 0), (255, 140, 0), (255, 200, 50), (255, 50, 0), (255, 255, 100),
                            ])
                        })

            elif spell['type'] == 'Lightning' or spell['type'] == 'Magic Beam':
                spell['life'] -= dt
                if spell['life'] <= 0:
                    self.spells.remove(spell)

        # --- 更新火焰粒子 ---
        for p in self.particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt
            # 縮小速度補償
            scale_factor = 0.9 ** dt
            p['radius'] = max(1, int(p['radius'] * scale_factor))
            if p['life'] <= 0:
                self.particles.remove(p)

    def cast_spell(self, spell_type, start_x, start_y):
        """觸發魔法，檢查冷卻並加入到發射清單"""
        if self.cooldowns[spell_type] == 0:
            if spell_type == 'Fireball':
                self.spells.append({
                    'type': 'Fireball',
                    'x': start_x,
                    'y': start_y,
                    'vx': 15,  # 向右飛 (敵人通常在右側)
                    'vy': 0,
                    'radius': 30,
                    'damage': 20
                })
            elif spell_type == 'Shield':
                self.shield_active_time = 120 # 護盾持續 2 秒
                
            elif spell_type == 'Lightning':
                self.spells.append({
                    'type': 'Lightning',
                    'x': start_x,
                    'y': start_y,
                    'life': 10,  # 瞬間爆發，只存活 10 幀
                    'damage': 50,
                    'end_x': 1280
                })

            elif spell_type == 'Magic Beam':
                self.spells.append({
                    'type': 'Magic Beam',
                    'x': start_x,
                    'y': start_y,
                    'life': 5,
                    'damage': 5,
                    'end_x': 1280
                })

            # 進入冷卻
            self.cooldowns[spell_type] = self.max_cooldowns[spell_type]

    def draw(self, surface):
        """用 Pygame 繪製所有發動中的魔法"""
        # --- 先畫火焰粒子（在火球下層，避免遮擋主體） ---
        particle_surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
        for p in self.particles:
            # 根據剩餘生命計算透明度，越接近消失越透明
            alpha = int(255 * (p['life'] / p['max_life']))
            color_with_alpha = (p['color'][0], p['color'][1], p['color'][2], alpha)
            pygame.draw.circle(particle_surface, color_with_alpha,
                               (int(p['x']), int(p['y'])), p['radius'])
        surface.blit(particle_surface, (0, 0))

        for spell in self.spells:
            if spell['type'] == 'Fireball':
                # 外層火焰光暈（半透明橘色，營造發光效果）
                glow_surface = pygame.Surface((spell['radius'] * 4, spell['radius'] * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (255, 120, 0, 60),
                                   (spell['radius'] * 2, spell['radius'] * 2), spell['radius'] * 2)
                surface.blit(glow_surface,
                             (int(spell['x']) - spell['radius'] * 2,
                              int(spell['y']) - spell['radius'] * 2))
                # 主體火球
                pygame.draw.circle(surface, (255, 100, 0), (int(spell['x']), int(spell['y'])), spell['radius'])
                # 內核亮黃色
                pygame.draw.circle(surface, (255, 255, 0), (int(spell['x']), int(spell['y'])), spell['radius'] // 2)

            elif spell['type'] == 'Lightning':
                # 依據終點比例計算 y 軸的偏移量，保持閃電向下的角度
                end_x = spell.get('end_x', 1280)
                end_y = spell['y'] + int(50 * max(0, end_x - spell['x']) / 1280)
                pygame.draw.line(surface, (200, 200, 255), (spell['x'], spell['y']), (end_x, end_y), 10)
                pygame.draw.line(surface, (255, 255, 255), (spell['x'], spell['y']), (end_x, end_y), 4)

            elif spell['type'] == 'Magic Beam':
                end_x = spell.get('end_x', 1280)
                rect_width = max(0, end_x - spell['x'])
                pygame.draw.rect(surface, (0, 255, 255), (spell['x'], spell['y'] - 5, rect_width, 10))

        # 繪製護盾 (如果在啟動時間內)
        if self.shield_active_time > 0:
            s = pygame.Surface((1280, 720), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 150, 255, 100), (300, 360), 200) # 給玩家一個包覆的藍色結界
            pygame.draw.circle(s, (0, 200, 255, 150), (300, 360), 200, 5) # 外框
            surface.blit(s, (0, 0))
