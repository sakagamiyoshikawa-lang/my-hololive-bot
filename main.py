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

# 期生・ユニットの判定用マッピング（簡易版）
def get_group(name):
    if any(x in name for x in ["いろは", "こより", "クロヱ", "ラプラス", "ルイ"]): return "holoX"
    if any(x in name for x in ["Gura", "Calliope", "Kiara", "Ina", "Amelia", "Baelz", "Mumei", "Fauna", "Kronii", "Sana", "Fuwa", "Mococo", "Bijou", "Nerissa", "Shiori"]): return "EN"
    if any(x in name for x in ["Risu", "Moona", "Iofifteen", "Ollie", "Anya", "Reine", "Zeta", "Kaela", "Kobo"]): return "ID"
    return "JP"

# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def super_clean_name(raw_name):
    name = re.sub(r'(?i)ch\.|channel|\s*-\s*.*|hololive|holoX|holoJP|holoEN|holoID', '', raw_name).strip()
    if re.search(r'[ぁ-んァ-ヶー一-龠]', name):
        name = re.sub(r'[a-zA-Z0-9\s!-/:-@[-`{-~]+', '', name).strip()
    return name if name else raw_name

def fetch_pure_holo():
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    combined = []
    for ep in ["live", "videos"]:
        params = {"org": "Hololive", "limit": 40}
        if ep == "videos": params.update({"sort": "view_count", "order": "desc", "type": "stream"})
        try:
            res = requests.get(f"https://holodex.net/api/v2/{ep}", params=params, headers=headers, timeout=20)
            if res.status_code == 200:
                data = res.json()
                combined.extend([v for v in data if isinstance(v, dict) and v.get('channel', {}).get('org') == 'Hololive'])
            time.sleep(1)
        except: pass
    return combined

