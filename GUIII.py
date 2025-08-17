import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import yt_dlp
import time

# 預設下載路徑
download_path = os.path.expanduser("~/Downloads")
stop_thread = None  # 用來控制停止下載的線程

# 進度與狀態變數
progress_vars = {
    "percent": 0,
    "speed": "",
    "eta": "",
    "status": "待命中…"
}

# 獲取外部檔案（yt-dlp.exe 和 ffmpeg.exe）的路徑
def get_executable_path(executable_name):
    # 如果程式是運行 .exe 檔案，則從 PyInstaller 提供的臨時目錄中獲取
    if getattr(sys, 'frozen', False):
        exe_dir = sys._MEIPASS  # PyInstaller 提供的解壓目錄
    else:
        exe_dir = os.getcwd()  # 開發模式中使用當前工作目錄

    # 構建檔案的完整路徑
    executable_path = os.path.join(exe_dir, executable_name)
    if not os.path.isfile(executable_path):
        raise FileNotFoundError(f"未找到 {executable_name}，請確認它是否與程式放在同一資料夾中。")
    
    return executable_path

# 選擇儲存路徑
def select_folder():
    global download_path
    folder = filedialog.askdirectory(initialdir=download_path)
    if folder:
        download_path = folder
        path_label.config(text=f"儲存路徑: {download_path}")

# 根據選擇的畫質建立下載格式
def build_format(height_choice: str) -> str:
    if height_choice == "最佳可用":
        return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
    else:
        try:
            h = int(height_choice.replace("p", ""))
        except:
            h = 1080
        return f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h}][ext=mp4]"

