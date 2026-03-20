這是一個遊戲關卡的輔助程式

## 已完成實作

- 技術：Python + FastAPI + WebSocket + In-Memory
- 前端：手機優先單頁網頁（即時同步）
- 規則：10 層、每層 4 個位置（1,2,3,4）
- 功能：
	- 不需輸入玩家名稱
	- 僅提供四大顏色選取（紅、綠、藍、黃）
	- 答案改為點擊 10x4 grid 作答（每層點一格）
	- 即時顯示每層每個位置的人數/顏色
	- 預設灰色（無人）
	- 若多人同格，顯示混色漸層
	- 一鍵清空「所有人所有答案」

## 檔案

- `main.py`：FastAPI + WebSocket 後端
- `templates/index.html`：網頁 UI（輸入、即時顯示、清空）
- `requirements.txt`：Python 套件

## 啟動方式

1. 安裝套件

```bash
pip install -r requirements.txt
```

2. 啟動伺服器

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

3. 開啟瀏覽器

```text
http://127.0.0.1:8000
```

## 使用 ngrok 分享給隊友

在另一個終端機執行：

```bash
ngrok http 8000
```

將 ngrok 顯示的公開網址（https://...）傳給隊友，隊友開啟後可即時同步看到同一份資料。