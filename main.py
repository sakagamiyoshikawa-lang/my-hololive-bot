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
    # 1. データを取得（再生数上位100件）
    url = "https://holodex.net/api/v2/videos"
    params = {
        "org": "Hololive", 
        "limit": 100, 
        "sort": "view_count", 
        "order": "desc",
        "type": "stream,clip"
    }
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        videos = response.json()
        if not isinstance(videos, list): # リストでない場合は空にする
            videos = []
    except Exception as e:
        print(f"API Error: {e}")
        videos = []

    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTML構築開始（CSS/JSの{}は{{}}でエスケープ）
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} | 人気TOP100・AI楽曲解析ナビ</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00c2ff; --sub: #ff66b2; --stars: #ffb800; --dark: #1a202c; --light: #f4f7f9; --music: #7e57c2; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--light); margin: 0; padding: 0; color: var(--dark); }}
            
            /* 巨大バナー風ヘッダー */
            header {{ 
                background: linear-gradient(135deg, var(--main) 0%, var(--sub) 100%); 
                color: white; padding: 100px 20px; text-align: center; box-shadow: 0 4px 30px rgba(0,0,0,0.2); 
                position: relative;
            }}
            header h1 {{ margin: 0; font-size: 4rem; font-weight: 900; letter-spacing: -2px; text-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
            .hero-badge {{ background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 50px; font-size: 1rem; display: inline-block; margin-top: 15px; font-weight: bold; }}

            .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}

            /* ナビゲーション（タブ） */
            .nav-container {{ 
                background: white; padding: 30px; border-radius: 30px; margin: -50px auto 40px; 
                text-align: center; box-shadow: 0 15px 35px rgba(0,0,0,0.1); position: relative; z-index: 100; max-width: 1000px; 
            }}
            .nav-group {{ margin-bottom: 25px; display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; }}
            .nav-label {{ font-size: 0.8rem; font-weight: 900; color: #cbd5e0; width: 100%; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 2px; }}

            .btn-nav {{ 
                padding: 12px 30px; border: 2px solid #edf2f7; background: white; cursor: pointer; border-radius: 50px; 
                font-weight: 900; transition: 0.3s; color: #718096; font-size: 0.9rem;
            }}
            .btn-nav.active {{ border-color: var(--main); background: var(--main); color: white; box-shadow: 0 5px 20px rgba(0,194,255,0.4); }}
            .btn-stars.active {{ border-color: var(--stars); background: var(--stars); color: white; box-shadow: 0 5px 20px rgba(255,184,0,0.4); }}

            /* カード表示制御 */
            .video-card {{ display: none; }}
            .video-card.show {{ display: flex; flex-direction: column; animation: slideUp 0.4s ease forwards; }}
            @keyframes slideUp {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}

            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); gap: 30px; }}
            .card {{ background: white; border-radius: 25px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); transition: 0.3s; height: 100%; display: flex; flex-direction: column; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,0,0,0.15); }}
            
            .thumb-container {{ position: relative; aspect-ratio: 16/9; background: #000; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .view-tag {{ position: absolute; bottom: 12px; right: 12px; background: rgba(0,0,0,0.8); color: white; padding: 4px 10px; border-radius: 8px; font-size: 0.8rem; font-weight: bold; }}
            .group-tag {{ position: absolute; top: 12px; left: 12px; padding: 5px 15px; border-radius: 10px; font-size: 0.75rem; font-weight: 900; color: white; letter-spacing: 1px; }}

            .info {{ padding: 25px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 0.9rem; font-weight: 900; color: var(--main); margin-bottom: 10px; }}
            .video-title {{ font-weight: bold; font-size: 1.05rem; line-height: 1.5; margin-bottom: 15px; height: 3em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
            
            /* 🎵 楽曲情報セクション */
            .music-info {{ background: #f3e5f5; border-radius: 15px; padding: 15px; margin-bottom: 15px; border-left: 6px solid var(--music); }}
            .music-label {{ font-size: 0.7rem; color: var(--music); font-weight: 900; display: block; margin-bottom: 5px; }}
            .music-text {{ font-size: 0.9rem; font-weight: 900; color: #4a148c; }}
            
            .ai-summary {{ font-size: 0.85rem; color: #4a5568; background: #f8fafc; padding: 12px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #edf2f7; line-height: 1.4; }}
            
            .links {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: auto; }}
            .btn-action {{ text-decoration: none; padding: 12px; border-radius: 15px; font-size: 0.8rem; font-weight: 900; text-align: center; transition: 0.2s; }}
            .btn-yt {{ background: var(--dark); color: white; grid-column: span 2; margin-bottom: 5px; }}
            .btn-amz {{ background: #ff9900; color: white; }}
            .btn-rak {{ background: #bf0000; color: white; }}
        </style>
        <script>
            let filter = {{ org: 'hololive', lang: 'ja' }};

            function apply() {{
                document.querySelectorAll('.btn-org').forEach(b => b.classList.remove('active'));
                document.getElementById('o-' + filter.org).classList.add('active');
                document.querySelectorAll('.btn-lang').forEach(b => b.classList.remove('active'));
                document.getElementById('l-' + filter.lang).classList.add('active');

                document.querySelectorAll('.video-card').forEach(c => {{
                    const mOrg = (filter.org === 'all' || c.dataset.org === filter.org);
                    const mLang = (c.dataset.lang === filter.lang);
                    if (mOrg && mLang) c.classList.add('show');
                    else c.classList.remove('show');
                }});
            }}
            function setOrg(v) {{ filter.org = v; apply(); }}
            function setLang(v) {{ filter.lang = v; apply(); }}
        </script>
    </head>
    <body onload="apply()">
        <header>
            <h1>🌟 {SITE_NAME}</h1>
            <div class="hero-badge">再生数TOP100 × AI楽曲解析ポータル</div>
        </header>

        <div class="container">
            <div class="nav-container">
                <div class="nav-group">
                    <span class="nav-label">Select Group</span>
                    <button id="o-all" class="btn-nav btn-org" onclick="setOrg('all')">ALL GROUPS</button>
                    <button id="o-hololive" class="btn-nav btn-org active" onclick="setOrg('hololive')">HOLOLIVE</button>
                    <button id="o-holostars" class="btn-nav btn-org btn-stars" onclick="setOrg('holostars')">HOLOSTARS</button>
                </div>
                <div class="nav-group">
                    <span class="nav-label">Select Language</span>
                    <button id="l-ja" class="btn-nav btn-lang active" onclick="setLang('ja')">🇯🇵 日本語 (JP)</button>
                    <button id="l-en" class="btn-nav btn-lang" onclick="setLang('en')">🇺🇸 English (EN)</button>
                    <button id="l-id" class="btn-nav btn-lang" onclick="setLang('id')">🇮🇩 Indonesia (ID)</button>
                </div>
            </div>

            <div class="grid">
    """

    for v in videos:
        # --- 堅牢なエラーガード ---
        if not isinstance(v, dict): continue
        channel = v.get('channel')
        if not isinstance(channel, dict): continue
            
        name = channel.get('name', 'Unknown')
        sub = channel.get('sub_org', '')
        
        # グループ判定（正確に！）
        is_stars = any(x in (sub+name).lower() for x in ["stars", "vol.", "uproar"])
        org = "holostars" if is_stars else "hololive"
        lang = v.get('lang', 'ja')
        v_id, title = v.get('id'), v.get('title', 'No Title')
        views = v.get('view_count', 0)

        # AI楽曲解析
        prompt = f"Music? [Song - Artist] : [None]. And 15-char summary. Format: MusicInfo | Summary. Title: {title}"
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            parts = res.text.strip().split('|')
            m_val = parts[0].strip()
            ai_txt = parts[1].strip() if len(parts) > 1 else "人気動画をチェック！"
        except:
            m_val, ai_txt = "[None]", "ホロライブ最新情報を分析中"

        m_html = f'<div class="music-info"><span class="music-label">🎵 MUSIC INFO</span><div class="music-text">{m_val}</div></div>' if "[None]" not in m_val else ""

        # リンク生成
        query = requests.utils.quote(f"{'ホロライブ' if org=='hololive' else 'ホロスターズ'} {name}")
        amz = f"https://www.amazon.co.jp/s?k={query}&tag={AMAZON_ID}"
        rak = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{query}%2F"

        html_content += f"""
        <div class="video-card card" data-org="{org}" data-lang="{lang}">
            <div class="thumb-container">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" class="thumb" loading="lazy">
                <div class="view-tag">👀 {views:,} views</div>
                <div class="group-tag" style="background: {'var(--main)' if org=='hololive' else 'var(--stars)'}">{org.upper()}</div>
            </div>
            <div class="info">
                <div class="ch-name">👤 {name}</div>
                <div class="video-title">{title}</div>
                {m_html}
                <div class="ai-summary">🤖 {ai_txt}</div>
                <div class="links">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn-action btn-yt">YouTubeで視聴する</a>
                    <a href="{amz}" target="_blank" class="btn-action btn-amz">Amazon</a>
                    <a href="{rak}" target="_blank" class="btn-action btn-rak">楽天市場</a>
                </div>
            </div>
        </div>"""

    html_content += f"""
            </div>
        </div>
        <footer style="text-align: center; padding: 100px; color: #a0aec0; background: white; margin-top: 80px;">
            © {datetime.now().year} {SITE_NAME} | AI-Powered Fan Project
        </footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
