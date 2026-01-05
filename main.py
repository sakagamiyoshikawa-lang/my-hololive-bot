import os
import requests
from google import genai
from datetime import datetime, timedelta
import urllib.parse
import re
import time

# ==========================================
# 🌟 設定
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ応援ナビ"
SITE_URL = "https://sakagamiyoshikawa-lang.github.io/my-hololive-bot/" 

def get_group(name):
    n = name.lower()
    if any(x in n for x in ["いろは", "こより", "クロヱ", "ラプラス", "ルイ"]): return "holoX"
    if any(x in n for x in ["gura", "calliope", "kiara", "ina", "amelia", "baelz", "mumei", "fauna", "kronii", "fuwa", "mococo", "bijou", "nerissa", "shiori", "raora", "cecilia", "elizabeth", "gigi"]): return "EN"
    if any(x in n for x in ["risu", "moona", "iofi", "ollie", "anya", "reine", "zeta", "kaela", "kobo"]): return "ID"
    if any(x in n for x in ["ao", "kanade", "ririka", "raden", "hajime"]): return "ReGLOSS"
    return "JP"

# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_pure_holo():
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    filtered_list = []
    for ep in ["live", "videos"]:
        params = {"org": "Hololive", "limit": 60}
        try:
            res = requests.get(f"https://holodex.net/api/v2/{ep}", params=params, headers=headers, timeout=20)
            if res.status_code == 200:
                # Stars関係を徹底排除
                filtered_list.extend([v for v in res.json() if v.get('channel', {}).get('org') == 'Hololive' and "STARS" not in v.get('channel', {}).get('suborg', '').upper()])
            time.sleep(1)
        except: pass
    return filtered_list

