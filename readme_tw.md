# LLM-SLA

## 簡介
這個專案是一個LLM的測試程式，使用 Playwright 自動化網頁互動來管理和測試 AI 服務。專案的設計具有彈性，可以為每個服務添加相應的配置文件來擴展到不同類型的網頁AI服務。此外，使用者可以自訂 runner 以調整測試前後的處理邏輯。

## 功能
- **網頁介面**: 使用 Flask 提供一個簡單的網頁介面，使用者可以在其中管理配置、執行測試和查看使用說明。
- **配置管理**: 使用者可以新增和修改 AI 服務的配置。
- **測試執行**: 提供測試功能並顯示測試結果。
- **日誌管理**: 使用自訂的 Logger 類別來管理和美化日誌輸出。

## 安裝
1. 將此存儲庫複製到本地：
   ```bash
   git clone https://github.com/Yicheng-1218/LLM-SLA.git
   ```
2. 進入專案目錄：
   ```bash
   cd https://github.com/Yicheng-1218/LLM-SLA.git
   ```
3. 安裝所需的 Python 套件：
   ```bash
   pip install -r requirements.txt
   ```
   或
   ```bash
   uv add -r requirements.txt
   ```

## 使用方法
### 啟動應用程式
- 您可以使用雙擊 `start.bat` 文件自動打開瀏覽器並啟動 `app.py` 應用程式。

### 手動啟動
1. 手動啟動應用程式：
   ```bash
   python app.py
   ```
2. 打開瀏覽器並訪問 `http://localhost:5000` 以訪問應用程式。

## 配置
- 配置文件位於 `configs` 目錄中，格式為 JSON。
- 你可以透過網頁介面來新增或是更新 `config` 文件
- 每個配置文件應包括以下必填項目：
  - AI 服務名稱
  - AI 服務網址
  - 輸入選擇器
  - 回應選擇器
  - 測試提示詞
  - 同時使用人數
  - 測試持續時間（秒）
- 範例
```json
{
    "name": "service",
    "url": "https://example.com",
    "input_selector": "textarea[placeholder='Talk to Bot']",
    "response_selector": ".bot-message",
    "test_prompts": [
        "what is LLM?"
    ],
    "headless": false,
    "concurrency": 5,
    "test_duration": 60
}
```

## 測試
- 使用者可以選擇配置並執行測試。測試結果將顯示在應用程式中。

## 日誌
- 日誌文件儲存在 `logs` 目錄下，並使用 `CustomLogger` 進行管理。

## 貢獻
歡迎提交問題和請求，或直接發送 Pull Request。

## 授權
此專案使用 MIT 授權。
