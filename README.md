# Artale 關卡輔助程式

手機優先的即時協作工具。使用者可在同一個房間內同步選色、填寫 10 層 × 4 位置答案。

---

## 功能總覽

- 後端：FastAPI + WebSocket（記憶體儲存）
- 前端：單頁網頁（Mobile First）
- 登入機制：
	- 進入前需輸入房間密碼
	- 輸入玩家 ID（最多 8 字）
	- 玩家 ID 不可重複
- 顏色機制：
	- 共 8 種顏色可選
	- 顏色一旦被某玩家選走，其他玩家不可再選
	- 色塊上直接顯示該顏色目前持有者 ID
- 作答機制：
	- 每層可選 1 個位置（共 10 層、每層 4 格）
	- 顯示順序為第 10 層在上、第 1 層在下
	- 點自己已選的格子可取消
	- 點到他人已選格子會先詢問是否覆蓋
- 全域清空：
	- 可清空所有玩家所有答案
	- 有二次確認
- 其他：
	- 左上即時顯示在線人數
	- 所有變更即時同步給所有連線玩家

---

## 專案檔案

- main.py：FastAPI / WebSocket 伺服器與房間狀態
- templates/index.html：前端 UI 與即時互動邏輯
- requirements.txt：Python 套件清單

---

## 快速啟動

1) 安裝依賴

```bash
pip install -r requirements.txt
```

2) 啟動服務

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

3) 本機開啟

```text
http://127.0.0.1:8000
```

---

## 密碼設定

請在 main.py 內修改常數：

```python
ROOM_PASSWORD = "123456"
```

改完後重新啟動服務。

---

## 對外分享（ngrok）

```bash
ngrok http 8000
```

把 ngrok 提供的 https 網址分享給隊友即可協作。
