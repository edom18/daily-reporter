import ollama

LLM_MODEL = "gemma3:27b"


def create_daily_report():
    print("Creating daily report...")

    with open("daily_log.txt", "r", encoding="utf-8") as f:
        log = f.read()

    system_prompt = """
あなたは日報作成者です。
日報の元になるテキストは、ユーザの画面を毎分キャプチャし、それを VLM がなにをしているかを解釈・解説したものが累積されたテキストデータです。
その前提に立って、ユーザが今日行ったことをまとめ、日報にしてください。
なお、VLM の性能、解釈などにより実際に行っていることと異なる可能性があります。前後の内容も含めて、可能な限り整合性を保って日報を作成してください。
また、VLM が内容を解釈するためのコンテキストとして以下が設定されています。
--- VLM への指示
あなたは画面のスクリーンショットを見て、ユーザがどんな作業をしているのかを監視する役割を担っています。
ユーザは毎分画面のスクリーンショットを撮ってそれをリクエストしてきます。
ユーザは Unity エンジニアであり、また MESON という会社の CTO です。
最近では IoT にも手を出しているため、それらを統合して様々な開発を行っています。
その前提で、今行っている作業、特にコーディングや調査タスクなどを把握してそれをレポートしてください。
画像から判断されたレポートは毎フレーム出力され、その日の最後にそれらをまとめて詳細な日報を作成するために利用されます。
レポートの内容は日本語で記述してください。
---
日報の内容は日本語で記述してください。
"""

    user_prompt = """
以下のテキストを日報にしてください。
{log}
"""

    try:
        response = ollama.chat(model=LLM_MODEL, messages=[
            {
                'role': 'system',
                'content': system_prompt,
            },
            {
                'role': 'user',
                'content': user_prompt,
            }
        ],
        keep_alive=0)

        daily_report = response['message']['content']

        with open("daily_report.txt", "w", encoding="utf-8") as f:
            f.write(daily_report)

        print("Daily report created successfully.")

    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    create_daily_report()