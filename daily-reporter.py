import ollama
import os
import shutil
import argparse
from datetime import datetime
from PIL import Image
import io

# 設定
LLM_MODEL = "gemma3:27b"
VLM_MODEL = "qwen3-vl:8b"
SCREENSHOTS_DIR = 'Screenshots'
LOG_DIR = 'Logs'
REPORT_DIR = 'Reports'
USER_PROFILIE_FILE = 'Prompts/user_profile.md'
USER_TOOL_FILE = 'Prompts/user_tools.md'

def get_vlm_analysis(image_path, user_profile, user_tools):
    """VLM を使用して画像を分析する"""
    print(f"Analyzing {image_path}...")
    
    try:
        with open(image_path, 'rb') as f:
            img_bytes = f.read()

        system_prompt = f"""
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

        user_prompt = "画像を分析してユーザがどのような作業をしているのかをレポートしてください。"

        response = ollama.chat(model=VLM_MODEL, messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt, 'images': [img_bytes]}
        ])
        return response['message']['content']
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def create_daily_report(target_date):
    print(f"Creating daily report for {target_date}...")

    # プロファイルとツールの読み込み
    try:
        with open(USER_PROFILIE_FILE, 'r', encoding='utf-8') as f:
            user_profile = f.read()
        with open(USER_TOOL_FILE, 'r', encoding='utf-8') as f:
            user_tools = f.read()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # スクリーンショットの処理
    target_dir = os.path.join(SCREENSHOTS_DIR, target_date)
    if not os.path.exists(target_dir):
        print(f"No screenshots found for {target_date} in {target_dir}")
        return

    screenshots = sorted([f for f in os.listdir(target_dir) if f.endswith('.png')])
    if not screenshots:
        print(f"No PNG screenshots found in {target_dir}")
        return
    
    log_entries = []
    for filename in screenshots:
        timestamp = filename.replace('.png', '').replace('-', ':')
        filepath = os.path.join(target_dir, filename)
        
        description = get_vlm_analysis(filepath, user_profile, user_tools)
        log_entry = f"[{timestamp}] {description}"
        log_entries.append(log_entry)
        print(log_entry)

    full_log = "\n\n---------------\n\n".join(log_entries)

    # ログをデバッグ用に書き出しておく
    log_filename = os.path.join(LOG_DIR, f"daily_log_{target_date}.txt")
    with open(log_filename, "w", encoding="utf-8") as f:
        f.write(full_log)
    print(f"Log saved to {log_filename}")

    # 日報の作成
    print("Generating summary...")
    system_prompt = """
あなたは日報作成者です。
日報の元になるテキストは、ユーザの画面を毎分キャプチャし、それを VLM がなにをしているかを解釈・解説したものが累積されたテキストデータです。
その前提に立って、ユーザが今日行ったことをまとめ、日報にしてください。
なお、VLM の性能、解釈などにより実際に行っていることと異なる可能性があります。前後の内容も含めて、可能な限り整合性を保って日報を作成してください。
日報の内容は日本語で記述してください。
"""

    user_prompt = f"以下のテキストを日報にしてください。\n\n{full_log}"

    try:
        response = ollama.chat(model=LLM_MODEL, messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ], keep_alive=0)

        daily_report = response['message']['content']

        report_filename = os.path.join(REPORT_DIR, f"daily_report_{target_date}.txt")
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(daily_report)

        print(f"Daily report created successfully: {report_filename}")

    except Exception as e:
        print("Error during report generation:", str(e))

def clear_screenshots(target_date):
    target_dir = os.path.join(SCREENSHOTS_DIR, target_date)
    if os.path.exists(target_dir):
        print(f"Deleting screenshots directory: {target_dir}...")
        shutil.rmtree(target_dir)
        print("Directory deleted successfully.")
    else:
        print(f"Directory not found: {target_dir}")

def main():
    parser = argparse.ArgumentParser(description="Daily Reporter CLI")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # report コマンド
    report_parser = subparsers.add_parser("report", help="Generate a daily report for a specific date")
    report_parser.add_argument("date", nargs="?", help="Target date (YYYY-MM-DD), defaults to today")

    # clear コマンド
    clear_parser = subparsers.add_parser("clear", help="Clear screenshots for a specific date")
    clear_parser.add_argument("date", help="Target date (YYYY-MM-DD)")

    args = parser.parse_args()

    if args.command == "report":
        target_date = args.date if args.date else datetime.now().strftime('%Y-%m-%d')
        create_daily_report(target_date)
    elif args.command == "clear":
        clear_screenshots(args.date)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
