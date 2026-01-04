import os
import requests
from google import genai
from datetime import datetime

# ==========================================
# 🌟 設定済みID
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_top_100(org):
    """API上限50件を回避し、指定組織から再生数上位100件を確実に取得"""
    url = "https://holodex.net/api/v2/videos"
    combined = []
    for offset in [0, 50]:
        params = {
            "org": org, "limit": 50, "offset": offset,
            "sort": "view_count", "order": "desc", "type": "stream,clip"
        }
        try:
            res = requests.get(url, params=params, headers={"X-APIKEY": HOLODEX_API_KEY}, timeout=10)
            data = res.json()
            if isinstance(data, list):
                combined.extend([v for v in data if isinstance(v, dict)])
        except:
            continue
    return combined

def main():
    # 1. 各グループから100件ずつ取得
    v_holo = fetch_top_100("Hololive")
    v_stars = fetch_top_100("Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTML構築
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} | Holodex UI</title>
        <style>
            :root {{
                --bg: #0f0f0f; --side: #121212; --card: #1c1c1c;
                --text: #ffffff; --sub: #aaaaaa; --accent: #00c2ff;
                --stars: #ffb800; --music: #bb86fc;
            }}
            body {{
                font-family: "Roboto", Arial, sans-serif; background: var(--bg); 
                color: var(--text); margin: 0; display: flex; height: 100vh; overflow: hidden;
            }}
            
            /* サイドバー */
            nav {{
                width: 200px; background: var(--side); border-right: 1px solid #333;
                flex-shrink: 0; display: flex; flex-direction: column; padding-top: 20px;
            }}
            .logo {{ padding: 0 20px 30px; font-size: 22px; font-weight: 900; color: var(--accent); }}
            .nav-item {{
                padding: 12px 20px; cursor: pointer; color: var(--sub); font-size: 14px;
                font-weight: bold; border-left: 4px solid transparent; transition: 0.2s;
            }}
            .nav-item:hover {{ background: #222; color: #fff; }}
            .nav-item.active {{ background: #262626; color: var(--accent); border-left-color: var(--accent); }}
            .nav-stars.active {{ color: var(--stars); border-left-color: var(--stars); }}

            /* メイン */
            main {{ flex: 1; overflow-y: auto; padding: 20px; }}
            .top-info {{ display: flex; justify-content: space-between; margin-bottom: 20px; font-size: 13px; color: var(--sub); }}
            
            .grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }}
            .grid.active {{ display: grid; }}

            /* カード */
            .card {{ background: var(--bg-card); border-radius: 4px; overflow: hidden; display: flex; flex-direction: column; transition: 0.15s; position: relative; }}
            .card:hover {{ background: #2a2a2a; transform: scale(1.02); z-index: 10; }}
            .thumb-box {{ position: relative; aspect-ratio: 16/9; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .v-badge {{ position: absolute; bottom: 4px; right: 4px; background: rgba(0,0,0,0.8); font-size: 11px; padding: 2px 6px; border-radius: 2px; }}

            .info {{ padding: 10px; flex-grow: 1; }}
            .title {{ font-size: 13px; font-weight: bold; line-height: 1.4; height: 2.8em; overflow: hidden; margin-bottom: 6px; }}
            .ch {{ font-size: 12px; color: var(--sub); margin-bottom: 8px; }}
            
            .ai-meta {{ border-top: 1px solid #333; padding-top: 8px; margin-top: 8px; font-size: 11px; }}
            .m-tag {{ color: var(--music); font-weight: bold; margin-bottom: 3px; }}
            .ai-desc {{ color: #777; font-style: italic; }}

            .links {{ display: flex; gap: 4px; margin-top: 10px; }}
            .btn {{ flex: 1; text-decoration: none; font-size: 10px; font-weight: bold; text-align: center; padding: 6px; border-radius: 2px; color: #fff; background: #333; }}
            .btn-watch {{ background: var(--accent); border: none; }}
        </style>
        <script>
            function tab(id) {{
                document.querySelectorAll('.grid').forEach(g => g.classList.remove('active'));
                document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                document.getElementById(id).classList.add('active');
                document.getElementById('btn-' + id).classList.add('active');
            }}
        </script>
    </head>
    <body onload="tab('holo')">
        <nav>
            <div class="logo">HoloNavi</div>
            <div id="btn-holo" class="nav-item active" onclick="tab('holo')">Hololive TOP 100</div>
            <div id="btn-stars" class="nav-item nav-stars" onclick="tab('stars')">Holostars TOP 100</div>
        </nav>
        <main>
            <div class="top-info">
                <span>再生数上位100選（自動更新）</span>
                <span>{datetime.now().strftime('%m/%d %H:%M')}</span>
            </div>
            <div id="holo" class="grid active">
    """

    def create_card(v, org_name, accent_color):
        channel = v.get('channel', {})
        ch_name = channel.get('name', 'Unknown') if isinstance(channel, dict) else "Unknown"
        v_id, title = v.get('id'), v.get('title', 'No Title')
        views = v.get('view_count', 0)
        
        # AI解析
        prompt = f"Music: [Song - Artist] or [None]. Summary: 15 chars. Format: Music|Summary. Title: {title}"
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            parts = res.text.strip().split('|')
            m_val, ai_txt = (parts[0].strip(), parts[1].strip()) if len(parts) > 1 else ("None", "最新情報をチェック")
        except: m_val, ai_txt = "None", "分析中"

        m_html = f'<div class="m-tag">🎵 {m_val}</div>' if "None" not in m_val else ""
        q = requests.utils.quote(f"{org_name} {ch_name}")

        return f"""
        <div class="card">
            <div class="thumb-box">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" class="thumb" loading="lazy">
                <div class="v-badge">{views:,} views</div>
            </div>
            <div class="info">
                <div class="title">{title}</div>
                <div class="ch">{ch_name}</div>
                <div class="ai-meta">
                    {m_html}
                    <div class="ai-desc">🤖 {ai_txt}</div>
                </div>
                <div class="links">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-watch" style="background:{accent_color}">Watch</a>
                    <a href="https://www.amazon.co.jp/s?k={q}&tag={AMAZON_ID}" target="_blank" class="btn">Amazon</a>
                    <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{q}%2F" target="_blank" class="btn">Rakuten</a>
                </div>
            </div>
        </div>"""

    # 生成
    for v in v_holo:
        if "stars" in str(v.get('channel', {}).get('sub_org', '')).lower(): continue
        html_content += create_card(v, "ホロライブ", "var(--accent)")
    
    html_content += """</div><div id="stars" class="grid">"""
    
    for v in v_stars:
        html_content += create_card(v, "ホロスターズ", "var(--stars)")

    html_content += """</div></main></body></html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
