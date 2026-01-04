import os
import requests
from google import genai
from datetime import datetime

# ==========================================
# 🌟 ID固定設定済み
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    # 1. Holodexからデータ取得（情報量確保のため30件に増量）
    url = "https://holodex.net/api/v2/videos"
    params = {
        "org": "Hololive", 
        "limit": 30, 
        "sort": "published_at", 
        "order": "desc", 
        "type": "placeholder,stream,clip"
    }
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    response = requests.get(url, params=params, headers=headers)
    videos = response.json()

    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTML構築（JavaScriptやCSSの { } は {{ }} と二重にしてエスケープしています）
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} | AIが届けるホロライブ最新情報</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00c2ff; --sub: #ff66b2; --dark: #1a202c; --light: #f7fafc; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--light); margin: 0; color: var(--dark); line-height: 1.6; }}
            
            /* 華やかなバナー風ヘッダー */
            header {{ 
                background: linear-gradient(135deg, var(--main) 0%, var(--sub) 100%); 
                color: white; 
                padding: 80px 20px; 
                text-align: center; 
                box-shadow: 0 4px 20px rgba(0,0,0,0.15); 
                position: relative;
                overflow: hidden;
            }}
            header::before {{
                content: ""; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                animation: rotate 20s linear infinite;
            }}
            @keyframes rotate {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}

            header h1 {{ margin: 0; font-size: 3.5rem; font-weight: 900; letter-spacing: -2px; text-shadow: 0 4px 10px rgba(0,0,0,0.3); position: relative; }}
            .hero-text {{ font-size: 1.2rem; margin-top: 15px; font-weight: bold; opacity: 0.95; position: relative; }}
            
            .container {{ max-width: 1200px; margin: 30px auto; padding: 0 20px; }}

            /* 言語フィルター（タブ） */
            .tabs {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 40px; flex-wrap: wrap; }}
            .tab-btn {{ 
                padding: 12px 25px; border: none; background: white; cursor: pointer; border-radius: 50px; 
                font-weight: bold; transition: 0.3s; box-shadow: 0 4px 10px rgba(0,0,0,0.05); color: #666;
            }}
            .tab-btn.active {{ background: var(--main); color: white; box-shadow: 0 4px 15px rgba(0,194,255,0.4); }}

            .video-list {{ display: none; }}
            .video-list.active {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 30px; }}

            /* カードデザイン */
            .card {{ background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); transition: 0.3s; display: flex; flex-direction: column; height: 100%; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,0,0,0.12); }}
            .thumb-container {{ position: relative; width: 100%; aspect-ratio: 16/9; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .status-badge {{ position: absolute; top: 12px; left: 12px; padding: 4px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: bold; color: white; background: rgba(0,0,0,0.7); }}
            .live {{ background: #e53e3e !important; }}
            
            .info {{ padding: 20px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 0.9rem; font-weight: bold; color: #4a5568; margin-bottom: 8px; }}
            .cat-tag {{ display: inline-block; background: var(--sub); color: white; padding: 2px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; margin-bottom: 10px; align-self: flex-start; }}
            .video-title {{ font-weight: bold; font-size: 1.05rem; color: var(--dark); margin-bottom: 12px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 2.8em; }}
            .ai-desc {{ background: #f1f5f9; padding: 15px; border-radius: 12px; font-size: 0.9rem; color: #475569; margin-bottom: 20px; border-left: 4px solid var(--main); flex-grow: 1; font-weight: bold; }}
            
            .links {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: auto; }}
            .btn {{ text-decoration: none; padding: 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; text-align: center; transition: 0.2s; }}
            .btn-yt {{ background: var(--dark); color: white; grid-column: span 2; margin-bottom: 5px; }}
            .btn-amz {{ background: #ff9900; color: white; }}
            .btn-rak {{ background: #bf0000; color: white; }}
            .btn:hover {{ opacity: 0.8; filter: brightness(1.1); }}
            
            footer {{ text-align: center; padding: 60px 20px; background: white; margin-top: 60px; color: #a0aec0; border-top: 1px solid #edf2f7; }}
        </style>
        <script>
            function openTab(lang) {{
                document.querySelectorAll('.video-list').forEach(list => list.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById(lang).classList.add('active');
                document.getElementById('btn-' + lang).classList.add('active');
            }}
        </script>
    </head>
    <body onload="openTab('ja')">
        <header>
            <h1>🌟 {SITE_NAME}</h1>
            <p class="hero-text">AI解析 | 推し活を加速させる最新ポータル</p>
            <div style="font-size: 0.8rem; color: rgba(255,255,255,0.7); margin-top: 20px;">UPDATE: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </header>
        <div class="container">
            <div class="tabs">
                <button class="tab-btn" id="btn-ja" onclick="openTab('ja')">🇯🇵 日本語</button>
                <button class="tab-btn" id="btn-en" onclick="openTab('en')">🇺🇸 English</button>
                <button class="tab-btn" id="btn-id" onclick="openTab('id')">🇮🇩 Indonesia</button>
            </div>

            <div id="ja" class="video-list active">
    """

    # --- データ仕分けとカード生成関数 ---
    def create_card(v):
        title, v_id, ch_name = v['title'], v['id'], v['channel']['name']
        status = v.get('status', 'upcoming')
        status_label, status_class = ("LIVE中", "live") if status == "live" else ("予約枠", "") if status == "upcoming" else ("アーカイブ", "")
        
        prompt = f"Categorize into [Original Song, Cover Song, Singing Stream, Other] and write a short attractive catchphrase in Japanese. Format: Category | Catchphrase. Title: {title}"
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            ai = res.text.strip().split('|')
            cat, desc = (ai[0].strip(), ai[1].strip()) if len(ai) > 1 else ("Other", "最新情報をチェック！")
        except:
            cat, desc = "Other", "ホロライブ最新配信をナビゲート"

        search = requests.utils.quote(f"ホロライブ {ch_name}")
        amz_url = f"https://www.amazon.co.jp/s?k={search}&tag={AMAZON_ID}"
        # 楽天市場の一般検索に変更
        rak_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2Fホロライブ%20{search}%2F"

        return f"""
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
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-yt">視聴する</a>
                    <a href="{amz_url}" target="_blank" class="btn btn-amz">Amazonグッズ</a>
                    <a href="{rak_url}" target="_blank" class="btn btn-rak">楽天市場で探す</a>
                </div>
            </div>
        </div>"""

    # 言語ごとに表示
    for v in [x for x in videos if x.get('lang', 'ja') == 'ja']: html_content += create_card(v)
    html_content += """</div><div id="en" class="video-list">"""
    for v in [x for x in videos if x.get('lang') == 'en']: html_content += create_card(v)
    html_content += """</div><div id="id" class="video-list">"""
    for v in [x for x in videos if x.get('lang') == 'id']: html_content += create_card(v)

    html_content += f"""
            </div>
        </div>
        <footer>
            <p>© {datetime.now().year} {SITE_NAME} | AI分析ポータル</p>
        </footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    main()
