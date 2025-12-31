import time
import schedule
from mss import mss
from PIL import Image
import os
from datetime import datetime

# 設定
SCREENSHOTS_DIR = 'Screenshots'

def get_target_dir():
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    
    # 基本のディレクトリ名
    base_dir = os.path.join(SCREENSHOTS_DIR, date_str)
    
    if not os.path.exists(base_dir):
        return base_dir
    
    # 既存のディレクトリがある場合はインクリメントする
    i = 2
    while True:
        target_dir = f"{base_dir}-{i}"
        if not os.path.exists(target_dir):
            return target_dir
        i += 1

# 起動時に一度だけ保存先を決定する
target_dir = get_target_dir()
if not os.path.exists(target_dir):
    os.makedirs(target_dir)
print(f"Target directory: {target_dir}")

def job():
    print("Capturing...")
    # 1. 高速スクリーンショット（mss を使用）
    with mss() as sct:
        # モニターの取得（環境に合わせて調整が必要な場合があります）
        # sct.monitors[0] は全画面、[1], [2]... は各モニター
        monitor = sct.monitors[2] if len(sct.monitors) > 2 else sct.monitors[0]
        sct_img = sct.grab(monitor)
        # PIL Image に変換
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        # 保存先ディレクトリ
        now = datetime.now()
        time_str = now.strftime('%H-%M-%S')
        
        # ファイル名の作成と保存
        filename = f"{time_str}.png"
        filepath = os.path.join(target_dir, filename)
        img.save(filepath)
        
        print(f"Saved: {filepath}")

# 1 分ごとに実行
schedule.every(1).minutes.do(job)
print("Start monitoring (saving screenshots only)...")

# 初回実行
job()

while True:
    schedule.run_pending()
    time.sleep(1)
