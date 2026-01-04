import os
import requests
from google import genai
from datetime import datetime
import urllib.parse

# ==========================================
# 🌟 ID固定設定済み
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_videos():
    """APIの制限を考慮し、再生数上位100件を確実に取得する"""
    url = "https://holodex.net/api/v2/videos"
    combined = []
    for offset in [0, 50]:
        params = {
            "org": "Hololive", "limit": 50, "offset": offset,
            "sort": "view_count", "order": "desc", "type": "stream,clip"
        }
        try:
            res = requests.get(url, params=params, headers={"X-APIKEY": HOLODEX_API_KEY}, timeout=10)
            data = res.json()
            if isinstance(data, list):
                # 辞書型であり、かつchannel情報が正常なものだけを抽出（ここがエラー対策）
                combined.extend([v for v in data if isinstance(v, dict) and isinstance(v.get('channel'), dict)])
        except:
            continue
    return combined

def main():
    videos = fetch_videos()
    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTMLヘッダー（CSS/JSの波括弧は {{ }} でエスケープ）
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} | AI分析ポータル</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00c2ff; --sub: #ff66b2; --stars: #ffb800; --dark: #1a202c; --light: #f4f7f9; --music: #7e57c2; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--light); margin: 0; color: var(--dark); line-height: 1.6; }}
            header {{ background: linear-gradient(135deg, var(--main) 0%, var(--sub) 100%); color: white; padding: 60px 20px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.15); }}
            header h1 {{ margin: 0; font-size: 3rem; font-weight: 900; letter-spacing: -2px; text-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
            .hero-text {{ font-size: 1.1rem; margin-top: 10px; font-weight: bold; opacity: 0.95; }}
            .container {{ max-width: 1400px; margin: 30px auto; padding: 0 20px; }}
            .tabs {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 30px; flex-wrap: wrap; }}
            .tab-btn {{ padding: 12px 25px; border: 2px solid #e2e8f0; background: white; cursor: pointer; border-radius: 50px; font-weight: bold; transition: 0.3s; color: #64748b; }}
            .tab-btn.active {{ border-color: var(--main); background: var(--main); color: white; box-shadow: 0 4px 15px rgba(0,194,255,0.4); }}
            .video-grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 30px; }}
            .video-grid.active {{ display: grid; }}
            .card {{ background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); transition: 0.3s; display: flex; flex-direction: column; height: 100%; border: 1px solid #e2e8f0; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,0,0,0.12); }}
            .thumb-box {{ position: relative; aspect-ratio: 16/9; background: #000; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .badge {{ position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.8); color: white; font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: bold; }}
            .org-badge {{ position: absolute; top: 8px; left: 8px; font-size: 10px; padding: 3px 8px; border-radius: 6px; font-weight: bold; color: white; }}
            .info {{ padding: 20px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 0.85rem; font-weight: bold; color: var(--main); margin-bottom: 8px; }}
            .video-title {{ font-weight: bold; font-size: 1rem; line-height: 1.5; margin-bottom: 12px; height: 3em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
            .ai-desc {{ background: #f8fafc; padding: 12px; border-radius: 12px; font-size: 0.85rem; color: #475569; border-left: 4px solid var(--main); font-style: italic; margin-bottom: 15px; }}
            .links {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: auto; }}
            .btn {{ text-decoration: none; padding: 10px; border-radius: 10px; font-size: 0.75rem; font-weight: 900; text-align: center; transition: 0.2s; }}
            .btn-yt {{ background: var(--dark); color: white; grid-column: span 2; margin-bottom: 5px; }}
            .btn-amz {{ background: #ff9900; color: white; }}
            .btn-rak {{ background: #bf0000; color: white; }}
        </style>
        <script>
            function tab(id) {{
                document.querySelectorAll('.video-grid').forEach(g => g.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.getElementById(id).classList.add('active');
                document.getElementById('btn-' + id).classList.add('active');
            }}
        </script>
    </head>
    <body onload="tab('ja')">
        <header>
            <h1>🌟 {SITE_NAME}</h1>
            <p class="hero-text">AI解析ポータル | 再生数TOP100</p>
            <div style="font-size: 0.8rem; margin-top: 15px; opacity: 0.8;">最終更新: {datetime.now().strftime('%m/%d %H:%M')}</div>
        </header>
        <div class="container">
            <div class="tabs">
                <button id="btn-ja" class="tab-btn active" onclick="tab('ja')">🇯🇵 日本語</button>
                <button id="btn-en" class="tab-btn" onclick="tab('en')">🇺🇸 English</button>
                <button id="btn-id" class="tab-btn" onclick="tab('id')">🇮🇩 Indonesia</button>
                <button id="btn-stars" class="tab-btn" onclick="tab('stars')">⭐ ホロスターズ</button>
            </div>
    """

    # 言語・グループごとのHTML格納用
    html_sections = {"ja": "", "en": "", "id": "", "stars": ""}

    for v in videos:
        try:
            ch_name = v['channel']['name']
            sub_org = v['channel'].get('sub_org', '')
            v_id, title = v['id'], v['title']
            views = v.get('view_count', 0)
            lang = v.get('lang', 'ja')

            # グループ判定
            is_stars = "stars" in sub_org.lower() or "stars" in ch_name.lower()
            target_key = "stars" if is_stars else lang if lang in html_sections else "ja"
            org_label = "STARS" if is_stars else "HOLO"
            accent = "var(--stars)" if is_stars else "var(--main)"

            # AI解析
            prompt = f"Music: [Song - Artist] or [None]. Summary: 15 chars. Format: Music|Summary. Title: {title}"
            try:
                res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                ai = res.text.strip().split('|')
                cat, desc = (ai[0].strip(), ai[1].strip()) if len(ai) > 1 else ("Other", "最新情報をチェック！")
            except: cat, desc = "Other", "配信情報をAI分析中"

            search = urllib.parse.quote(f"{'ホロライブ' if not is_stars else 'ホロスターズ'} {ch_name}")
            amz = f"https://www.amazon.co.jp/s?k={search}&tag={AMAZON_ID}"
            rak = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search}%2F"

            html_sections[target_key] += f"""
            <div class="card">
                <div class="thumb-box">
                    <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" class="thumb">
                    <div class="badge">👀 {views:,} views</div>
                    <div class="org-badge" style="background:{accent}">{org_label}</div>
                </div>
                <div class="info">
                    <div class="ch-name">👤 {ch_name}</div>
                    <div class="video-title">{title}</div>
                    <div class="ai-desc">🤖 {desc}</div>
                    <div class="links">
                        <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-yt">視聴する</a>
                        <a href="{amz}" target="_blank" class="btn btn-amz">Amazon</a>
                        <a href="{rak}" target="_blank" class="btn btn-rak">楽天市場</a>
                    </div>
                </div>
            </div>"""
        except: continue

    for key, content in html_sections.items():
        html_content += f'<div id="{key}" class="video-grid {"active" if key=="ja" else ""}">{content}</div>'

    html_content += f"""
        </div>
        <footer style="text-align:center; padding:60px; color:#94a3b8;">© {datetime.now().year} {SITE_NAME} | Fan Project</footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    main()
