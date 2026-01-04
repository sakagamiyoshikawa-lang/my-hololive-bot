import os
import requests
from google import genai
from datetime import datetime

# ==========================================
# 🌟 あなたの専用ID設定済み（固定版）
# ==========================================
AMAZON_ID = "191383501790a-22" 
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    # 1. Holodexからデータ取得（情報量アップのため20件取得）
    url = "https://holodex.net/api/v2/videos"
    params = {
        "org": "Hololive", 
        "limit": 20, 
        "sort": "published_at", 
        "order": "desc", 
        "type": "placeholder,stream,clip"
    }
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    response = requests.get(url, params=params, headers=headers)
    videos = response.json()

    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTMLヘッダー・最新のモダンデザイン
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} | ホロライブ最新情報AIナビ</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00c2ff; --sub: #ff66b2; --dark: #1a202c; --light: #f7fafc; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--light); margin: 0; color: var(--dark); line-height: 1.6; }}
            header {{ background: white; padding: 40px 20px; text-align: center; border-bottom: 6px solid var(--main); box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            header h1 {{ margin: 0; color: var(--main); font-size: 2.5rem; font-weight: 900; letter-spacing: -1px; }}
            .hero-text {{ color: #718096; font-size: 1rem; margin-top: 10px; font-weight: bold; }}
            .container {{ max-width: 1200px; margin: 40px auto; padding: 0 20px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 30px; }}
            .card {{ background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); transition: 0.3s; display: flex; flex-direction: column; height: 100%; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,0,0,0.12); }}
            .thumb-container {{ position: relative; width: 100%; aspect-ratio: 16/9; background: #eee; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .status-badge {{ position: absolute; top: 12px; left: 12px; padding: 4px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: bold; color: white; background: rgba(0,0,0,0.7); }}
            .live {{ background: #e53e3e !important; }}
            .info {{ padding: 20px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 0.9rem; font-weight: bold; color: #4a5568; margin-bottom: 8px; }}
            .cat-tag {{ display: inline-block; background: var(--sub); color: white; padding: 2px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; margin-bottom: 10px; align-self: flex-start; }}
            .video-title {{ font-weight: bold; font-size: 1.05rem; color: var(--dark); margin-bottom: 12px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 2.8em; }}
            .ai-desc {{ background: #f1f5f9; padding: 12px; border-radius: 12px; font-size: 0.85rem; color: #475569; margin-bottom: 20px; border-left: 4px solid var(--main); flex-grow: 1; }}
            .links {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: auto; }}
            .btn {{ text-decoration: none; padding: 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; text-align: center; transition: 0.2s; }}
            .btn-yt {{ background: var(--dark); color: white; grid-column: span 2; margin-bottom: 5px; }}
            .btn-amz {{ background: #ff9900; color: white; }}
            .btn-rak {{ background: #bf0000; color: white; }}
            .btn:hover {{ opacity: 0.8; filter: brightness(1.1); }}
            footer {{ text-align: center; padding: 60px 20px; background: white; margin-top: 60px; color: #a0aec0; border-top: 1px solid #edf2f7; }}
        </style>
    </head>
    <body>
        <header>
            <h1>🌟 {SITE_NAME}</h1>
            <p class="hero-text">AIが最新のホロライブ配信を分析・ナビゲート</p>
            <div style="font-size: 0.8rem; color: #cbd5e0; margin-top: 15px;">最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </header>
        <div class="container">
            <div class="grid">
    """

    for v in videos:
        title = v['title']
        v_id = v['id']
        ch_name = v['channel']['name']
        status = v.get('status', 'upcoming')
        
        status_label = "アーカイブ"
        status_class = ""
        if status == "live":
            status_label = "LIVE中"
            status_class = "live"
        elif status == "upcoming":
            status_label = "予約枠"

        # AI解析
        prompt = f"Categorize into [Original Song, Cover Song, Singing Stream, Other] and write a short attractive catchphrase in Japanese. Format: Category | Catchphrase. Title: {title}"
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            ai_output = res.text.strip().split('|')
            cat = ai_output[0].strip()
            desc = ai_output[1].strip() if len(ai_output) > 1 else "推しの最新情報をチェック！"
        except:
            cat, desc = "Other", "配信情報をチェックしよう！"

        # 収益化リンク
        search_query = requests.utils.quote(f"ホロライブ {ch_name}")
        amz_url = f"https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}"
        rak_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F"

        html_content += f"""
        <div class="card">
            <div class="thumb-container">
                <img src="https://img.youtube.com/vi/{v_id}/maxresdefault.jpg" class="thumb" onerror="this.src='https://img.youtube.com/vi/{v_id}/mqdefault.jpg'">
                <div class="status-badge {status_class}">{status_label}</div>
            </div>
            <div class="info">
                <div class="ch-name">👤 {ch_name}</div>
                <span class="cat-tag">{cat}</span>
                <div class="video-title">{title}</div>
                <div class="ai-desc">🤖 {desc}</div>
                <div class="links">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-yt">YouTubeで視聴</a>
                    <a href="{amz_url}" target="_blank" class="btn btn-amz">Amazonグッズ</a>
                    <a href="{rak_url}" target="_blank" class="btn btn-rak">楽天ブックス</a>
                </div>
            </div>
        </div>
        """

    html_content += f"""
            </div>
        </div>
        <footer>
            <p>© {datetime.now().year} {SITE_NAME} | AI分析ポータル</p>
            <p style="font-size: 0.7rem;">当サイトはファンプロジェクトです。紹介リンクを通じて収益が発生する場合があります。</p>
        </footer>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
