import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import yt_dlp
import time
import re
import subprocess

# 獲取 yt-dlp 版本
def get_version(executable_name):
    try:
        result = subprocess.run([executable_name, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return result.stdout.strip()  # 返回版本資訊
        else:
            return f"無法獲取 {executable_name} 版本"
    except FileNotFoundError:
        return f"{executable_name} 沒有找到"

# 顯示版本資訊
def show_versions(event=None):
    yt_dlp_version = get_version('yt-dlp.exe')
    version_info = f"yt-dlp 版本: {yt_dlp_version}"
    version_label.config(text=version_info)

# 預設下載路徑
download_path = os.path.expanduser("~/Downloads")
# 進度與狀態變數
progress_vars = {
    "percent": 0,
    "speed": "",
    "eta": "",
    "status": "待命中…"
}

# 下載過的檔案列表
downloaded_files = []

# 獲取外部檔案（yt-dlp.exe）的路徑
def get_executable_path(executable_name):
    if getattr(sys, 'frozen', False):
        exe_dir = sys._MEIPASS  # PyInstaller 提供的解壓目錄
    else:
        exe_dir = os.getcwd()  # 開發模式中使用當前工作目錄

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

        # 將下載的檔案加入檔案清單
        downloaded_files.append(d['filename'])
        update_download_list()

# 設置 UI 為忙碌狀態
def set_ui_busy(busy: bool):
    url_entry.config(state=tk.DISABLED if busy else tk.NORMAL)
    browse_btn.config(state=tk.DISABLED if busy else tk.NORMAL)
    download_btn.config(state=tk.DISABLED if busy else tk.NORMAL)
    quality_combo.config(state=tk.DISABLED if busy else tk.NORMAL)

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

# 顯示影片名稱
def display_video_info(info):
    video_title = info.get("title", "未知影片")
    title_label.config(text=f"影片名稱: {video_title}")

# 下載影片的主要邏輯
def do_download(url: str, height_choice: str, audio_only: bool):
    set_ui_busy(True)
    log_text.delete("1.0", tk.END)

    try:
        # 獲取 yt-dlp.exe 路徑
        yt_dlp_path = get_executable_path('yt-dlp.exe')

        # 獲取影片元數據
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)  # 只提取資訊，不下載
            display_video_info(info)  # 顯示影片名稱

        # 根據選擇的畫質建立下載格式
        format_choice = build_format(height_choice)

        # 如果選擇只下載音訊
        if audio_only:
            format_choice = "bestaudio[ext=m4a]/best"
            file_name = '%(title)s_' + "audio" + '.%(ext)s'
            ydl_opts = {
                'format': format_choice,
                'outtmpl': os.path.join(download_path, file_name),
                'progress_hooks': [on_progress],
                'logger': TkLogger(log_text),
                'quiet': True,
                'no_warnings': False,
            }
        else:
            file_name = '%(title)s_' + height_choice + '.%(ext)s'
            ydl_opts = {
                'format': format_choice,
                'outtmpl': os.path.join(download_path, file_name),
                'merge_output_format': 'mp4',
                'postprocessors': [
                    {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}
                ],
                'postprocessor_args': ['-movflags', 'faststart'],
                'progress_hooks': [on_progress],
                'logger': TkLogger(log_text),
                'quiet': True,
                'no_warnings': False,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        progress_vars["status"] = "完成 ✅"
        messagebox.showinfo("完成", f"下載完成！已輸出音訊檔案。" if audio_only else "影片下載完成！已輸出 MP4 格式。")
    except Exception as e:
        progress_vars["status"] = "失敗 ❌"
        messagebox.showerror("錯誤", f"下載失敗：{e}")
    finally:
        set_ui_busy(False)

# 更新下載檔案清單
def update_download_list():
    # 清空檔案列表並顯示所有下載的檔案
    download_listbox.delete(0, tk.END)
    for file in downloaded_files:
        download_listbox.insert(tk.END, file)

# 開始下載影片
def download_video():
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("錯誤", "請輸入 YouTube 影片網址")
        return

    progress_vars.update({"percent": 0, "speed": "", "eta": "", "status": "準備中…"})
    progress_bar['value'] = 0
    status_label.config(text="準備中…")

    t = threading.Thread(target=do_download, args=(url, quality_var.get(), audio_only_var.get()), daemon=True)
    t.start()

# ---------------- 設定圖標 ----------------
def resource_path(name: str) -> str:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, name)

def set_app_icon(root: tk.Tk):
    ico_path = resource_path("app_icon.ico")
    try:
        if os.path.exists(ico_path):
            root.iconbitmap(ico_path)
            return
    except tk.TclError as e:
        print(f"[icon] iconbitmap 失敗：{e}")

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
root.title("Yume YouTube Download - ByFU-FU V2.0.2")
set_app_icon(root)

# 建立 Notebook（選項卡）
notebook = ttk.Notebook(root)
notebook.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# 下載頁面
download_tab = ttk.Frame(notebook)
notebook.add(download_tab, text="下載")

tk.Label(download_tab, text="YouTube 影片網址:").pack(pady=(10, 3))
url_entry = tk.Entry(download_tab, width=70)
url_entry.pack()

path_label = tk.Label(download_tab, text=f"儲存路徑: {download_path}")
path_label.pack(pady=5)

quality_frame = tk.Frame(download_tab)
quality_frame.pack(pady=3)
tk.Label(quality_frame, text="畫質：").pack(side=tk.LEFT, padx=(0, 5))

quality_options = ["最佳可用", "2160p", "1440p", "1080p", "720p", "480p", "360p"]
quality_var = tk.StringVar(value="1080p")
quality_combo = ttk.Combobox(quality_frame, textvariable=quality_var, values=quality_options, state="readonly", width=10)
quality_combo.pack(side=tk.LEFT)

audio_only_var = tk.BooleanVar()
audio_only_check = tk.Checkbutton(download_tab, text="只下載音訊", variable=audio_only_var)
audio_only_check.pack(pady=5)

btn_frame = tk.Frame(download_tab)
btn_frame.pack(pady=8)
browse_btn = tk.Button(btn_frame, text="選擇資料夾", command=select_folder)
browse_btn.pack(side=tk.LEFT, padx=5)
download_btn = tk.Button(btn_frame, text="下載", command=download_video)
download_btn.pack(side=tk.LEFT, padx=5)

# 顯示影片名稱
title_label = tk.Label(download_tab, text="影片名稱: ")
title_label.pack(pady=10)

progress_bar = ttk.Progressbar(download_tab, orient="horizontal", length=560, mode="determinate", maximum=100)
progress_bar.pack(pady=(10, 2))
status_label = tk.Label(download_tab, text="待命中…")
status_label.pack()

tk.Label(download_tab, text="訊息 / 日誌：").pack(pady=(10, 3))
log_text = tk.Text(download_tab, height=10, width=80)
log_text.pack(padx=10, pady=(0, 10))

# 版本頁面
version_tab = ttk.Frame(notebook)
notebook.add(version_tab, text="查看版本")

# 版本資訊標籤，進入時自動顯示版本
version_label = tk.Label(version_tab, text="版本資訊載入中...")
version_label.pack(pady=50)

# 下載內容頁面
downloaded_tab = ttk.Frame(notebook)
notebook.add(downloaded_tab, text="查看下載")

# 顯示已下載檔案的列表
download_listbox = tk.Listbox(downloaded_tab, width=80, height=15)
download_listbox.pack(pady=10)

# 在顯示版本頁面時自動呼叫 show_versions
notebook.select(download_tab)  # 預設選擇下載頁面
show_versions()  # 立即顯示版本

root.after(200, ui_pulse)

root.mainloop()
