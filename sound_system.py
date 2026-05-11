"""
sound_system.py — 音效系統模組
使用 numpy 合成波形，透過 Pygame 播放。
不需要外部音檔，所有音效都是程式即時產生的。
"""

import pygame
import numpy as np


class SoundSystem:
    """
    遊戲音效管理器。
    使用數學波形合成各種音效，包含攻擊音效、敵人死亡音效等。
    """

    def __init__(self):
        # 初始化 Pygame 混音器（設定取樣率與聲道）
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        self.sample_rate = 44100

        # 預先合成所有音效並存入字典
        self.sounds = {
            'fireball':    self._make_fireball_sound(),
            'lightning':   self._make_lightning_sound(),
            'magic_beam':  self._make_beam_sound(),
            'shield':      self._make_shield_sound(),
            'enemy_hit':   self._make_enemy_hit_sound(),
            'enemy_death': self._make_enemy_death_sound(),
            'player_hit':  self._make_player_hit_sound(),
            'level_clear': self._make_level_clear_sound(),
            'victory':     self._make_victory_sound(),
        }

        # 音效音量設定（0.0 ~ 1.0）
        for sound in self.sounds.values():
            sound.set_volume(0.4)

        # 特別調整部分音效音量
        self.sounds['enemy_death'].set_volume(0.5)
        self.sounds['level_clear'].set_volume(0.6)
        self.sounds['victory'].set_volume(0.6)

    def _make_sound(self, samples):
        """
        將 numpy 陣列轉換為 Pygame Sound 物件。
        samples: float 陣列，值範圍 -1.0 ~ 1.0
        """
        # 轉換為 16-bit 整數格式
        samples = np.clip(samples, -1.0, 1.0)
        audio_data = (samples * 32767).astype(np.int16)
        return pygame.mixer.Sound(buffer=audio_data.tobytes())

    def _make_fireball_sound(self):
        """火球術音效：低頻轟鳴 + 快速上升音"""
        duration = 0.3
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        # 從低到高的掃頻（200Hz → 600Hz）
        freq = 200 + 400 * (t / duration)
        wave = np.sin(2 * np.pi * freq * t) * 0.6
        # 加入一點噪音模擬火焰
        noise = np.random.uniform(-0.15, 0.15, len(t))
        # 音量包絡線：快速起音，緩慢衰減
        envelope = np.exp(-t * 8)
        return self._make_sound((wave + noise) * envelope)

    def _make_lightning_sound(self):
        """閃電音效：尖銳的高頻爆裂聲"""
        duration = 0.25
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        # 高頻方波
        wave = np.sign(np.sin(2 * np.pi * 800 * t)) * 0.3
        # 加入白噪音模擬電流劈啪聲
        noise = np.random.uniform(-0.4, 0.4, len(t))
        # 極快衰減
        envelope = np.exp(-t * 15)
        return self._make_sound((wave + noise) * envelope)

    def _make_beam_sound(self):
        """奧術光束音效：持續的高頻嗡嗡聲"""
        duration = 0.15
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = np.sin(2 * np.pi * 1000 * t) * 0.3
        wave += np.sin(2 * np.pi * 1500 * t) * 0.15
        envelope = np.ones(len(t))
        envelope[:200] = np.linspace(0, 1, 200)   # 淡入
        envelope[-200:] = np.linspace(1, 0, 200)   # 淡出
        return self._make_sound(wave * envelope)

    def _make_shield_sound(self):
        """護盾音效：柔和的上升泛音"""
        duration = 0.35
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = np.sin(2 * np.pi * 400 * t) * 0.3
        wave += np.sin(2 * np.pi * 600 * t) * 0.2
        wave += np.sin(2 * np.pi * 800 * t) * 0.1
        envelope = np.exp(-t * 4)
        return self._make_sound(wave * envelope)

    def _make_enemy_hit_sound(self):
        """敵人被擊中音效：短促的撞擊聲"""
        duration = 0.15
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = np.sin(2 * np.pi * 300 * t) * 0.5
        noise = np.random.uniform(-0.2, 0.2, len(t))
        envelope = np.exp(-t * 20)
        return self._make_sound((wave + noise) * envelope)

    def _make_enemy_death_sound(self):
        """敵人死亡音效：下降音調 + 爆裂感"""
        duration = 0.5
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        # 頻率從高到低（800Hz → 100Hz）
        freq = 800 - 700 * (t / duration)
        wave = np.sin(2 * np.pi * freq * t) * 0.5
        # 加入噪音爆裂感
        noise = np.random.uniform(-0.3, 0.3, len(t))
        noise_env = np.exp(-t * 10)
        envelope = np.exp(-t * 4)
        return self._make_sound(wave * envelope + noise * noise_env * 0.5)

    def _make_player_hit_sound(self):
        """玩家被擊中音效：低沉的衝擊聲"""
        duration = 0.2
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = np.sin(2 * np.pi * 150 * t) * 0.6
        noise = np.random.uniform(-0.15, 0.15, len(t))
        envelope = np.exp(-t * 12)
        return self._make_sound((wave + noise) * envelope)

    def _make_level_clear_sound(self):
        """過關音效：上升的三連音"""
        notes = [523, 659, 784]  # C5, E5, G5（大三和弦）
        samples = np.array([], dtype=np.float64)
        for note in notes:
            dur = 0.2
            t = np.linspace(0, dur, int(self.sample_rate * dur), False)
            wave = np.sin(2 * np.pi * note * t) * 0.4
            envelope = np.exp(-t * 5)
            samples = np.concatenate([samples, wave * envelope])
        return self._make_sound(samples)

    def _make_victory_sound(self):
        """勝利音效：歡樂的上行旋律"""
        notes = [523, 587, 659, 784, 1047]  # C5, D5, E5, G5, C6
        samples = np.array([], dtype=np.float64)
        for note in notes:
            dur = 0.15
            t = np.linspace(0, dur, int(self.sample_rate * dur), False)
            wave = np.sin(2 * np.pi * note * t) * 0.35
            wave += np.sin(2 * np.pi * note * 2 * t) * 0.1  # 泛音
            envelope = np.exp(-t * 4)
            samples = np.concatenate([samples, wave * envelope])
        return self._make_sound(samples)

    # ========== 播放介面 ==========

    def play(self, sound_name):
        """
        播放指定名稱的音效。
        如果音效名稱不存在則靜默忽略。
        """
        sound = self.sounds.get(sound_name)
        if sound:
            sound.play()

    def play_attack(self, spell_type):
        """
        根據法術類型播放對應的攻擊音效。
        spell_type: 'Fireball', 'Shield', 'Lightning', 'Magic Beam'
        """
        mapping = {
            'Fireball': 'fireball',
            'Shield': 'shield',
            'Lightning': 'lightning',
            'Magic Beam': 'magic_beam',
        }
        name = mapping.get(spell_type)
        if name:
            self.play(name)
