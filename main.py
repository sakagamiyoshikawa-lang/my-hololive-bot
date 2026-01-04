import os
import requests
from google import genai
from datetime import datetime

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    url = "https://holodex.net/api/v2/videos"
    params = {"org": "Hololive", "limit": 10, "sort": "published_at", "order": "desc", "type": "placeholder,stream"}
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    response = requests.get(url, params=params, headers=headers)
    videos = response.json()

    client = genai.Client(api_key=GEMINI_API_KEY)

    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>ホロライブ新着AI判定</title>
        <style>
            body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f0f8ff; }}
            .card {{ background: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .category {{ font-weight: bold; color: #ff66b2; }}
            .ad-space {{ background: #eee; padding: 10px; text-align: center; margin-top: 20px; border: 1px dashed #999; }}
        </style>
    </head>
    <body>
        <h1>🌟 ホロライブ新着AI判定 ({datetime.now().strftime('%Y-%m-%d %H:%M')})</h1>
        <p>AIが最新の動画を自動で判別しています。</p>
    """

    for v in videos:
        title = v['title']
        video_id = v['id']
        # 404エラー対策：モデル名を最もシンプルな形に変更
        prompt = f"Categorize this: [Original Song, Cover Song, Singing Stream, Other]. Output only 1 category. Title: {title}"
        
        try:
            # モデル名の指定を修正
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            category = res.text.strip() if res.text else "判定中"
            
            html_content += f"""
            <div class="card">
                <span class="category">【{category}】</span><br>
                {title}<br>
                <a href="https://www.youtube.com/watch?v={video_id}" target="_blank">▶︎動画を見る</a>
            </div>
            """
        except:
            continue

    # 収益化用のスペース（ここにAmazon等のリンクを貼る）
    html_content += """
        <div class="ad-space">
            <p>おすすめグッズ情報などはここに追加予定</p>
        </div>
    </body></html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
