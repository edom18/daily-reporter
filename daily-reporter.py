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
TASK_FILE = 'Prompts/VLM/task.md'
ROLE_FILE = 'Prompts/VLM/role.md'
DAILY_REPORT_ROLE_FILE = 'Prompts/LLM/role.md'

def get_vlm_analysis(image_path, task, role):
    """VLM を使用して画像を分析する"""
    print(f"Analyzing {image_path}...")
    
    try:
        with open(image_path, 'rb') as f:
            img_bytes = f.read()

        system_prompt = f"""
{role}

{task}
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
        with open(TASK_FILE, 'r', encoding='utf-8') as f:
            task = f.read()
        with open(ROLE_FILE, 'r', encoding='utf-8') as f:
            role = f.read()
        with open(DAILY_REPORT_ROLE_FILE, 'r', encoding='utf-8') as f:
            daily_report_role = f.read()
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
        
        description = get_vlm_analysis(filepath, task, role)
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
    system_prompt = f"""
{daily_report_role}

{user_profile}

{user_tools}
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
        
        # インクリメントされたディレクトリを含め、最新のものを探す
        if not args.date:
            candidates = sorted([d for d in os.listdir(SCREENSHOTS_DIR) if d.startswith(target_date)])
            if candidates:
                target_date = candidates[-1]
                print(f"Latest directory found: {target_date}")
        
        create_daily_report(target_date)
    elif args.command == "clear":
        clear_screenshots(args.date)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
