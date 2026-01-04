import os
import requests
from google import genai
from datetime import datetime

# ==========================================
# 🌟 あなたの専用ID設定済み
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_top_100(org):
    url = "https://holodex.net/api/v2/videos"
    combined = []
    for offset in [0, 50]:
        params = {
            "org": org, "limit": 50, "offset": offset,
            "sort": "view_count", "order": "desc", "type": "stream,clip"
        }
        try:
            res = requests.get(url, params=params, headers={"X-APIKEY": HOLODEX_API_KEY})
            data = res.json()
            if isinstance(data, list): combined.extend(data)
        except: pass
    return combined

def main():
    v_holo = [v for v in fetch_top_100("Hololive") if "stars" not in v.get('channel', {}).get('sub_org', '').lower()]
    v_stars = fetch_top_100("Holostars")
    client = genai.Client(api_key=GEMINI_API_KEY)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} | HOLODEX Style Portal</title>
        <style>
            :root {{
                --bg-body: #121212; --bg-sidebar: #1e1e1e; --bg-card: #1e1e1e;
                --text-main: #efeff1; --text-sub: #adadb8; --accent: #00c2ff;
                --stars: #ffb800; --music: #bb86fc;
            }}
            body {{
                font-family: Inter, "Roobert", "Helvetica Neue", Helvetica, Arial, sans-serif;
                background-color: var(--bg-body); color: var(--text-main); margin: 0; display: flex;
            }}
            
            /* 左サイドバー */
            nav {{
                width: 240px; height: 100vh; background: var(--bg-sidebar); 
                position: fixed; border-right: 1px solid #333; padding-top: 20px;
            }}
            .nav-item {{
                padding: 12px 20px; cursor: pointer; display: flex; align-items: center;
                font-weight: bold; color: var(--text-sub); transition: 0.2s;
            }}
            .nav-item:hover {{ background: #333; color: var(--text-main); }}
            .nav-item.active {{ color: var(--accent); border-left: 4px solid var(--accent); background: #262626; }}
            .nav-item-stars.active {{ color: var(--stars); border-left: 4px solid var(--stars); }}

            /* メインコンテンツ */
            main {{ flex: 1; margin-left: 240px; padding: 20px; }}
            .header-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }}

            /* カードデザイン (HOLODEX Style) */
            .card {{ background: var(--bg-card); border-radius: 4px; overflow: hidden; transition: 0.2s; position: relative; }}
            .card:hover {{ background: #262626; }}
            .thumb-box {{ position: relative; width: 100%; aspect-ratio: 16/9; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .badge {{ position: absolute; bottom: 4px; right: 4px; background: rgba(0,0,0,0.8); font-size: 11px; padding: 2px 4px; border-radius: 2px; }}
            .org-tag {{ position: absolute; top: 4px; left: 4px; font-size: 10px; padding: 2px 4px; border-radius: 2px; font-weight: bold; }}

            .info {{ padding: 10px; font-size: 13px; }}
            .video-title {{ font-weight: bold; line-height: 1.2; height: 2.4em; overflow: hidden; margin-bottom: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
            .ch-name {{ color: var(--text-sub); font-size: 12px; margin-bottom: 6px; }}
            
            .ai-box {{ background: #2d2d2d; padding: 6px; border-radius: 4px; margin-bottom: 8px; border-left: 3px solid var(--accent); }}
            .music-info {{ color: var(--music); font-weight: bold; font-size: 11px; margin-bottom: 2px; }}
            .ai-desc {{ color: #ccc; font-size: 11px; }}

            .links {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }}
            .btn {{ text-decoration: none; text-align: center; padding: 6px; border-radius: 2px; font-size: 11px; font-weight: bold; color: white; }}
            .btn-amz {{ background: #333; border: 1px solid #444; }}
            .btn-rak {{ background: #333; border: 1px solid #444; }}
            .btn:hover {{ background: #444; }}

            @media (max-width: 768px) {{
                nav {{ width: 60px; }} .nav-text {{ display: none; }} main {{ margin-left: 60px; }}
            }}
        </style>
        <script>
            function show(id) {{
                document.querySelectorAll('.video-list').forEach(el => el.style.display = 'none');
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                document.getElementById(id).style.display = 'grid';
                document.getElementById('n-' + id).classList.add('active');
            }}
        </script>
    </head>
    <body onload="show('holo')">
        <nav>
            <div style="padding: 0 20px 20px; color: var(--accent); font-size: 20px; font-weight: 900;">{SITE_NAME}</div>
            <div id="n-holo" class="nav-item active" onclick="show('holo')"><span class="nav-text">Hololive</span></div>
            <div id="n-stars" class="nav-item nav-item-stars" onclick="show('stars')"><span class="nav-text">Holostars</span></div>
        </nav>
        <main>
            <div class="header-bar">
                <div style="font-weight: bold; color: var(--text-sub);">再生数上位 100選</div>
                <div style="font-size: 12px; color: #555;">Updated: {datetime.now().strftime('%m/%d %H:%M')}</div>
            </div>

            <div id="holo" class="video-list grid">
    """

    def create_card(v, org_name, color):
        try:
            if not isinstance(v.get('channel'), dict): return ""
            ch, v_id, title, views = v['channel']['name'], v['id'], v['title'], v.get('view_count', 0)
        except: return ""

        prompt = f"Music: [Song - Artist] or [None]. Summary: 15 chars. Format: Music|Summary. Title: {title}"
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            parts = res.text.strip().split('|')
            m_val, ai_txt = parts[0].strip(), parts[1].strip() if len(parts) > 1 else "Analysis..."
        except: m_val, ai_txt = "[None]", "Analyzing..."

        m_html = f'<div class="music-info">🎵 {m_val}</div>' if "[None]" not in m_val else ""
        q = requests.utils.quote(f"{org_name} {ch}")

        return f"""
        <div class="card">
            <div class="thumb-box">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" class="thumb" loading="lazy">
                <div class="badge">{views:,} views</div>
                <div class="org-tag" style="background:{color};">{org_name[:4].upper()}</div>
            </div>
            <div class="info">
                <div class="video-title">{title}</div>
                <div class="ch-name">{ch}</div>
                <div class="ai-box" style="border-left-color:{color};">
                    {m_html}
                    <div class="ai-desc">🤖 {ai_txt}</div>
                </div>
                <div class="links">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-amz" style="grid-column: span 2; background: {color}; border:none; margin-bottom:4px;">Watch</a>
                    <a href="https://www.amazon.co.jp/s?k={q}&tag={AMAZON_ID}" target="_blank" class="btn btn-amz">Amazon</a>
                    <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{q}%2F" target="_blank" class="btn btn-rak">Rakuten</a>
                </div>
            </div>
        </div>"""

    for v in v_holo: html_content += create_card(v, "Hololive", "var(--accent)")
    html_content += """</div><div id="stars" class="video-list grid" style="display:none;">"""
    for v in v_stars: html_content += create_card(v, "Holostars", "var(--stars)")

    html_content += """</main></body></html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__": main()