def main():
    list_holo = fetch_pure_holo()
    client = genai.Client(api_key=GEMINI_API_KEY)

    def create_card(v, is_pick=False):
        v_id, title = v.get('id'), v.get('title', 'No Title')
        status = v.get('status', 'past')
        raw_start = v.get('start_scheduled') or v.get('start_actual')
        ch = v.get('channel', {})
        raw_ch_name, ch_id = ch.get('name', 'Unknown'), ch.get('id')
        clean_name = super_clean_name(raw_ch_name)
        group = get_group(raw_ch_name)
        
        highlight, msg = "必見の配信！", "一緒に応援しましょう！"
        try:
            prompt = f"配信『{title}』の魅力を10文字の見出し|15文字の紹介文で。ファン目線で。"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                highlight, msg = parts[0].strip(), parts[1].strip() if len(parts) > 1 else msg
        except: pass

        badge = f'<div class="badge live">LIVE</div>' if status == 'live' else f'<div class="badge upcoming" data-start="{raw_start}">待機中</div>'
        
        # 予約URL
        cal_url = "#"
        if status == 'upcoming' and raw_start:
            try:
                st_dt = datetime.strptime(raw_start.replace('Z', '')[:19], '%Y-%m-%dT%H:%M:%S')
                st, et = st_dt.strftime('%Y%m%dT%H%M%SZ'), (st_dt + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')
                cal_url = f"https://www.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote('【視聴予約】'+title)}&dates={st}/{et}&details={urllib.parse.quote('出演: '+raw_ch_name)}"
            except: pass

        share_text = urllib.parse.quote(f"✨{highlight}\n{msg}\n#ホロ応援ナビ #{clean_name}")
        search_query = urllib.parse.quote(clean_name)
        
        card_class = "pick-card" if is_pick else "card"
        
        return f"""
        <div class="{card_class}" data-group="{group}">
            <div class="thumb-box"><img src="https://img.youtube.com/vi/{v_id}/maxresdefault.jpg" onerror="this.src='https://img.youtube.com/vi/{v_id}/mqdefault.jpg'" loading="lazy">{badge}</div>
            <div class="card-body">
                <p class="ch-name">👤 {raw_ch_name}</p>
                <h3 class="highlight-txt">{highlight}</h3>
                <div class="quote-box">{msg}</div>
                <div class="actions">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn watch">📺 視聴・応援に行く</a>
                    {f'<a href="{cal_url}" target="_blank" class="btn reserve">📅 カレンダー予約</a>' if status == 'upcoming' else ''}
                    <div class="support-grid">
                        <a href="https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}" target="_blank" class="s-link amz">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F" target="_blank" class="s-link rak">楽天</a>
                        <a href="https://www.youtube.com/channel/{ch_id}/join" target="_blank" class="s-link join">メン限</a>
                    </div>
                </div>
            </div>
        </div>"""

    # 重複排除
    seen_ids = set()
    unique_list = [v for v in list_holo if v.get('id') not in seen_ids and not seen_ids.add(v.get('id'))]
    
    # ピックアップ（最初の1件）
    pick_html = create_card(unique_list[0], is_pick=True) if unique_list else ""
    # その他
    cards_html = "".join([create_card(v) for v in unique_list[1:]])

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@700;900&display=swap" rel="stylesheet">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <style>
            :root {{ --main: #00c2ff; --bg: #f0f4f8; --card: #ffffff; --text: #1e293b; }}
            @media (prefers-color-scheme: dark) {{ :root {{ --bg: #0f172a; --card: #1e293b; --text: #f8fafc; }} }}
            
            body {{ font-family: 'M PLUS Rounded 1c', sans-serif; background: var(--bg); margin: 0; color: var(--text); transition: 0.3s; }}
            
            /* ロゴ・アニメーションヘッダー */
            header {{ 
                background: linear-gradient(135deg, #00c2ff 0%, #0078ff 100%); 
                color: #fff; padding: 60px 20px 100px; text-align: center;
                clip-path: polygon(0 0, 100% 0, 100% 88%, 50% 100%, 0 88%);
                position: relative; overflow: hidden;
            }}
            .bg-shape {{ position: absolute; background: rgba(255,255,255,0.1); width: 100px; height: 100px; transform: rotate(45deg); animation: float 10s infinite; }}
            @keyframes float {{ 0% {{ top: 110%; left: 10%; }} 100% {{ top: -20%; left: 90%; }} }}

            /* フィルターナビ */
            .nav-filter {{ display: flex; justify-content: center; gap: 10px; margin: -30px auto 30px; position: relative; z-index: 100; flex-wrap: wrap; }}
            .f-btn {{ padding: 10px 20px; border: none; background: var(--card); color: var(--text); border-radius: 50px; font-weight: 900; box-shadow: 0 5px 15px rgba(0,0,0,0.1); cursor: pointer; }}
            .f-btn.active {{ background: var(--main); color: white; }}

            .container {{ max-width: 1400px; margin: 0 auto 60px; padding: 0 20px; }}
            
            /* ピックアップ */
            .pick-area {{ margin-bottom: 50px; }}
            .pick-card {{ background: var(--card); border-radius: 40px; display: grid; grid-template-columns: 1.5fr 1fr; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.1); }}
            @media (max-width: 850px) {{ .pick-card {{ grid-template-columns: 1fr; }} }}

            /* グリッド */
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 30px; }}
            .card {{ background: var(--card); border-radius: 30px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05); transition: 0.3s; display: flex; flex-direction: column; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,194,255,0.2); }}

            .thumb-box {{ position: relative; aspect-ratio: 16/9; background:#000; }}
            .thumb-box img {{ width: 100%; height: 100%; object-fit: cover; }}
            .badge {{ position: absolute; top: 15px; right: 15px; padding: 6px 15px; border-radius: 12px; font-size: 11px; font-weight: 900; color: #fff; }}
            .badge.live {{ background: #ff0000; box-shadow: 0 0 15px rgba(255,0,0,0.5); }}
            .badge.upcoming {{ background: #ffb800; }}

            .card-body {{ padding: 25px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 11px; color: var(--main); font-weight: 900; margin-bottom: 10px; }}
            .highlight-txt {{ font-size: 1.4rem; font-weight: 900; margin-bottom: 12px; line-height: 1.2; }}
            .quote-box {{ background: rgba(0,194,255,0.05); padding: 15px; border-radius: 18px; font-size: 14px; border-left: 5px solid var(--main); margin-bottom: 20px; font-weight: 700; }}
            
            .btn {{ display: block; text-decoration: none; text-align: center; padding: 14px; border-radius: 18px; font-weight: 900; font-size: 14px; margin-bottom: 8px; }}
            .btn.watch {{ background: var(--main); color: #fff; }}
            .btn.reserve {{ background: #ffb800; color: #fff; }}
            .support-grid {{ display: flex; gap: 6px; }}
            .s-link {{ flex: 1; text-decoration: none; font-size: 10px; font-weight: 900; text-align: center; padding: 10px 2px; border-radius: 10px; background: rgba(0,0,0,0.05); color: var(--text); }}
        </style>
    </head>
    <body>
        <header>
            <div class="bg-shape"></div>
            <h1 style="font-size: 2.8rem; font-weight: 900; margin:0;">💙 {SITE_NAME}</h1>
            <p style="font-weight: 700; opacity: 0.9;">ホロライブの魅力をAIで見守る、究極の応援ポータル</p>
        </header>

        <div class="nav-filter">
            <button class="f-btn active" onclick="filter('all')">すべて</button>
            <button class="f-btn" onclick="filter('JP')">JP</button>
            <button class="f-btn" onclick="filter('holoX')">holoX</button>
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
            // カウントダウン更新
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
