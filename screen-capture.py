import time
import schedule
from mss import mss
from PIL import Image
import os
from datetime import datetime

# 設定
SCREENSHOTS_DIR = 'Screenshots'

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

        # 保存先ディレクトリの作成
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H-%M-%S')
        
        target_dir = os.path.join(SCREENSHOTS_DIR, date_str)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

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
