# Vue + Python WebRTC Camera Uplink 執行計畫

## 目的

將目前的 Python sender -> Python receiver 架構，重構為：

- Vue 3 + Vite 前端使用 `getUserMedia()` 擷取攝影機
- Python 後端使用 FastAPI + aiortc 接收 WebRTC 視訊
- 後端保留 OpenCV / AI 處理能力

## 目標產出

- 一個可在瀏覽器啟動攝影機並送流到 Python 的前端頁面
- 一個可接收 SDP offer 並回傳 SDP answer 的 Python signaling API
- 一個可在 Python 端接收視訊 frame 並交給處理流程的 aiortc receiver
- 一份更新後的使用說明與測試方式

## 執行項目

### 1. 後端基礎重構

- 將目前 `receiver.py` 的接收邏輯拆成可重用模組
- 建立 FastAPI 應用程式入口
- 建立 `POST /api/webrtc/offer` signaling API
- 在 request 進來時建立 `RTCPeerConnection`
- 將 offer 設為 remote description，建立 answer 並回傳
- 為每個 peer connection 建立生命週期管理與清理機制

### 2. 視訊處理流程整理

- 保留目前 `VideoReceiver.handle_track(...)` 的核心能力
- 把 frame 轉換、時間戳、OpenCV 處理封裝成獨立 processor
- 定義是否保留預覽、存圖、推理等可選行為
- 避免預設每幀寫檔造成 I/O 壓力

### 3. 前端初始化

- 建立 Vue 3 + Vite 前端專案
- 建立攝影機預覽頁面
- 建立 `useWebRtcPublisher` composable 管理 WebRTC 狀態
- 實作開始送流與停止送流的 UI
- 顯示攝影機權限、連線狀態與錯誤訊息

### 4. WebRTC 前端流程

- 呼叫 `getUserMedia({ video: true, audio: false })`
- 建立 `RTCPeerConnection`
- 將 video track 加入 peer connection
- 建立 offer 並設定 local description
- 將 offer 傳送到 FastAPI signaling API
- 接收 answer 並設定 remote description
- 監聽 `connectionState` 與必要事件

### 5. 開發環境整合

- 設定 Vite dev server proxy 指向 Python API
- 處理本機開發期的 CORS 問題
- 規劃環境變數，例如 API base URL、STUN server 設定
- 確保前後端可分開啟動與整合測試

### 6. 網路與部署能力

- 第一版先以單機或同網段測試為目標
- 補上 STUN 設定，驗證基礎 NAT traversal
- 評估是否需要 TURN 支援外網或企業網路環境
- 規劃 HTTPS 需求，避免瀏覽器封鎖 `getUserMedia()`

### 7. 驗證與文件

- 驗證前端能夠取得攝影機畫面並顯示預覽
- 驗證前端 offer 與後端 answer 可以完成協商
- 驗證 Python 後端可穩定收到 frame
- 驗證中斷、重新整理、停止送流時的清理流程
- 更新 README 與使用方式

## 拆解子計畫

001 作為總體遷移計畫，負責維護範圍、順序、驗收標準與整體風險。實際執行時拆成以下子計畫：

- `002-backend-signaling-and-receiver-foundation.md`: FastAPI + aiortc 後端基礎、offer/answer signaling、peer lifecycle、track 接收
- `003-vue-camera-publisher-page.md`: Vue 3 + Vite 前端頁面、攝影機預覽、WebRTC publisher 流程與 UI 狀態
- `004-development-integration-and-networking.md`: Vite proxy、環境變數、CORS、STUN/HTTPS 與本機整合
- `005-validation-and-documentation.md`: 驗證案例、手動測試、README 與操作文件整理

## 建議執行順序

1. 先做 FastAPI + aiortc 的最小 signaling 與接收端
2. 再做 Vue 前端的攝影機預覽與 offer/answer 流程
3. 跑通單一路徑後，再補上 STUN、錯誤處理與重連
4. 最後整理處理模組、部署方式與文件

## 驗收標準

- 使用者可在瀏覽器中授權攝影機並啟動送流
- Python 後端可收到並處理視訊 frame
- 前後端可以正確建立與關閉 WebRTC 連線
- 專案文件足以讓其他人重現開發與測試流程

## 風險與注意事項

- 瀏覽器的 `getUserMedia()` 在非 localhost 環境通常要求 HTTPS
- 沒有 STUN/TURN 時，跨 NAT 或跨外網可能連線失敗
- 若每個 session 都長時間保留資源，需特別注意記憶體與連線清理
- 若後端做高成本模型推理，需再評估 frame rate、佇列與背壓控制