def main():
    raw_list = fetch_pure_holo()
    client = genai.Client(api_key=GEMINI_API_KEY)
    seen_ids = set()
    unique_list = [v for v in raw_list if v.get('id') not in seen_ids and not seen_ids.add(v.get('id'))]

    def create_card(v, is_pick=False):
        v_id, title = v.get('id'), v.get('title', 'No Title')
        status = v.get('status', 'past')
        raw_start = v.get('start_scheduled') or v.get('start_actual')
        ch = v.get('channel', {})
        raw_ch_name, ch_id = ch.get('name', 'Unknown'), ch.get('id')
        clean_name = re.sub(r'(?i)ch\.|channel|\s*-\s*.*|hololive', '', raw_ch_name).strip()
        group = get_group(raw_ch_name)
        
        # AIにジャンルと紹介文を判定させる
        topic_icon, highlight, msg = "📺", "必見の配信！", "みんなで応援しましょう！"
        try:
            prompt = f"配信『{title}』を解析し、アイコン(🎮,🎤,💬,🍲,🎨から1つ)|見出し(12文字)|紹介文(20文字)で答えて。句読点なし。"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                if len(parts) >= 3:
                    topic_icon, highlight, msg = parts[0].strip(), parts[1].strip(), parts[2].strip()
        except: pass

        badge = '<div class="badge live">LIVE</div>' if status == 'live' else f'<div class="badge upcoming" data-start="{raw_start}">待機中</div>'
        search_query = urllib.parse.quote(clean_name)
        card_class = "pick-card" if is_pick else "card"
        
        return f"""
        <div class="{card_class}" data-group="{group}" data-ch-id="{ch_id}">
            <div class="thumb-box">
                <img src="https://img.youtube.com/vi/{v_id}/maxresdefault.jpg" onerror="this.src='https://img.youtube.com/vi/{v_id}/mqdefault.jpg'" loading="lazy">
                {badge}
                <button class="oshi-btn" onclick="toggleOshi('{ch_id}')">❤</button>
                <div class="topic-tag">{topic_icon}</div>
            </div>
            <div class="card-body">
                <p class="ch-name">👤 {raw_ch_name}</p>
                <h3 class="highlight-txt">{highlight}</h3>
                <div class="quote-box">{msg}</div>
                <div class="actions">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn watch">📺 視聴・応援に行く</a>
                    <div class="support-grid">
                        <a href="https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}" target="_blank" class="s-link amz">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F" target="_blank" class="s-link rak">楽天</a>
                    </div>
                </div>
            </div>
        </div>"""

    pick_html = create_card(unique_list[0], is_pick=True) if unique_list else ""
    cards_html = "".join([create_card(v) for v in unique_list[1:]]) if len(unique_list) > 1 else ""

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@700;900&display=swap" rel="stylesheet">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <style>
            :root {{ --main: #00c2ff; --bg: #f8fafc; --card: #ffffff; --text: #1e293b; }}
            @media (prefers-color-scheme: dark) {{ :root {{ --bg: #0f172a; --card: #1e293b; --text: #f8fafc; }} }}
            body {{ font-family: 'M PLUS Rounded 1c', sans-serif; background: var(--bg); margin: 0; color: var(--text); padding-bottom: 80px; }}
            header {{ background: linear-gradient(135deg, #00c2ff, #0078ff); color: #fff; padding: 50px 20px 80px; text-align: center; clip-path: polygon(0 0, 100% 0, 100% 85%, 50% 100%, 0 85%); }}
            
            .nav-filter {{ display: flex; justify-content: center; gap: 8px; margin: -25px auto 40px; position: relative; z-index: 100; flex-wrap: wrap; }}
            .f-btn {{ padding: 10px 18px; border: none; background: var(--card); color: #475569; border-radius: 50px; font-weight: 900; box-shadow: 0 4px 12px rgba(0,0,0,0.1); cursor: pointer; }}
            .f-btn.active {{ background: var(--main); color: white; }}

            .container {{ max-width: 1400px; margin: 0 auto; padding: 0 20px; }}
            .pick-card {{ background: var(--card); border-radius: 40px; display: grid; grid-template-columns: 1.6fr 1fr; overflow: hidden; box-shadow: 0 25px 50px rgba(0,0,0,0.1); margin-bottom: 50px; border: 4px solid var(--main); }}
            @media (max-width: 900px) {{ .pick-card {{ grid-template-columns: 1fr; }} }}

            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 30px; }}
            .card {{ background: var(--card); border-radius: 32px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05); transition: 0.3s; display: flex; flex-direction: column; position: relative; }}
            .card:hover {{ transform: translateY(-10px); }}
            
            .thumb-box {{ position: relative; aspect-ratio: 16/9; }}
            .thumb-box img {{ width: 100%; height: 100%; object-fit: cover; }}
            .badge {{ position: absolute; top: 15px; right: 15px; padding: 6px 14px; border-radius: 12px; font-size: 11px; font-weight: 900; color: #fff; background: #ffb800; }}
            .badge.live {{ background: #ff0000; box-shadow: 0 0 15px rgba(255,0,0,0.4); }}
            
            .topic-tag {{ position: absolute; bottom: 10px; left: 10px; background: rgba(0,0,0,0.6); color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; }}
            .oshi-btn {{ position: absolute; top: 10px; left: 10px; background: rgba(255,255,255,0.8); border: none; width: 35px; height: 35px; border-radius: 50%; cursor: pointer; font-size: 18px; color: #ccc; transition: 0.2s; }}
            .oshi-btn.active {{ color: #ff4757; background: #fff; }}

            .card-body {{ padding: 25px; flex-grow: 1; display: flex; flex-direction: column; }}
            .highlight-txt {{ font-size: 1.3rem; font-weight: 900; margin: 10px 0; }}
            .quote-box {{ background: rgba(0,194,255,0.05); padding: 14px; border-radius: 18px; font-size: 14px; border-left: 5px solid var(--main); margin-bottom: 20px; }}
            
            .btn {{ display: block; text-decoration: none; text-align: center; padding: 14px; border-radius: 16px; font-weight: 900; background: var(--main); color: #fff; }}
            .support-grid {{ display: flex; gap: 6px; margin-top: 10px; }}
            .s-link {{ flex: 1; text-decoration: none; font-size: 11px; font-weight: 900; text-align: center; padding: 10px; border-radius: 10px; background: rgba(0,0,0,0.05); color: var(--text); }}

            /* ボトムナビゲーション */
            .bottom-nav {{ position: fixed; bottom: 0; left: 0; right: 0; background: var(--card); display: flex; justify-content: space-around; padding: 15px; box-shadow: 0 -5px 20px rgba(0,0,0,0.1); z-index: 1000; }}
            .nav-item {{ text-decoration: none; color: #94a3b8; font-size: 10px; text-align: center; font-weight: 900; }}
            .nav-item.active {{ color: var(--main); }}
        </style>
    </head>
    <body>
        <header><h1 style="font-size: 2.5rem; font-weight: 900; margin:0;">💙 {SITE_NAME}</h1><p>推しの活動をAIで精査し、全力で応援する</p></header>
        <div class="nav-filter">
            <button class="f-btn active" onclick="filter('all')">すべて</button>
            <button class="f-btn" onclick="filter('JP')">JP</button>
            <button class="f-btn" onclick="filter('holoX')">holoX</button>
            <button class="f-btn" onclick="filter('EN')">EN</button>
            <button class="f-btn" onclick="filter('ID')">ID</button>
        </div>
        <div class="container">
            <div class="pick-area">{pick_html}</div>
            <div class="grid" id="mainGrid">{cards_html}</div>
        </div>
        <div class="bottom-nav">
            <a href="#" class="nav-item active">🏠 ホーム</a>
            <a href="#" class="nav-item" onclick="showOshiOnly()">⭐ 推しメン</a>
            <a href="#featured-footer" class="nav-item">🛒 ショップ</a>
        </div>
        <script>
            let oshiList = JSON.parse(localStorage.getItem('oshiList') || '[]');
            function toggleOshi(id) {{
                oshiList = oshiList.includes(id) ? oshiList.filter(x => x !== id) : [...oshiList, id];
                localStorage.setItem('oshiList', JSON.stringify(oshiList));
                renderOshi();
            }}
            function renderOshi() {{
                document.querySelectorAll('[data-ch-id]').forEach(c => {{
                    const btn = c.querySelector('.oshi-btn');
                    if (oshiList.includes(c.dataset.ch_id)) btn.classList.add('active');
                    else btn.classList.remove('active');
                }});
            }}
            function filter(g) {{
                document.querySelectorAll('.f-btn').forEach(b => b.classList.remove('active'));
                event.target.classList.add('active');
                document.querySelectorAll('.card, .pick-card').forEach(c => c.style.display = (g === 'all' || c.dataset.group === g) ? 'flex' : 'none');
            }}
            window.onload = renderOshi;
        </script>
    </body>
    </html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(full_html)

if __name__ == "__main__": main()
