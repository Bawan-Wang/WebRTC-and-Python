# Backend Signaling and Receiver Foundation 執行計畫

## 目的

建立可讓瀏覽器作為 WebRTC sender、Python 作為 WebRTC receiver 的最小後端骨架。

本計畫聚焦在：

- FastAPI 應用程式入口
- offer/answer signaling API
- `aiortc` peer connection 建立與回收
- 視訊 track 接收與 frame 處理掛點

## 範圍

### 本次範圍內

- 建立後端目錄與應用程式入口
- 定義 SDP request/response schema
- 建立 `POST /api/webrtc/offer` 路由
- 建立 `RTCPeerConnection` 並完成 `setRemoteDescription` / `createAnswer` / `setLocalDescription`
- 監聽 `connectionstatechange` 與 `track`
- 將接收到的 frame 交給可替換的 processor
- 補上 peer connection 清理與資源回收

### 本次範圍外

- Vue 前端頁面與 UI
- 多人房間與 session 認證
- WebSocket signaling
- TURN 佈建
- 模型推理最佳化

## 目標產出

- 一個可啟動的 FastAPI 後端
- 一個可接受瀏覽器 offer 並回傳 answer 的 API
- 一個可收到 video track 並消費 frame 的 aiortc receiver 流程
- 一個可供後續 OpenCV / AI 使用的 processor 介面

## 執行項目

### 1. 應用程式骨架

- 建立後端入口，例如 `backend/app.py`
- 定義路由註冊與基本設定
- 規劃 `webrtc/` 模組放置 signaling、peer 管理與 processor

### 2. Signaling API

- 定義 offer request schema 與 answer response schema
- 建立 `POST /api/webrtc/offer`
- 驗證傳入的 `sdp` 與 `type`
- 回傳標準化的 answer payload

### 3. Peer Connection 管理

- 建立 `RTCPeerConnection` factory
- 在 connection state 變更時記錄與清理
- 管理正在存活的 peer connection 集合
- 在關閉、失敗或客戶端中斷時釋放資源

### 4. Receiver 與 Processor 掛點

- 將目前 `receiver.py` 中的 track handling 邏輯抽成可重用模組
- 在 `@pc.on("track")` 中只接收 `video` 類型
- 透過 `await track.recv()` 持續取得 `VideoFrame`
- 將 frame 轉成 ndarray 並交由 processor 處理

### 5. 錯誤處理

- 處理無效 SDP、連線失敗、track 中斷
- 避免例外導致 peer connection 洩漏
- 明確回傳 API 錯誤訊息，方便前端顯示

## 驗證方式

- 後端可正常啟動並暴露 signaling API
- 送入合法 offer 時可回傳合法 answer
- 後端收到視訊 track 後可進入 frame 消費流程
- 中斷連線後 peer connection 會被正確關閉與回收

## 完成定義

- 後端可在沒有前端 UI 的情況下被單獨測試
- signaling API 與 receiver 流程能穩定建立最小 WebRTC 通道
- 後續前端只需要接上 offer/answer 即可整合

## 風險與注意事項

- 若一開始就混入多人 session 管理，實作複雜度會快速上升
- 若 processor 直接做重度推理，可能阻塞接收迴圈
- 需明確規劃 peer connection 的生命週期，避免記憶體與 task 洩漏
