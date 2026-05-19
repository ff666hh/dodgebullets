# Dodgebullets

[觀看示範影片](https://youtu.be/jQOALIRhK_c)

簡短說明
--
一個以手勢與即時手部追蹤為互動方式的躲避射擊小遊戲範例，使用攝影機偵測手勢來控制角色移動與施放技能，並包含音效與基本 UI 顯示。

主要功能
--
- 即時手部追蹤與手勢辨識（使用手標記檔案 `hand_landmarker.task`）
- 敵人產生與行為系統（`enemy_system.py`）
- 技能施放系統（`spell_system.py`）
- 音效系統（`sound_system.py`）
- 簡易 UI 顯示（`ui_system.py`）

系統需求
--
- 作業系統：Windows / macOS / Linux
- Python 3.8+
- 網路攝影機（webcam）或其他相機輸入

安裝
--
1. 建議使用虛擬環境（範例名稱：`uv`）：

```bash
# 建立虛擬環境（名稱為 uv）
python -m venv uv

# 啟用（Windows PowerShell）
.\uv\Scripts\Activate.ps1

# 或 Windows cmd:
.\uv\Scripts\activate

# macOS / Linux:
source uv/bin/activate
```

2. 安裝相依套件：

- 本專案採用 `pyproject.toml` 管理相依性（如使用 poetry 或直接用 pip）：

```bash
# 若你使用 poetry
poetry install

# 或使用 pip（若你已將相依寫入 requirements.txt）
pip install -r requirements.txt

# 若想以可編輯模式安裝（若 pyproject 支援）
pip install -e .
```

執行
--
1. 啟動 `uv` 虛擬環境，例如：

```bash
# Windows PowerShell
.\uv\Scripts\Activate.ps1

# macOS / Linux
source uv/bin/activate
```

2. 執行主程式：

```bash
python main.py
```

操作說明（快速）
--
- 將會開啟攝影機視窗，透過手部或手勢控制遊戲中的角色。具體手勢對應請查看 `gesture_recognition.py` 與 `hand_tracking.py` 的實作。
- 螢幕上會顯示簡單 UI（分數、血量等），音效由 `sound_system.py` 控制。

專案結構（重點檔案）
--
- `main.py`：遊戲啟動程式與主要迴圈
- `hand_tracking.py`：手部追蹤邏輯
- `gesture_recognition.py`：手勢辨識流程與對映行為
- `hand_landmarker.task`：手勢/手部模型設定檔
- `enemy_system.py`：敵人生成與行為
- `spell_system.py`：技能施放與管理
- `sound_system.py`：音效播放
- `ui_system.py`：畫面 UI 元件
- `pyproject.toml`：專案套件與設定

開發與貢獻
--
- 若要新增功能或修正 bug，請建立 branch 並發送 pull request。
- 建議先在本機執行並確認攝影機與相依套件正確運作，再提交變更。

授權
--
本專案預設採 MIT 授權（如需更改請在此說明）。

聯絡
--
如有問題或需要協助，請在專案中建立 issue 或直接聯絡作者。
