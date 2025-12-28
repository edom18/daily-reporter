import time
import schedule
from mss import mss
import ollama
from PIL import Image
import io
import json

# 設定
# VLM_MODEL = 'openbmb/minicpm-v4.5'
VLM_MODEL = 'qwen2.5vl:7b'
# VLM_MODEL = 'qwen2.5vl:32b'
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
レポートの内容は日本語で記述してください。
"""

    user_prompt = """
画像を分析して、ユーザがどのような作業をしているのかをレポートしてください。
"""

#         system_prompt = """
# You are a visual activity logger.

# Your task is to analyze a screenshot of a Windows PC screen
# and extract the user's work context in a concise, structured form.

# Rules:
# - Be factual and conservative. Do not guess beyond visible evidence.
# - Prefer short phrases over long explanations.
# - If information is unclear, mark it as "unknown".
# - Output ONLY valid JSON. No markdown, no comments.
# - All text must be in English.
# """

#         user_prompt = """
# This image is a screenshot captured from a Windows PC.

# Analyze the screen and output a JSON object with the following schema.

# Focus on:
# - Which application(s) are being used
# - What the user is likely doing at this moment
# - Important visible text (titles, errors, code, documents)
# - Whether this moment is meaningful enough to include in a daily report

# JSON schema:

# {
#   "timestamp": "<ISO8601 string or unknown>",
#   "active_app": "<main foreground application name>",
#   "other_visible_apps": ["<app name>", "..."],
#   "window_titles": ["<window title>", "..."],
#   "work_category": "<coding | document | meeting | browsing | design | terminal | communication | idle | other>",
#   "user_intent": "<short phrase describing what the user is trying to do>",
#   "actions": ["<visible action>", "..."],
#   "extracted_text": ["<important visible text>", "..."],
#   "tags": ["<keyword>", "..."],
#   "importance": "<low | medium | high>",
#   "confidence": <number between 0.0 and 1.0>
# }
# """

    # 2. Ollama で画像認識
    try:
        response = ollama.chat(model=VLM_MODEL, messages=[
            {
                'role': 'system',
                'content': system_prompt,
            },
            {
                'role': 'user',
                'content': user_prompt,
                'images': [img_bytes]
            }
        ])
        #, keep_alive=0)

        description = response['message']['content']
        timestamp = time.strftime('%H:%M')
        log_entry = f"[{timestamp}] {description}\n\n---------------\n\n"

        # 3. ログ保存
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        print("Log entry:", log_entry)
    except Exception as e:
        print("Error:", str(e))


# 1 分ごとに実行
schedule.every(1).minutes.do(job)
print("Start monitoring...")

while True:
    schedule.run_pending()
    time.sleep(1)