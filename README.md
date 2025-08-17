

悠夢 YouTube 下載器 - ByFU-FU V1.9.2 🎥

送給悠夢

一款基於 Python + Tkinter 的簡易圖形介面 YouTube 影片下載器。
內建整合 yt-dlp 與 FFmpeg，支援多種畫質選擇、進度顯示，以及下載過程的即時日誌。


---

✨ 功能特色

🎬 多畫質下載：支援 2160p (4K)、1440p、1080p、720p、480p、360p 等，並自動選擇最佳格式。

⚡ 即時進度條：顯示下載進度、速度、剩餘時間。

📝 即時日誌：將下載與錯誤訊息直接顯示於 GUI 介面。

📂 路徑選擇：可自由選擇下載儲存資料夾。

🛑 下載中止：可在需要時手動停止下載。

🖼 自訂圖示：內建 app_icon.ico 與 app_icon.png。



---

🖼 軟體截圖 (範例)

<img width="587" height="418" alt="image" src="https://github.com/user-attachments/assets/aadcbad6-c437-41be-b2e8-bf34c777b5aa" />


---

📦 安裝與打包

此專案使用 cx_Freeze 進行打包，並整合外部程式：

yt-dlp.exe

ffmpeg.exe


主要依賴：

yt-dlp

tkinter (Python 內建)

cx_Freeze




-

📂 專案結構

project_directory/
│
├── GUIII.py          # 主程式
├── setup.py          # cx_Freeze 打包設定
├── yt-dlp.exe        # 外部下載器
├── ffmpeg.exe        # 外部影片處理工具
├── app_icon.ico      # 應用程式圖示 (Windows)
├── app_icon.png      # 應用程式圖示 (跨平台備援)
└── requirements.txt  # 依賴套件清單


---

🚀 未來規劃

[ ] 新增批次下載清單功能

[ ] 增加 MP3 音樂下載模式

[ ] 優化 UI，支援深色模式

[ ] 加入更多影片平台支援（Twitch, Bilibili, 等）



---

❤️ 致謝

yt-dlp：強大的 YouTube 下載工具

FFmpeg：專業影音轉檔工具

cx_Freeze：Python 應用程式打包工具



---

👉 如果你喜歡這個專案，記得幫我點個 ⭐ Star！




