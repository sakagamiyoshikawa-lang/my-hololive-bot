import os
import requests
from google import genai
from datetime import datetime

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    url = "https://holodex.net/api/v2/videos"
    params = {"org": "Hololive", "limit": 12, "sort": "published_at", "order": "desc", "type": "placeholder,stream"}
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    response = requests.get(url, params=params, headers=headers)
    videos = response.json()

    client = genai.Client(api_key=GEMINI_API_KEY)

    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>HoloAI Tracker - 最新ホロライブ判定</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {{ --primary: #33a6ff; --accent: #ff66b2; --bg: #f8fafc; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--bg); margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1 {{ text-align: center; color: var(--primary); font-size: 2rem; margin-bottom: 30px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
            .card {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); transition: 0.3s; }}
            .card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }}
            .thumb {{ width: 100%; height: 180px; object-fit: cover; }}
            .content {{ padding: 15px; }}
            .category {{ display: inline-block; background: var(--accent); color: white; padding: 2px 10px; border-radius: 20px; font-size: 0.8rem; margin-bottom: 10px; }}
            .title {{ font-weight: bold; font-size: 0.95rem; line-height: 1.4; height: 2.8em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
            .footer {{ margin-top: 15px; display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: #666; }}
            .btn {{ text-decoration: none; color: white; background: var(--primary); padding: 5px 15px; border-radius: 5px; }}
            .ad-section {{ margin-top: 50px; padding: 30px; background: #fff; border-radius: 12px; text-align: center; border: 2px dashed var(--primary); }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌟 HoloAI Tracker <span style="font-size: 1rem; color: #999;">({datetime.now().strftime('%Y-%m-%d %H:%M')})</span></h1>
            <div class="grid">
    """

    for v in videos:
        title = v['title']
        video_id = v['id']
        channel_name = v['channel']['name']
        
        prompt = f"Categorize this: [Original Song, Cover Song, Singing Stream, Other]. Output only 1 category. Title: {title}"
        
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            category = res.text.strip() if res.text else "判定中"
            
            # YouTubeサムネイル画像URL
            thumb_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
            
            html_content += f"""
            <div class="card">
                <img src="{thumb_url}" class="thumb">
                <div class="content">
                    <span class="category">{category}</span>
                    <div class="title">{title}</div>
                    <div class="footer">
                        <span>👤 {channel_name}</span>
                        <a href="https://www.youtube.com/watch?v={video_id}" target="_blank" class="btn">視聴する</a>
                    </div>
                </div>
            </div>
            """
        except:
            continue

    html_content += """
            </div>
            <div class="ad-section">
                <h3>📢 今週の注目アイテム</h3>
                <p>（ここにAmazonアソシエイトなどの広告を掲載できます）</p>
            </div>
        </div>
    </body></html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
