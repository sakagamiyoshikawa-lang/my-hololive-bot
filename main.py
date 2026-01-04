import os
import requests
from google import genai
from datetime import datetime

# ==========================================
# 設定エリア（ここを自分のIDに変えてください）
# ==========================================
AMAZON_ID = 191383501790a-22
RAKUTEN_ID = 4fb92fbd.48f820ce.4fb92fbe.82189b12
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    # 1. Holodexからデータ取得
    url = "https://holodex.net/api/v2/videos"
    params = {"org": "Hololive", "limit": 12, "sort": "published_at", "order": "desc", "type": "placeholder,stream"}
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    response = requests.get(url, params=params, headers=headers)
    videos = response.json()

    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTMLヘッダー・デザイン設定
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} - AIが届けるホロライブ最新情報</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {{ --main-blue: #00c2ff; --sub-pink: #ff66b2; --bg: #f0f4f8; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--bg); margin: 0; padding: 0; color: #333; }}
            header {{ background: white; padding: 20px; text-align: center; border-bottom: 4px solid var(--main-blue); box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ margin: 0; color: var(--main-blue); font-size: 1.8rem; }}
            .update-time {{ font-size: 0.8rem; color: #888; margin-top: 5px; }}
            .container {{ max-width: 1100px; margin: 30px auto; padding: 0 15px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; }}
            .card {{ background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 6px 20px rgba(0,0,0,0.06); transition: 0.3s; }}
            .card:hover {{ transform: translateY(-8px); }}
            .thumb {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; }}
            .info {{ padding: 15px; }}
            .cat-tag {{ display: inline-block; background: var(--sub-pink); color: white; padding: 3px 12px; border-radius: 50px; font-size: 0.75rem; font-weight: bold; margin-bottom: 10px; }}
            .video-title {{ font-weight: bold; font-size: 0.95rem; height: 2.8em; overflow: hidden; line-height: 1.4; margin-bottom: 15px; }}
            .links {{ display: flex; flex-wrap: wrap; gap: 8px; border-top: 1px solid #eee; padding-top: 15px; }}
            .btn {{ flex: 1; text-align: center; text-decoration: none; padding: 8px; border-radius: 8px; font-size: 0.75rem; font-weight: bold; }}
            .btn-yt {{ background: #ff0000; color: white; }}
            .btn-amz {{ background: #ff9900; color: white; }}
            .btn-rak {{ background: #bf0000; color: white; }}
            .ad-banner {{ background: white; margin-top: 40px; padding: 30px; border-radius: 15px; text-align: center; border: 3px dashed var(--main-blue); }}
        </style>
    </head>
    <body>
        <header>
            <h1>🌟 {SITE_NAME}</h1>
            <div class="update-time">AI判定更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </header>
        <div class="container">
            <div class="grid">
    """

    for v in videos:
        title = v['title']
        v_id = v['id']
        ch_name = v['channel']['name']
        thumb = f"https://img.youtube.com/vi/{v_id}/mqdefault.jpg"
        
        # AI判定
        prompt = f"Categorize into one: [Original Song, Cover Song, Singing Stream, Other]. Output only category name. Title: {title}"
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            cat = res.text.strip() if res.text else "判定中"
        except:
            cat = "Other"

        # 収益化リンクの作成（検索クエリを作成）
        search_query = requests.utils.quote(f"ホロライブ {ch_name}")
        amz_url = f"https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}"
        rak_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F"

        html_content += f"""
        <div class="card">
            <img src="{thumb}" class="thumb">
            <div class="info">
                <span class="cat-tag">{cat}</span>
                <div class="video-title">{title}</div>
                <div class="links">
                    <a href="https://
