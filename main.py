import os
import requests
from google import genai
from datetime import datetime, timedelta
import urllib.parse
import re
import time

# ==========================================
# 🌟 設定・アフィリエイトID
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ応援ナビ"
SITE_URL = "https://sakagamiyoshikawa-lang.github.io/my-hololive-bot/" 

# 厳密なグループ判定ロジック
def get_group(name):
    n = name.lower()
    if any(x in n for x in ["いろは", "こより", "クロヱ", "ラプラス", "ルイ", "iroha", "koyori", "chloe", "laplus", "lui"]): return "holoX"
    # EN: Myth, Council, Promise, Advent, Justice
    if any(x in n for x in ["gura", "calliope", "kiara", "ina", "amelia", "baelz", "mumei", "fauna", "kronii", "fuwa", "mococo", "bijou", "nerissa", "shiori", "raora", "cecilia", "elizabeth", "gigi"]): return "EN"
    # ID: 1, 2, 3 generations
    if any(x in n for x in ["risu", "moona", "iofi", "ollie", "anya", "reine", "zeta", "kaela", "kobo"]): return "ID"
    # ReGLOSS
    if any(x in n for x in ["ao", "kanade", "ririka", "raden", "hajime"]): return "ReGLOSS"
    return "JP"

# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_pure_holo():
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    filtered_list = []
    for ep in ["live", "videos"]:
        params = {"org": "Hololive", "limit": 50}
        if ep == "videos": params.update({"sort": "view_count", "order": "desc", "type": "stream"})
        try:
            res = requests.get(f"https://holodex.net/api/v2/{ep}", params=params, headers=headers, timeout=20)
            if res.status_code == 200:
                data = res.json()
                for v in data:
                    ch = v.get('channel', {})
                    org = ch.get('org', '')
                    sub_org = ch.get('suborg', '')
                    # 【鉄壁の検閲】所属が 'Hololive' かつ、Stars関係の文字列が含まれていないこと
                    if org == "Hololive" and "STARS" not in sub_org.upper() and "STARS" not in ch.get('name', '').upper():
                        filtered_list.append(v)
            time.sleep(1)
        except: pass
    return filtered_list

