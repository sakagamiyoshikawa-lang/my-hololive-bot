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

def super_clean_name(raw_name):
    # 「Ch.」「- hololive-EN」「- holoX -」などのゴミを徹底除去
    name = re.sub(r'(?i)ch\.|channel|\s*-\s*.*|hololive|holoX|holoJP|holoEN|holoID|ReGLOSS', '', raw_name).strip()
    return name

def get_group(name):
    n = name.lower()
    if any(x in n for x in ["いろは", "こより", "クロヱ", "ラプラス", "ルイ"]): return "holoX"
    if any(x in n for x in ["gura", "calli", "kiara", "ina", "amelia", "baelz", "mumei", "fauna", "kronii", "fuwa", "moco", "bijou", "nerissa", "shiori", "raora", "ceci", "eliz", "gigi"]): return "EN"
    if any(x in n for x in ["risu", "moona", "iofi", "ollie", "anya", "reine", "zeta", "kaela", "kobo"]): return "ID"
    return "JP"

# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_pure_holo():
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    filtered_list = []
    for ep in ["live", "videos"]:
        params = {"org": "Hololive", "limit": 60}
        if ep == "videos": params.update({"type": "stream", "status": "upcoming"})
        try:
            res = requests.get(f"https://holodex.net/api/v2/{ep}", params=params, headers=headers, timeout=20)
            if res.status_code == 200:
                for v in res.json():
                    # 削除済み・非公開・Stars勢を厳密に除外
                    if v.get('channel', {}).get('org') == 'Hololive' and \
                       "STARS" not in v.get('channel', {}).get('suborg', '').upper() and \
                       v.get('id'): # 動画IDが存在するもののみ
                        filtered_list.append(v)
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
        clean_name = super_clean_name(raw_ch_name)
        group = get_group(raw_ch_name)
        
        # AI解析
        icon, highlight, msg, color = "📺", "必見の配信！", "一緒に応援しましょう！", "#00c2ff"
        try:
            prompt = f"配信『{title}』の魅力を10文字の見出し|15文字の紹介文|テーマカラー16進数で。定型文禁止。"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text and '|' in res.text:
                parts = res.text.strip().split('|')
                highlight, msg = parts[0].strip(), parts[1].strip()
                if len(parts) > 2: color = parts[2].strip()
        except: pass

        badge = '<div class="badge live">LIVE</div>' if status == 'live' else f'<div class="badge upcoming" data-start="{raw_start}">待機中</div>'
        
        # カレンダー予約ボタンの復活
        res_btn = ""
        if status == 'upcoming' and raw_start:
            try:
                st_dt = datetime.strptime(raw_start.replace('Z', '')[:19], '%Y-%m-%dT%H:%M:%S')
                st, et = st_dt.strftime('%Y%m%dT%H%M%SZ'), (st_dt + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')
                cal_url = f"https://www.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote('【視聴】'+title)}&dates={st}/{et}"
                res_btn = f'<a href="{cal_url}" target="_blank" class="btn reserve">📅 予約 (カレンダー)</a>'
            except: pass

        share_text = urllib.parse.quote(f"✨{highlight}\n{msg}\n#ホロ応援ナビ #{clean_name}")
        search_query = urllib.parse.quote(clean_name)
        card_class = "pick-card" if is_pick else "card"
        border_style = f'style="border: 3px solid {color};"' if is_pick else ""
        
        return f"""
        <div class="{card_class}" data-group="{group}" data-ch-id="{ch_id}" {border_style}>
            <div class="thumb-box">
                <img src="https://img.youtube.com/vi/{v_id}/maxresdefault.jpg" onerror="this.src='https://img.youtube.com/vi/{v_id}/mqdefault.jpg'" loading="lazy">
                {badge}
                <button class="oshi-btn" onclick="toggleOshi('{ch_id}')">❤</button>
            </div>
            <div class="card-body">
                <p class="ch-name" style="color:{color}">👤 {raw_ch_name}</p>
                <h3 class="highlight-txt">{highlight}</h3>
                <div class="quote-box">{msg}</div>
                <div class="actions">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn watch">📺 視聴・応援に行く</a>
                    {res_btn}
                    <a href="https://twitter.com/intent/tweet?text={share_text}&url={SITE_URL}" target="_blank" class="btn share">📢 布教する</a>
                    <div class="support-grid">
                        <a href="https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}" target="_blank" class="s-link amz" onclick="celebrate()">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F" target="_blank" class="s-link rak" onclick="celebrate()">楽天</a>
                    </div>
                </div>
            </div>
        </div>"""

    pick_html = create_card(unique_list[0], is_pick=True) if unique_list else ""
    cards_html = "".join([create_card(v) for v in unique_list[1:]])

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@700;900&display=swap" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
        <style>
            :root {{ --main: #00c2ff; --bg: #f8fafc; --card: #ffffff; --text: #1e293b; }}
            @media (prefers-color-scheme: dark) {{ :root {{ --bg: #0f172a; --card: #1e293b; --text: #f8fafc; }} }}
            body {{ font-family: 'M PLUS Rounded 1c', sans-serif; background: var(--bg); margin: 0; color: var(--text); padding-bottom: 90px; }}
            header {{ background: linear-gradient(135deg, #00c2ff, #0078ff); color: #fff; padding: 50px 20px 80px; text-align: center; clip-path: polygon(0 0, 100% 0, 100% 88%, 50% 100%, 0 88%); }}
            .nav-filter {{ display: flex; justify-content: center; gap: 8px; margin: -25px auto 40px; position: relative; z-index: 100; flex-wrap: wrap; }}
            .f-btn {{ padding: 10px 18px; border: none; background: var(--card); color: #475569; border-radius: 50px; font-weight: 900; box-shadow: 0 4px 12px rgba(0,0,0,0.1); cursor: pointer; }}
            .f-btn.active {{ background: var(--main); color: white; }}
            .container {{ max-width: 1400px; margin: 0 auto; padding: 0 20px; }}
            .pick-card {{ background: var(--card); border-radius: 40px; display: grid; grid-template-columns: 1.6fr 1fr; overflow: hidden; margin-bottom: 50px; }}
            @media (max-width: 900px) {{ .pick-card {{ grid-template-columns: 1fr; }} }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 30px; }}
            .card {{ background: var(--card); border-radius: 32px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.04); transition: 0.3s; display: flex; flex-direction: column; }}
            .thumb-box {{ position: relative; aspect-ratio: 16/9; }}
            .thumb-box img {{ width: 100%; height: 100%; object-fit: cover; }}
            .badge {{ position: absolute; top: 15px; right: 15px; padding: 6px 14px; border-radius: 12px; font-size: 11px; font-weight: 900; color: #fff; background: #ffb800; }}
            .badge.live {{ background: #ff0000; box-shadow: 0 0 15px rgba(255,0,0,0.4); }}
            .oshi-btn {{ position: absolute; top: 10px; left: 10px; background: rgba(255,255,255,0.8); border: none; width: 35px; height: 35px; border-radius: 50%; cursor: pointer; font-size: 18px; color: #ccc; }}
            .oshi-btn.active {{ color: #ff4757; background: #fff; }}
            .card-body {{ padding: 25px; flex-grow: 1; display: flex; flex-direction: column; }}
            .highlight-txt {{ font-size: 1.3rem; font-weight: 900; margin: 10px 0; }}
            .quote-box {{ background: rgba(0,194,255,0.06); padding: 14px; border-radius: 18px; font-size: 14px; border-left: 5px solid var(--main); margin-bottom: 20px; font-weight: 700; }}
            .btn {{ display: block; text-decoration: none; text-align: center; padding: 14px; border-radius: 16px; font-weight: 900; margin-bottom: 8px; font-size: 14px; }}
            .btn.watch {{ background: var(--main); color: #fff; }}
            .btn.reserve {{ background: #ffb800; color: #fff; }}
            .btn.share {{ background: #000; color: #fff; }}
            .support-grid {{ display: flex; gap: 6px; }}
            .s-link {{ flex: 1; text-decoration: none; font-size: 10px; font-weight: 900; text-align: center; padding: 10px 2px; border-radius: 10px; background: rgba(0,0,0,0.05); color: var(--text); }}
            .bottom-nav {{ position: fixed; bottom: 0; left: 0; right: 0; background: var(--card); display: flex; justify-content: space-around; padding: 15px; box-shadow: 0 -5px 20px rgba(0,0,0,0.1); z-index: 1000; }}
            .nav-item {{ text-decoration: none; color: #94a3b8; font-size: 10px; text-align: center; font-weight: 900; cursor:pointer; }}
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
            <div class="nav-item active" onclick="location.reload()">🏠 ホーム</div>
            <div class="nav-item" id="oshiModeBtn" onclick="toggleOshiMode()">⭐ 推しメン</div>
        </div>
        <script>
            let oshiList = JSON.parse(localStorage.getItem('oshiList') || '[]');
            let oshiMode = false;
            function toggleOshi(id) {{ oshiList = oshiList.includes(id) ? oshiList.filter(x => x !== id) : [...oshiList, id]; localStorage.setItem('oshiList', JSON.stringify(oshiList)); renderOshi(); }}
            function renderOshi() {{ document.querySelectorAll('[data-ch-id]').forEach(c => {{ const btn = c.querySelector('.oshi-btn'); if (oshiList.includes(c.dataset.ch_id)) btn.classList.add('active'); else btn.classList.remove('active'); if (oshiMode) c.style.display = oshiList.includes(c.dataset.ch_id) ? 'flex' : 'none'; }}); }}
            function toggleOshiMode() {{ oshiMode = !oshiMode; document.getElementById('oshiModeBtn').classList.toggle('active'); renderOshi(); }}
            function filter(g) {{ document.querySelectorAll('.f-btn').forEach(b => b.classList.remove('active')); event.target.classList.add('active'); document.querySelectorAll('.card, .pick-card').forEach(c => c.style.display = (g === 'all' || c.dataset.group === g) ? 'flex' : 'none'); }}
            function celebrate() {{ confetti({{ particleCount: 150, spread: 70, origin: {{ y: 0.6 }} }}); }}
            window.onload = renderOshi;
        </script>
    </body>
    </html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(full_html)

if __name__ == "__main__": main()
