import time
import schedule
from mss import mss
import ollama
from PIL import Image
import io

# 設定
VLM_MODEL = 'openbmb/minicpm-v4.5'
# VLM_MODEL = 'qwen2.5vl:7b'
LOG_FILE = 'daily_log.txt'

def job():
    print("Capturing...")
    # 1. 高速スクリーンショット（mss を使用）
    with mss() as sct:
        monitor = sct.monitors[2]
        sct_img = sct.grab(monitor)
        # PIL Image に変換
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        # バイナリバッファに保存（ディスク IO を減らすため）
        # デバッグ用：画像をファイルに保存
        img.save("debug_screenshot.png")

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()

    system_prompt = """
あなたは画面のスクリーンショットを見て、ユーザがどんな作業をしているのかを監視する役割を担っています。
ユーザは毎分画面のスクリーンショットを撮ってそれをリクエストしてきます。
ユーザは Unity エンジニアであり、また MESON という会社の CTO です。
最近では IoT にも手を出しているため、それらを統合して様々な開発を行っています。
その前提で、今行っている作業、特にコーディングや調査タスクなどを把握してそれをレポートしてください。
画像から判断されたレポートは毎フレーム出力され、その日の最後にそれらをまとめて詳細な日報を作成するために利用されます。
レポートの内容は英語で記述してください。
"""

    # 2. Ollama で画像認識
    try:
        response = ollama.chat(model=VLM_MODEL, messages=[
            {
                'role': 'system',
                'content': system_prompt,
            },
            {
                'role': 'user',
                'content': '現在の作業状況です。スクリーンショットから内容を判断・判定してください。',
                'images': [img_bytes]
            }
        ])

        description = response['message']['content']
        timestamp = time.strftime('%H:%M')
        log_entry = f"[{timestamp}] {description}\n"

        print("Log entry:", log_entry)
    except Exception as e:
        print("Error:", str(e))

print("Start monitoring...")

job()