def main():
    raw_list = fetch_pure_holo()
    client = genai.Client(api_key=GEMINI_API_KEY)

    # 重複排除
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
        
        highlight, msg = "必見の配信！", "みんなで応援しましょう！"
        try:
            # プロンプトを強化して、一律な文章を避ける
            prompt = f"配信『{title}』の内容から、ファンの期待を煽る15文字の見出し|20文字の熱い紹介文を作って。句読点は不要。"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                highlight, msg = parts[0].strip(), parts[1].strip() if len(parts) > 1 else msg
        except: pass

        badge = '<div class="badge live">LIVE</div>' if status == 'live' else f'<div class="badge upcoming" data-start="{raw_start}">待機中</div>'
        
        # 予約用URL生成
        cal_url = "#"
        if status == 'upcoming' and raw_start:
            try:
                st_dt = datetime.strptime(raw_start.replace('Z', '')[:19], '%Y-%m-%dT%H:%M:%S')
                st, et = st_dt.strftime('%Y%m%dT%H%M%SZ'), (st_dt + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')
                cal_url = f"https://www.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote('【予約】'+title)}&dates={st}/{et}&details={urllib.parse.quote('出演: '+raw_ch_name)}"
            except: pass

        search_query = urllib.parse.quote(clean_name)
        card_class = "pick-card" if is_pick else "card"
        
        return f"""
        <div class="{card_class}" data-group="{group}">
            <div class="thumb-box">
                <img src="https://img.youtube.com/vi/{v_id}/maxresdefault.jpg" onerror="this.src='https://img.youtube.com/vi/{v_id}/mqdefault.jpg'" loading="lazy">
                {badge}
            </div>
            <div class="card-body">
                <p class="ch-name">👤 {raw_ch_name}</p>
                <h3 class="highlight-txt">{highlight}</h3>
                <div class="quote-box">{msg}</div>
                <div class="actions">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn watch">📺 視聴・応援に行く</a>
                    {f'<a href="{cal_url}" target="_blank" class="btn reserve">📅 予約 (Google連携)</a>' if status == 'upcoming' else ''}
                    <div class="support-grid">
                        <a href="https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}" target="_blank" class="s-link amz">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F" target="_blank" class="s-link rak">楽天</a>
                        <a href="https://www.youtube.com/channel/{ch_id}/join" target="_blank" class="s-link join">メン限</a>
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
        <style>
            :root {{ --main: #00c2ff; --bg: #f8fafc; --card: #ffffff; --text: #1e293b; }}
            @media (prefers-color-scheme: dark) {{ :root {{ --bg: #0f172a; --card: #1e293b; --text: #f8fafc; }} }}
            body {{ font-family: 'M PLUS Rounded 1c', sans-serif; background: var(--bg); margin: 0; color: var(--text); }}
            header {{ 
                background: linear-gradient(135deg, #00c2ff 0%, #0078ff 100%); 
                color: #fff; padding: 60px 20px 90px; text-align: center;
                clip-path: polygon(0 0, 100% 0, 100% 88%, 50% 100%, 0 88%);
                position: relative; overflow: hidden;
            }}
            .deco {{ position: absolute; background: rgba(255,255,255,0.1); width: 80px; height: 80px; transform: rotate(45deg); animation: float 15s infinite; }}
            @keyframes float {{ 0% {{ top: 110%; left: 10%; }} 100% {{ top: -20%; left: 90%; }} }}

            .nav-filter {{ display: flex; justify-content: center; gap: 8px; margin: -25px auto 40px; position: relative; z-index: 100; flex-wrap: wrap; }}
            .f-btn {{ padding: 10px 18px; border: none; background: var(--card); color: #475569; border-radius: 50px; font-weight: 900; box-shadow: 0 4px 12px rgba(0,0,0,0.1); cursor: pointer; }}
            .f-btn.active {{ background: var(--main); color: white; }}

            .container {{ max-width: 1400px; margin: 0 auto; padding: 0 20px; }}
            .pick-card {{ background: var(--card); border-radius: 40px; display: grid; grid-template-columns: 1.6fr 1fr; overflow: hidden; box-shadow: 0 25px 50px rgba(0,0,0,0.1); margin-bottom: 50px; border: 4px solid var(--main); }}
            @media (max-width: 900px) {{ .pick-card {{ grid-template-columns: 1fr; }} }}

            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 30px; }}
            .card {{ background: var(--card); border-radius: 32px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05); transition: 0.3s; display: flex; flex-direction: column; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 45px rgba(0,194,255,0.2); }}

            .thumb-box {{ position: relative; aspect-ratio: 16/9; background:#000; }}
            .thumb-box img {{ width: 100%; height: 100%; object-fit: cover; }}
            .badge {{ position: absolute; top: 15px; right: 15px; padding: 6px 14px; border-radius: 12px; font-size: 11px; font-weight: 900; color: #fff; }}
            .badge.live {{ background: #ff0000; box-shadow: 0 0 15px rgba(255,0,0,0.4); }}
            .badge.upcoming {{ background: #ffb800; }}

            .card-body {{ padding: 25px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 11px; color: var(--main); font-weight: 900; margin-bottom: 8px; }}
            .highlight-txt {{ font-size: 1.35rem; font-weight: 900; margin-bottom: 12px; line-height: 1.2; }}
            .quote-box {{ background: rgba(0,194,255,0.08); padding: 14px; border-radius: 18px; font-size: 14px; border-left: 5px solid var(--main); margin-bottom: 20px; font-weight: 700; }}
            
            .btn {{ display: block; text-decoration: none; text-align: center; padding: 14px; border-radius: 16px; font-weight: 900; font-size: 14px; margin-bottom: 10px; }}
            .btn.watch {{ background: var(--main); color: #fff; }}
            .btn.reserve {{ background: #ffb800; color: #fff; }}
            .support-grid {{ display: flex; gap: 6px; }}
            .s-link {{ flex: 1; text-decoration: none; font-size: 10px; font-weight: 900; text-align: center; padding: 10px 2px; border-radius: 10px; background: rgba(0,0,0,0.05); color: #475569; }}
        </style>
    </head>
    <body>
        <header><div class="deco"></div><h1 style="font-size: 2.8rem; font-weight: 900; margin:0;">💙 {SITE_NAME}</h1><p style="font-weight: 700; opacity: 0.9;">ホロライブの魅力をAIで精査し、全力で応援・支援するポータル</p></header>
        <div class="nav-filter">
            <button class="f-btn active" onclick="filter('all')">すべて</button>
            <button class="f-btn" onclick="filter('JP')">JP</button>
            <button class="f-btn" onclick="filter('holoX')">holoX</button>
            <button class="f-btn" onclick="filter('ReGLOSS')">ReGLOSS</button>
            <button class="f-btn" onclick="filter('EN')">EN</button>
            <button class="f-btn" onclick="filter('ID')">ID</button>
        </div>
        <div class="container">
            <div class="pick-area">{pick_html}</div>
            <div class="grid">{cards_html}</div>
        </div>
        <script>
            function filter(g) {{
                document.querySelectorAll('.f-btn').forEach(b => b.classList.remove('active'));
                event.target.classList.add('active');
                document.querySelectorAll('.card, .pick-card').forEach(c => {{
                    c.style.display = (g === 'all' || c.dataset.group === g) ? 'flex' : 'none';
                    if (c.classList.contains('pick-card') && g !== 'all') c.style.display = 'grid';
                }});
            }}
            setInterval(() => {{
                document.querySelectorAll('.badge.upcoming').forEach(b => {{
                    const start = new Date(b.dataset.start);
                    const diff = Math.floor((start - new Date()) / 1000 / 60);
                    if (diff > 0) b.innerText = "あと " + diff + "分";
                    else b.innerText = "まもなく開始";
                }});
            }}, 60000);
        </script>
    </body>
    </html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(full_html)

if __name__ == "__main__": main()
