import os
import requests
from google import genai
from datetime import datetime, timedelta
import urllib.parse
import re
import time

# ==========================================
# 🌟 応援・支援用設定
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ応援ナビ"
SITE_URL = "https://sakagamiyoshikawa-lang.github.io/my-hololive-bot/" 
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def super_clean_name(raw_name):
    """名前からノイズを削ぎ落とす"""
    name = re.sub(r'(?i)ch\.|channel|\s*-\s*.*|hololive|holoX|holoJP|holoEN|holoID', '', raw_name).strip()
    if re.search(r'[ぁ-んァ-ヶー一-龠]', name):
        name = re.sub(r'[a-zA-Z0-9\s!-/:-@[-`{-~]+', '', name).strip()
    return name if name else raw_name

def fetch_pure_holo():
    """ホロライブ所属メンバーのみを厳格に取得"""
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    combined = []
    # ライブ中と最新ビデオ/予定を取得
    for ep in ["live", "videos"]:
        params = {"org": "Hololive", "limit": 50}
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

    def create_card(v):
        v_id, title = v.get('id'), v.get('title', 'No Title')
        status = v.get('status', 'past')
        raw_start = v.get('start_scheduled') or v.get('start_actual')
        ch = v.get('channel', {})
        raw_ch_name, ch_id = ch.get('name', 'Unknown'), ch.get('id')
        
        clean_name = super_clean_name(raw_ch_name)
        
        # AI分析（短く熱く）
        highlight, msg = "注目の配信！", "みんなで応援しましょう！"
        try:
            prompt = f"配信『{title}』の魅力を10文字程度の見出し|15文字の紹介文で書いて。"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                highlight, msg = parts[0].strip(), parts[1].strip() if len(parts) > 1 else msg
        except: pass

        # ボタン・バッジ生成
        badge = '<div class="badge live">LIVE中</div>' if status == 'live' else ''
        main_btn = f'<a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn watch">📺 視聴・応援に行く</a>'
        
        if status == 'upcoming' and raw_start:
            badge = '<div class="badge upcoming">配信予定</div>'
            try:
                # 日時フォーマット変換
                st_dt = datetime.strptime(raw_start.replace('Z', '')[:19], '%Y-%m-%dT%H:%M:%S')
                st = st_dt.strftime('%Y%m%dT%H%M%SZ')
                et = (st_dt + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')
                
                # --- カレンダータイトルの修正 ---
                cal_title = urllib.parse.quote(f"【視聴予約】{title}")
                cal_details = urllib.parse.quote(f"出演: {raw_ch_name}\n視聴URL: https://www.youtube.com/watch?v={v_id}\n\n(ホロ応援ナビより予約)")
                
                cal_url = f"https://www.google.com/calendar/render?action=TEMPLATE&text={cal_title}&dates={st}/{et}&details={cal_details}"
                main_btn = f'<a href="{cal_url}" target="_blank" class="btn reserve">📅 予約 (Googleカレンダー)</a>' + main_btn
            except: pass

        share_text = urllib.parse.quote(f"✨{highlight}\n{msg}\n#ホロライブ応援ナビ #{clean_name}")
        search_query = urllib.parse.quote(clean_name)
        
        return f"""
        <div class="card">
            <div class="thumb-box">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" loading="lazy">
                {badge}
            </div>
            <div class="card-body">
                <p class="ch-name">👤 {raw_ch_name}</p>
                <h3 class="highlight-txt">{highlight}</h3>
                <div class="quote-box">{msg}</div>
                <div class="actions">
                    {main_btn}
                    <a href="https://twitter.com/intent/tweet?text={share_text}&url={SITE_URL}" target="_blank" class="btn share">📢 この配信を布教する</a>
                    <div class="support-grid">
                        <a href="https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}" target="_blank" class="s-link amz">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F" target="_blank" class="s-link rak">楽天市場</a>
                        <a href="https://www.youtube.com/channel/{ch_id}/join" target="_blank" class="s-link join">メン限</a>
                    </div>
                </div>
            </div>
        </div>"""

    seen_ids = set()
    cards_html = "".join([create_card(v) for v in list_holo if v.get('id') not in seen_ids and not seen_ids.add(v.get('id'))])

    if not cards_html:
        cards_html = "<p class='empty-msg'>現在データを精査中です。しばらくお待ちください。</p>"

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00c2ff; --bg: #f0f4f8; --card: #fff; }}
            body {{ font-family: 'M PLUS Rounded 1c', sans-serif; background: var(--bg); margin: 0; padding-bottom: 50px; }}
            header {{ background: linear-gradient(135deg, #00c2ff, #0078ff); color: #fff; padding: 60px 20px; text-align: center; clip-path: polygon(0 0, 100% 0, 100% 85%, 0 100%); }}
            h1 {{ margin: 0; font-size: 2.5rem; font-weight: 900; }}
            .container {{ max-width: 1400px; margin: -30px auto 0; padding: 0 20px; display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 30px; }}
            .card {{ background: var(--card); border-radius: 30px; overflow: hidden; box-shadow: 0 15px 35px rgba(0,0,0,0.05); display: flex; flex-direction: column; transition: 0.3s; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 50px rgba(0,194,255,0.15); }}
            .thumb-box {{ position: relative; aspect-ratio: 16/9; background:#000; }}
            .thumb-box img {{ width: 100%; height: 100%; object-fit: cover; }}
            .badge {{ position: absolute; top: 15px; right: 15px; padding: 6px 15px; border-radius: 12px; font-size: 11px; font-weight: 900; color: #fff; }}
            .badge.live {{ background: #ff0000; animation: pulse 1s infinite; }}
            .badge.upcoming {{ background: #ffb800; }}
            @keyframes pulse {{ 0%, 100% {{opacity: 1;}} 50% {{opacity: 0.7;}} }}
            .card-body {{ padding: 25px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 11px; color: var(--main); font-weight: 900; margin: 0 0 10px; }}
            .highlight-txt {{ font-size: 1.4rem; font-weight: 900; margin: 0 0 12px; line-height: 1.2; }}
            .quote-box {{ background: #f8fafc; padding: 15px; border-radius: 18px; font-size: 14px; border-left: 5px solid var(--main); margin-bottom: 20px; }}
            .btn {{ display: block; text-decoration: none; text-align: center; padding: 14px; border-radius: 18px; font-weight: 900; font-size: 14px; margin-bottom: 10px; transition: 0.2s; }}
            .btn.watch {{ background: var(--main); color: #fff; }}
            .btn.reserve {{ background: #ffb800; color: #fff; }}
            .btn.share {{ background: #000; color: #fff; }}
            .support-grid {{ display: flex; gap: 8px; margin-top: 10px; }}
            .s-link {{ flex: 1; text-decoration: none; font-size: 10px; font-weight: 900; text-align: center; padding: 10px 2px; border-radius: 10px; background: #f1f5f9; color: #475569; }}
            .s-link.amz {{ border-bottom: 3px solid #ff9900; }}
            .s-link.rak {{ border-bottom: 3px solid #bf0000; }}
            .s-link.join {{ border-bottom: 3px solid #00c2ff; }}
            footer {{ text-align: center; padding: 80px 20px; color: #a0aec0; font-size: 12px; }}
        </style>
    </head>
    <body>
        <header><h1>💙 {SITE_NAME}</h1><p>推しの活動をAIで見守り、全力で布教・支援する応援ポータル</p></header>
        <div class="container">{cards_html}</div>
        <footer>© 2026 {SITE_NAME} | 非公式応援プロジェクト</footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__": main()
