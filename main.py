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

USER_PROFILIE_FILE = 'Prompts/user_profile.md'
USER_TOOL_FILE = 'Prompts/user_tools.md'

with open(USER_PROFILIE_FILE, 'r', encoding='utf-8') as f:
    user_profile = f.read()

with open(USER_TOOL_FILE, 'r', encoding='utf-8') as f:
    user_tools = f.read()

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
# あなたの役割
あなたは画面のスクリーンショットを見て、ユーザがどんな作業をしているのかを監視する役割を担っています。
システムは毎分画面のスクリーンショットを撮影します。それを見て今の作業内容を把握してそれをレポートしてください。

# ユーザプロフィール
{user_profile}

# ユーザがよく使うツール
{user_tools}

# あなたのやるべきこと
あなたのやるべきことは、ユーザの画面キャプチャからタスクを判断し、なにをしているかをレポートすることです。

## 注目ポイント
ユーザの開いているアプリケーションを注意深く確認し、どんな作業をしているかを判断します。
ウィンドウは複数開いていることがあるため、特に前面に来ているアプリケーションに注目します。

その後、それに関連しそうなアプリケーションが開いていないかを確認し、もし関連しそうなものを開いている場合はそれを読み取ってください。

# レポートの扱い
画像から判断されたレポートはログエントリとして出力され、その日の最後にそれらをまとめて詳細な日報を作成するために利用されます。
レポートの内容は日本語で記述してください。
"""

    user_prompt = """
画像を分析してユーザがどのような作業をしているのかをレポートしてください。
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