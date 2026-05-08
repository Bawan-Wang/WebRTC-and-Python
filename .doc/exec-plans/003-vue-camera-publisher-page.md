# Vue Camera Publisher Page 執行計畫

## 目的

建立 Vue 3 + Vite 前端頁面，讓使用者可在瀏覽器中授權攝影機、預覽畫面，並將視訊透過 WebRTC 傳送到 Python 後端。

## 範圍

### 本次範圍內

- 建立 Vue 3 + Vite 前端專案或前端目錄
- 建立攝影機預覽頁面
- 實作 `useWebRtcPublisher` composable
- 建立開始送流、停止送流與狀態顯示 UI
- 串接後端 offer/answer API

### 本次範圍外

- 視訊回放頁面
- 多裝置切換與進階裝置設定
- 音訊送流
- 完整設計系統與視覺優化

## 目標產出

- 一個可在瀏覽器啟動攝影機的頁面
- 一個可建立 WebRTC offer 並套用 answer 的前端流程
- 一個管理 media stream、peer connection 與連線狀態的 composable

## 執行項目

### 1. 前端結構建立

- 建立 Vue 3 + Vite 專案結構
- 建立頁面、元件與 API 模組目錄
- 規劃與後端 API 的呼叫方式

### 2. 攝影機存取與本地預覽

- 呼叫 `navigator.mediaDevices.getUserMedia({ video: true, audio: false })`
- 將 `MediaStream` 綁定到 `<video>` 元素進行本地預覽
- 處理權限拒絕與無可用裝置的錯誤提示

### 3. WebRTC Publisher Flow

- 建立 `RTCPeerConnection`
- 將本地 video track 加入 peer connection
- 建立 offer 並設定 local description
- 呼叫後端 signaling API 取得 answer
- 設定 remote description 完成協商

### 4. UI 狀態與生命週期

- 顯示待命、請求權限、連線中、已連線、失敗等狀態
- 在停止送流或頁面離開時停止 tracks 並關閉 peer connection
- 顯示後端或瀏覽器回傳的錯誤訊息

## 驗證方式

- 使用者可在頁面看到本地攝影機預覽
- 點擊開始送流後可成功建立 offer 並收到 answer
- 停止送流後攝影機與 peer connection 可被正確關閉
- 失敗情境下畫面可顯示可理解的錯誤

## 完成定義

- 前端可獨立演示完整 publisher 流程
- 前端不依賴手動操作 devtools 才能完成送流
- 後續只需補上整合設定即可與後端共同運作

## 風險與注意事項

- 若在非 localhost 環境開發，`getUserMedia()` 可能因缺少 HTTPS 被瀏覽器阻擋
- 若把所有 WebRTC 邏輯寫死在頁面元件中，後續維護會變差
- 不建議第一版就加入音訊與裝置切換，容易模糊最小交付範圍
