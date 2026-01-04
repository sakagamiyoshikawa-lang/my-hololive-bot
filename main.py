import os
import requests
from google import genai
from datetime import datetime

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    # 1. Holodexからデータ取得
    url = "https://holodex.net/api/v2/videos"
    params = {"org": "Hololive", "limit": 10, "sort": "published_at", "order": "desc", "type": "placeholder,stream"}
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    response = requests.get(url, params=params, headers=headers)
    videos = response.json()

    # 2. Gemini設定（モデル名をより確実な表記に変更）
    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTMLの準備
    html_content = f"""
    <html>
    <head><meta charset="utf-8"><title>ホロライブ新着判定</title></head>
    <body style="font-family: sans-serif; padding: 20px;">
        <h1>🕒 ホロライブ新着AI判定 ({datetime.now().strftime('%Y-%m-%d %H:%M')})</h1>
        <hr>
    """

    for v in videos:
        title = v['title']
        video_id = v['id']
        prompt = f"Categorize this YouTube title into one: [Original Song, Cover Song, Singing Stream, Other]. Output ONLY the category name.\nTitle: {title}"
        
        try:
            # 判定（モデル指定を修正）
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            category = res.text.strip() if res.text else "判定中"
            
            # HTMLに行を追加
            html_content += f"""
            <div style="margin-bottom: 20px;">
                <p><strong>判定: {category}</strong></p>
                <p>{title}</p>
                <a href="https://www.youtube.com/watch?v={video_id}" target="_blank">動画を見る</a>
            </div>
            """
        except Exception as e:
            print(f"Error: {e}")

    html_content += "</body></html>"

    # ファイルに保存
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ index.html を作成しました")

if __name__ == "__main__":
    main()
