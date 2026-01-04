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

# 最下部に移動した「お宝特選コレクション」HTML
FEATURED_FOOTER_HTML = """
<section class="featured-footer">
    <h2 class="footer-section-title">✨ 推しの活動を支える特選アイテム</h2>
    <div class="footer-scroll-container">
        <div class="footer-scroll-track">
            <div class="item-wrap">
                <table border="0" cellpadding="0" cellspacing="0"><tr><td><div style="border:1px solid #95a5a6;border-radius:.75rem;background-color:#FFFFFF;width:504px;margin:10px;padding:5px;text-align:center;overflow:hidden;"><table><tr><td style="width:240px"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-23%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><img src="https://hbb.afl.rakuten.co.jp/hgb/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?me_id=1375600&item_id=10001628&pc=https%3A%2F%2Fthumbnail.image.rakuten.co.jp%2F%400_mall%2Ff082015-mito%2Fcabinet%2F10011667%2Fdw-23-1.jpg%3F_ex%3D240x240&s=240x240&t=picttext" border="0" style="margin:2px" alt="マリンズラム"></a></td><td style="vertical-align:top;width:248px;display: block;"><p style="font-size:12px;line-height:1.4em;text-align:left;margin:0px;padding:2px 6px;word-wrap:break-word"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-23%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener">【ふるさと納税】マリンズラム 宝鐘マリン 珠玉のラム酒</a><br><span>価格：26,000円</span></p><div style="margin:10px;"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-23%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><div style="width:100%;height:27px;background-color:#bf0000;color:#fff;font-size:12px;line-height:27px;border-radius:16px;text-align:center;font-weight:bold;"> 楽天で購入 </div></a></div></td></tr></table></div></td></tr></table>
            </div>
            <div class="item-wrap">
                <table border="0" cellpadding="0" cellspacing="0"><tr><td><div style="border:1px solid #95a5a6;border-radius:.75rem;background-color:#FFFFFF;width:504px;margin:10px;padding:5px;text-align:center;overflow:hidden;"><table><tr><td style="width:240px"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-19%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><img src="https://hbb.afl.rakuten.co.jp/hgb/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?me_id=1375600&item_id=10001383&pc=https%3A%2F%2Fthumbnail.image.rakuten.co.jp%2F%400_mall%2Ff082015-mito%2Fcabinet%2F10011667%2Fdw-19-1.jpg%3F_ex%3D240x240&s=240x240&t=picttext" border="0" style="margin:2px" alt="酔うたい焼き"></a></td><td style="vertical-align:top;width:248px;display: block;"><p style="font-size:12px;line-height:1.4em;text-align:left;margin:0px;padding:2px 6px;word-wrap:break-word"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-19%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener">【ふるさと納税】酔うたい焼き さくらみこすぺしゃる</a><br><span>価格：12,000円</span></p><div style="margin:10px;"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-19%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><div style="width:100%;height:27px;background-color:#bf0000;color:#fff;font-size:12px;line-height:27px;border-radius:16px;text-align:center;font-weight:bold;"> 楽天で購入 </div></a></div></td></tr></table></div></td></tr></table>
            </div>
            </div>
    </div>
</section>
"""
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

    def create_card(v):
        v_id, title = v.get('id'), v.get('title', 'No Title')
        status = v.get('status', 'past')
        raw_start = v.get('start_scheduled') or v.get('start_actual')
        ch = v.get('channel', {})
        raw_ch_name, ch_id = ch.get('name', 'Unknown'), ch.get('id')
        clean_name = super_clean_name(raw_ch_name)
        
        highlight, msg = "注目の配信！", "一緒に応援しましょう！"
        try:
            prompt = f"配信『{title}』の魅力を10文字程度の見出し|15文字の紹介文で書いて。ホロライブ公式のトーンで。"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                highlight, msg = parts[0].strip(), parts[1].strip() if len(parts) > 1 else msg
        except: pass

        badge = '<div class="badge live">LIVE</div>' if status == 'live' else ''
        main_btn = f'<a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn watch">📺 視聴・応援に行く</a>'
        
        if status == 'upcoming' and raw_start:
            badge = '<div class="badge upcoming">配信予定</div>'
            try:
                st_dt = datetime.strptime(raw_start.replace('Z', '')[:19], '%Y-%m-%dT%H:%M:%S')
                st, et = st_dt.strftime('%Y%m%dT%H%M%SZ'), (st_dt + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')
                cal_url = f"https://www.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote('【視聴予約】'+title)}&dates={st}/{et}&details={urllib.parse.quote('出演: '+raw_ch_name)}"
                main_btn = f'<a href="{cal_url}" target="_blank" class="btn reserve">📅 予約 (Google連携)</a>' + main_btn
            except: pass

        share_text = urllib.parse.quote(f"✨{highlight}\n{msg}\n#ホロ応援ナビ #{clean_name}")
        search_query = urllib.parse.quote(clean_name)
        
        return f"""
        <div class="card">
            <div class="thumb-box"><img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" loading="lazy">{badge}</div>
            <div class="card-body">
                <p class="ch-name">👤 {raw_ch_name}</p>
                <h3 class="highlight-txt">{highlight}</h3>
                <div class="quote-box">{msg}</div>
                <div class="actions">
                    {main_btn}
                    <a href="https://twitter.com/intent/tweet?text={share_text}&url={SITE_URL}" target="_blank" class="btn share">📢 布教する</a>
                    <div class="support-grid">
                        <a href="https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}" target="_blank" class="s-link amz">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F" target="_blank" class="s-link rak">楽天</a>
                        <a href="https://www.youtube.com/channel/{ch_id}/join" target="_blank" class="s-link join">メン限</a>
                    </div>
                </div>
            </div>
        </div>"""

    seen_ids = set()
    cards_html = "".join([create_card(v) for v in list_holo if v.get('id') not in seen_ids and not seen_ids.add(v.get('id'))])

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00c2ff; --bg: #f8fafc; --white: #ffffff; }}
            body {{ font-family: 'M PLUS Rounded 1c', sans-serif; background: var(--bg); margin: 0; color: #333; }}
            
            /* --- ロゴを意識したモダンヘッダー --- */
            header {{ 
                background: linear-gradient(135deg, #00c2ff 0%, #0078ff 100%); 
                color: #fff; padding: 60px 20px 80px; text-align: center;
                clip-path: polygon(0 0, 100% 0, 100% 85%, 0 100%);
                border-bottom: 5px solid rgba(255,255,255,0.3);
            }}
            .logo-text {{ font-size: 2.8rem; font-weight: 900; letter-spacing: -1px; margin: 0; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1)); }}
            .logo-sub {{ font-size: 1rem; font-weight: 700; opacity: 0.9; margin-top: 10px; }}

            .container {{ max-width: 1400px; margin: -40px auto 60px; padding: 0 20px; display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 30px; }}
            
            /* カードデザイン */
            .card {{ background: var(--white); border-radius: 32px; overflow: hidden; box-shadow: 0 15px 40px rgba(0,0,0,0.04); transition: 0.3s; display: flex; flex-direction: column; }}
            .card:hover {{ transform: translateY(-12px); box-shadow: 0 20px 60px rgba(0,194,255,0.15); }}
            .thumb-box {{ position: relative; aspect-ratio: 16/9; background:#000; }}
            .thumb-box img {{ width: 100%; height: 100%; object-fit: cover; }}
            .badge {{ position: absolute; top: 15px; right: 15px; padding: 6px 14px; border-radius: 12px; font-size: 11px; font-weight: 900; color: #fff; }}
            .badge.live {{ background: #ff0000; box-shadow: 0 0 15px rgba(255,0,0,0.4); }}
            .badge.upcoming {{ background: #ffb800; }}
            
            .card-body {{ padding: 25px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 11px; color: var(--main); font-weight: 900; margin-bottom: 10px; }}
            .highlight-txt {{ font-size: 1.3rem; font-weight: 900; margin-bottom: 12px; line-height: 1.3; color: #1a202c; }}
            .quote-box {{ background: #f1f5f9; padding: 15px; border-radius: 18px; font-size: 14px; border-left: 6px solid var(--main); margin-bottom: 20px; color: #4a5568; font-weight: 700; }}
            
            /* ボタン */
            .btn {{ display: block; text-decoration: none; text-align: center; padding: 15px; border-radius: 18px; font-weight: 900; font-size: 14px; margin-bottom: 10px; transition: 0.2s; }}
            .btn.watch {{ background: var(--main); color: #fff; }}
            .btn.reserve {{ background: #ffb800; color: #fff; }}
            .btn.share {{ background: #000; color: #fff; }}
            
            .support-grid {{ display: flex; gap: 6px; }}
            .s-link {{ flex: 1; text-decoration: none; font-size: 10px; font-weight: 900; text-align: center; padding: 10px 2px; border-radius: 10px; background: #f1f5f9; color: #475569; border-bottom: 3px solid #cbd5e1; }}

            /* --- 最下部コレクション --- */
            .featured-footer {{ padding: 80px 20px; border-top: 1px solid #e2e8f0; }}
            .footer-section-title {{ text-align: center; font-size: 1.5rem; font-weight: 900; margin-bottom: 40px; color: #1a202c; }}
            .footer-scroll-container {{ overflow-x: auto; padding-bottom: 30px; scrollbar-width: none; }}
            .footer-scroll-track {{ display: flex; gap: 30px; width: max-content; margin: 0 auto; }}
            .item-wrap {{ transition: 0.3s; }}
            .item-wrap:hover {{ transform: scale(1.02); }}
        </style>
    </head>
    <body>
        <header>
            <h1 class="logo-text">💙 {SITE_NAME}</h1>
            <p class="logo-sub">推しの素晴らしさをAIで精査し、全力で応援・支援するポータル</p>
        </header>

        <div class="container">{cards_html}</div>

        {FEATURE_ITEM_SECTION if 'FEATURE_ITEM_SECTION' in locals() else FEATURED_FOOTER_HTML}

        <footer style="text-align: center; padding: 40px; color: #94a3b8; font-size: 12px; font-weight: bold;">
            © 2026 {SITE_NAME} | 推し活を、もっと楽しく。
        </footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__": main()
