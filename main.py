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
    except:
        videos = []

    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTML構築開始（CSS/JSの{}は{{}}でエスケープ）
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} | 人気TOP100 AI解析ポータル</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00c2ff; --sub: #ff66b2; --stars: #ffb800; --dark: #1a202c; --light: #f4f7f9; --music: #7e57c2; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--light); margin: 0; padding: 0; color: var(--dark); }}
            
            /* バナー風ヘッダー */
            header {{ 
                background: linear-gradient(135deg, var(--main) 0%, var(--sub) 100%); 
                color: white; padding: 60px 20px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.15); 
            }}
            header h1 {{ margin: 0; font-size: 3.5rem; font-weight: 900; letter-spacing: -2px; text-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
            
            .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}

            /* ナビゲーション */
            .nav-box {{ background: white; padding: 20px; border-radius: 25px; margin: -40px auto 40px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.1); position: relative; z-index: 100; max-width: 800px; }}
            .nav-group {{ margin-bottom: 15px; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }}
            .nav-label {{ font-size: 0.75rem; font-weight: bold; color: #aaa; width: 100%; margin-bottom: 8px; text-transform: uppercase; }}

            .btn-nav {{ padding: 10px 25px; border: 2px solid #eee; background: white; cursor: pointer; border-radius: 50px; font-weight: bold; transition: 0.3s; color: #666; }}
            .btn-nav.active {{ border-color: var(--main); background: var(--main); color: white; box-shadow: 0 4px 15px rgba(0,194,255,0.3); }}
            .btn-stars.active {{ border-color: var(--stars); background: var(--stars); color: white; box-shadow: 0 4px 15px rgba(255,184,0,0.3); }}

            /* 表示制御 */
            .video-card {{ display: none; }}
            .video-card.show {{ display: flex; flex-direction: column; animation: fadeIn 0.5s ease forwards; }}
            @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}

            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 30px; }}
            .card {{ background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); transition: 0.3s; height: 100%; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,0,0,0.12); }}
            
            .thumb-container {{ position: relative; aspect-ratio: 16/9; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .view-badge {{ position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.8); color: white; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; }}
            .org-badge {{ position: absolute; top: 10px; left: 10px; padding: 4px 12px; border-radius: 8px; font-size: 0.7rem; font-weight: bold; color: white; }}

            .info {{ padding: 20px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 0.85rem; font-weight: bold; color: var(--main); margin-bottom: 10px; }}
            .video-title {{ font-weight: bold; font-size: 1rem; line-height: 1.5; margin-bottom: 15px; height: 3em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
            
            /* 楽曲情報ボックス */
            .music-card {{ background: #f3e5f5; border-radius: 12px; padding: 12px; margin-bottom: 15px; border-left: 5px solid var(--music); display: flex; align-items: center; gap: 10px; }}
            .music-text {{ font-size: 0.85rem; font-weight: bold; color: #4a148c; }}
            
            .ai-desc {{ font-size: 0.85rem; color: #555; background: #f8fafc; padding: 12px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #edf2f7; font-style: italic; }}
            
            .links {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: auto; }}
            .btn-link {{ text-decoration: none; padding: 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; text-align: center; transition: 0.2s; }}
            .btn-amz {{ background: #ff9900; color: white; }}
            .btn-rak {{ background: #bf0000; color: white; }}
        </style>
        <script>
            let curOrg = 'hololive';
            let curLang = 'ja';

            function update() {{
                document.querySelectorAll('.btn-org').forEach(b => b.classList.remove('active'));
                document.getElementById('o-' + curOrg).classList.add('active');
                document.querySelectorAll('.btn-lang').forEach(b => b.classList.remove('active'));
                document.getElementById('l-' + curLang).classList.add('active');

                document.querySelectorAll('.video-card').forEach(c => {{
                    const matchOrg = (curOrg === 'all' || c.dataset.org === curOrg);
                    const matchLang = (c.dataset.lang === curLang);
                    if (matchOrg && matchLang) c.classList.add('show');
                    else c.classList.remove('show');
                }});
            }}
            function setOrg(v) {{ curOrg = v; update(); }}
            function setLang(v) {{ curLang = v; update(); }}
        </script>
    </head>
    <body onload="update()">
        <header>
            <h1>🌟 {SITE_NAME}</h1>
            <p style="font-weight:bold; opacity:0.9;">AI楽曲解析 × 再生数TOP100ポータル</p>
        </header>

        <div class="container">
            <div class="nav-box">
                <div class="nav-group">
                    <span class="nav-label">Group Select</span>
                    <button id="o-all" class="btn-nav btn-org" onclick="setOrg('all')">ALL</button>
                    <button id="o-hololive" class="btn-nav btn-org active" onclick="setOrg('hololive')">HOLOLIVE</button>
                    <button id="o-holostars" class="btn-nav btn-org btn-stars" onclick="setOrg('holostars')">HOLOSTARS</button>
                </div>
                <div class="nav-group">
                    <span class="nav-label">Language</span>
                    <button id="l-ja" class="btn-nav btn-lang active" onclick="setLang('ja')">🇯🇵 JP</button>
                    <button id="l-en" class="btn-nav btn-lang" onclick="setLang('en')">🇺🇸 EN</button>
                    <button id="l-id" class="btn-nav btn-lang" onclick="setLang('id')">🇮🇩 ID</button>
                </div>
            </div>

            <div class="grid">
    """

    for v in videos:
        # エラー対策：データが欠けている場合はスキップ
        if not isinstance(v.get('channel'), dict): continue
        
        ch_name = v['channel'].get('name', 'Unknown')
        sub_org = v['channel'].get('sub_org', '')
        # 正確なグループ判定
        org_type = "holostars" if "stars" in sub_org.lower() or "stars" in ch_name.lower() else "hololive"
        lang = v.get('lang', 'ja')
        v_id, title = v['id'], v['title']
        views = v.get('view_count', 0)

        # AI解析：楽曲名と紹介文
        prompt = f"1.If music, [Song Name - Artist]. If not, [None]. 2.Attractive summary (15 chars). Format: Music | Summary. Title: {title}"
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            ai_data = res.text.strip().split('|')
            music_info = ai_data[0].strip()
            ai_desc = ai_data[1].strip() if len(ai_data) > 1 else "人気配信をチェック！"
        except:
            music_info, ai_desc = "None", "ホロライブ最新情報をナビゲート"

        music_html = f'<div class="music-card"><span class="music-text">🎵 {music_info}</span></div>' if "None" not in music_info else ""

        # 収益リンク
        search = requests.utils.quote(f"ホロライブ {ch_name}")
        amz_url = f"https://www.amazon.co.jp/s?k={search}&tag={AMAZON_ID}"
        rak_base = "ホロライブ" if org_type == "hololive" else "ホロスターズ"
        rak_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{rak_base}%20{requests.utils.quote(ch_name)}%2F"

        html_content += f"""
        <div class="video-card card" data-org="{org_type}" data-lang="{lang}">
            <div class="thumb-container">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" class="thumb">
                <div class="view-badge">👀 {views:,} views</div>
                <div class="org-badge" style="background: {'var(--main)' if org_type=='hololive' else 'var(--stars)'}">{org_type.upper()}</div>
            </div>
            <div class="info">
                <div class="ch-name">👤 {ch_name}</div>
                <div class="video-title">{title}</div>
                {music_html}
                <div class="ai-desc">🤖 {ai_desc}</div>
                <div class="links">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn-link" style="grid-column: span 2; background: var(--dark); color: white; margin-bottom: 5px;">動画を視聴する</a>
                    <a href="{amz_url}" target="_blank" class="btn-link btn-amz">Amazon</a>
                    <a href="{rak_url}" target="_blank" class="btn-link btn-rak">楽天市場</a>
                </div>
            </div>
        </div>"""

    html_content += """
            </div>
        </div>
        <footer style="text-align: center; padding: 60px; color: #aaa;">© 2026 ホロ活ナビ | AI Portal</footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    main()