# 更新下載進度
def on_progress(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded = d.get('downloaded_bytes', 0)
        pct = int(downloaded * 100 / total) if total else 0

        speed = d.get('speed') or 0
        if speed:
            if speed >= 1024**2:
                speed_str = f"{speed/1024**2:.2f} MB/s"
            else:
                speed_str = f"{speed/1024:.0f} kB/s"
        else:
            speed_str = "--"

        eta = d.get('eta')
        if eta is not None:
            if eta >= 3600:
                eta_str = time.strftime("%H:%M:%S", time.gmtime(eta))
            else:
                eta_str = time.strftime("%M:%S", time.gmtime(eta))
        else:
            eta_str = "--:--"

        progress_vars["percent"] = pct
        progress_vars["speed"] = speed_str
        progress_vars["eta"] = eta_str
        progress_vars["status"] = "下載中…"
    elif d['status'] == 'finished':
        progress_vars["status"] = "下載完成，正在處理檔案…"
        progress_vars["percent"] = 100

# 設置 UI 為忙碌狀態
def set_ui_busy(busy: bool):
    url_entry.config(state=tk.DISABLED if busy else tk.NORMAL)
    browse_btn.config(state=tk.DISABLED if busy else tk.NORMAL)
    download_btn.config(state=tk.DISABLED if busy else tk.NORMAL)
    quality_combo.config(state=tk.DISABLED if busy else tk.NORMAL)
    stop_btn.config(state=tk.NORMAL if busy else tk.DISABLED)

# 更新進度條與狀態顯示
def ui_pulse():
    progress_bar['value'] = progress_vars["percent"]
    status_label.config(
        text=f"{progress_vars['status']}  |  速度：{progress_vars['speed']}  |  剩餘：{progress_vars['eta']}"
    )
    root.after(200, ui_pulse)

# 記錄錯誤、警告、訊息到 UI
class TkLogger:
    def __init__(self, text_widget: tk.Text):
        self.text = text_widget

    def _append(self, level, msg):
        self.text.insert(tk.END, f"[{level}] {msg}\n")
        self.text.see(tk.END)

    def debug(self, msg):
        if isinstance(msg, str) and '\r' in msg:
            return
        self._append("DEBUG", str(msg))

    def warning(self, msg):
        self._append("警告", str(msg))

    def error(self, msg):
        self._append("錯誤", str(msg))

# 下載影片的主要邏輯
def do_download(url: str, height_choice: str):
    global stop_thread
    set_ui_busy(True)
    log_text.delete("1.0", tk.END)

    try:
        # 獲取 yt-dlp.exe 和 ffmpeg.exe 路徑
        yt_dlp_path = get_executable_path('yt-dlp.exe')
        ffmpeg_path = get_executable_path('ffmpeg.exe')

        # 構建檔案名，將畫質加入檔名
        file_name = '%(title)s_' + height_choice + '.%(ext)s'

        ydl_opts = {
            'format': build_format(height_choice),
            'outtmpl': os.path.join(download_path, file_name),
            'merge_output_format': 'mp4',
            'postprocessors': [
                {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}
            ],
            'postprocessor_args': ['-movflags', 'faststart'],
            'ffmpeg_location': ffmpeg_path,  # 設置 ffmpeg 路徑
            'progress_hooks': [on_progress],
            'logger': TkLogger(log_text),
            'quiet': True,
            'no_warnings': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            stop_thread = ydl
            ydl.download([url])

        progress_vars["status"] = "完成 ✅"
        messagebox.showinfo("完成", f"影片下載完成！已輸出 MP4 格式。")
    except Exception as e:
        progress_vars["status"] = "失敗 ❌"
        messagebox.showerror("錯誤", f"下載失敗：{e}")
    finally:
        stop_thread = None
        set_ui_busy(False)

# 停止下載
def stop_download():
    global stop_thread
    if stop_thread:
        stop_thread.cancel()  # 取消下載
        progress_vars["status"] = "已停止 ❌"
        messagebox.showwarning("已停止", "下載已停止。")
        set_ui_busy(False)

# 開始下載影片
def download_video():
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("錯誤", "請輸入 YouTube 影片網址")
        return

    progress_vars.update({"percent": 0, "speed": "", "eta": "", "status": "準備中…"})
    progress_bar['value'] = 0
    status_label.config(text="準備中…")

    t = threading.Thread(target=do_download, args=(url, quality_var.get()), daemon=True)
    t.start()

# ---------------- 設定圖標 ----------------
def resource_path(name: str) -> str:
    # PyInstaller 打包後的臨時資料夾
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, name)

def set_app_icon(root: tk.Tk):
    # 先試 .ico（Windows 標題列最穩定）
    ico_path = resource_path("app_icon.ico")
    try:
        if os.path.exists(ico_path):
            root.iconbitmap(ico_path)
            return
    except tk.TclError as e:
        print(f"[icon] iconbitmap 失敗：{e}")

    # 備援：用 .png（跨平台），需用 iconphoto
    png_path = resource_path("app_icon.png")
    if os.path.exists(png_path):
        try:
            img = tk.PhotoImage(file=png_path)
            root.iconphoto(True, img)
            root._icon_ref = img
            return
        except tk.TclError as e:
            print(f"[icon] iconphoto 失敗：{e}")

# ---------------- GUI ----------------
root = tk.Tk()
root.title("悠夢 YouTube 下載器 - ByFU-FU V1.9.2")
set_app_icon(root)

tk.Label(root, text="YouTube 影片網址:").pack(pady=(10, 3))
url_entry = tk.Entry(root, width=70)
url_entry.pack()

path_label = tk.Label(root, text=f"儲存路徑: {download_path}")
path_label.pack(pady=5)

quality_frame = tk.Frame(root)
quality_frame.pack(pady=3)
tk.Label(quality_frame, text="畫質：").pack(side=tk.LEFT, padx=(0, 5))

quality_options = ["最佳可用", "2160p", "1440p", "1080p", "720p", "480p", "360p"]
quality_var = tk.StringVar(value="1080p")
quality_combo = ttk.Combobox(quality_frame, textvariable=quality_var, values=quality_options, state="readonly", width=10)
quality_combo.pack(side=tk.LEFT)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=8)
browse_btn = tk.Button(btn_frame, text="選擇資料夾", command=select_folder)
browse_btn.pack(side=tk.LEFT, padx=5)
download_btn = tk.Button(btn_frame, text="下載", command=download_video)
download_btn.pack(side=tk.LEFT, padx=5)
stop_btn = tk.Button(btn_frame, text="停止", command=stop_download, state=tk.DISABLED)
stop_btn.pack(side=tk.LEFT, padx=5)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=560, mode="determinate", maximum=100)
progress_bar.pack(pady=(10, 2))
status_label = tk.Label(root, text="待命中…")
status_label.pack()

tk.Label(root, text="訊息 / 日誌：").pack(pady=(10, 3))
log_text = tk.Text(root, height=10, width=80)
log_text.pack(padx=10, pady=(0, 10))

root.after(200, ui_pulse)

root.mainloop()