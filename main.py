import os
import requests
from google import genai
from datetime import datetime
import urllib.parse
import re
import time

# ==========================================
# 🌟 応援・支援用設定
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロライブ応援ナビ"
SITE_URL = "https://sakagamiyoshikawa-lang.github.io/my-hololive-bot/" # 自分のURL
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def super_clean_name(raw_name):
    name = re.sub(r'(?i)ch\.|channel|\s*-\s*.*|hololive|holoX|holoJP|holoEN|holoID', '', raw_name).strip()
    has_japanese = re.search(r'[ぁ-んァ-ヶー一-龠]', name)
    if has_japanese:
        name = re.sub(r'[a-zA-Z0-9\s!-/:-@[-`{-~]+', '', name).strip()
    return name if name else raw_name

def fetch_data(endpoint, org):
    url = f"https://holodex.net/api/v2/{endpoint}"
    params = {"org": org, "limit": 30}
    if endpoint == "videos":
        params.update({"sort": "view_count", "order": "desc", "type": "stream"})
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    try:
        res = requests.get(url, params=params, headers=headers, timeout=20)
        return res.json() if res.status_code == 200 else []
    except: return []

def main():
    list_holo = fetch_data("live", "Hololive") + fetch_data("videos", "Hololive")
    time.sleep(1)
    list_stars = fetch_data("live", "Holostars") + fetch_data("videos", "Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    def create_card(v, org_tag):
        if not isinstance(v, dict) or not v.get('id'): return ""
        v_id, title = v.get('id'), v.get('title', 'No Title')
        status = v.get('status', 'past')
        ch = v.get('channel', {})
        raw_ch_name = ch.get('name', 'Unknown')
        ch_id = ch.get('id')
        
        clean_name = super_clean_name(raw_ch_name)
        
        highlight, msg = "必見の配信！", "みんなで応援しましょう！"
        try:
            prompt = f"タイトル『{title}』の魅力をファン目線で要約して。形式: 見出し(12字)|紹介文(20字)"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                highlight = parts[0].strip()
                msg = parts[1].strip() if len(parts) > 1 else msg
        except: pass

        # SNSシェア用の文章作成
        share_text = urllib.parse.quote(f"✨{highlight}\n{msg}\n#ホロライブ応援ナビ #{clean_name}")
        share_url = f"https://twitter.com/intent/tweet?text={share_text}&url={SITE_URL}"
        
        search_query = urllib.parse.quote(clean_name)
        live_badge = '<span class="badge live">LIVE</span>' if status == 'live' else ''
        
        return f"""
        <div class="card">
            <div class="thumb-box">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" loading="lazy">
                {live_badge}
                <div class="org-tag">{org_tag}</div>
            </div>
            <div class="info">
                <div class="ch-name">👤 {raw_ch_name}</div>
                <div class="highlight">{highlight}</div>
                <div class="ai-msg">💬 {msg}</div>
                
                <div class="actions">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn-main">配信を視聴・応援</a>
                    <a href="{share_url}" target="_blank" class="btn-share">📢 この尊さを布教する</a>
                    
                    <div class="support-section">
                        <p class="section-title">活動を直接支援する</p>
                        <div class="support-grid">
                            <a href="https://www.youtube.com/channel/{ch_id}/join" target="_blank" class="s-link">メン限</a>
                            <a href="https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}" target="_blank" class="s-link amz">Amazon</a>
                            <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F" target="_blank" class="s-link rak">楽天</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>"""

    def build_content(v_list, tag):
        seen, html = set(), ""
        for v in v_list:
            if isinstance(v, dict) and v.get('id') not in seen:
                html += create_card(v, tag)
                seen.add(v.get('id'))
        return html if html else "<p class='error-msg'>データ取得中...</p>"

    content_holo = build_content(list_holo, "Hololive")
    content_stars = build_content(list_stars, "Holostars")

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --holo: #00c2ff; --stars: #ffb800; --bg: #f0f4f8; --card: #ffffff; --txt: #2d3748; }}
            body {{ font-family: 'M PLUS Rounded 1c', sans-serif; background: var(--bg); color: var(--txt); margin: 0; }}
            
            header {{ background: linear-gradient(135deg, var(--holo), #0077ff); color: white; padding: 60px 20px; text-align: center; clip-path: polygon(0 0, 100% 0, 100% 85%, 0 100%); }}
            header h1 {{ margin: 0; font-size: 2.5rem; font-weight: 900; letter-spacing: 2px; text-shadow: 2px 2px 10px rgba(0,0,0,0.2); }}
            header p {{ opacity: 0.9; font-weight: bold; margin-top: 10px; }}

            .container {{ max-width: 1300px; margin: -40px auto 40px; padding: 0 20px; }}
            .nav {{ display: flex; justify-content: center; gap: 15px; margin-bottom: 40px; }}
            .nav-btn {{ padding: 15px 40px; border: none; background: white; border-radius: 50px; font-weight: 900; color: #718096; cursor: pointer; box-shadow: 0 10px 20px rgba(0,0,0,0.1); transition: 0.3s; }}
            .nav-btn.active {{ background: var(--holo); color: white; transform: scale(1.05); }}

            .grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 30px; }}
            .grid.active {{ display: grid; }}

            .card {{ background: var(--card); border-radius: 24px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05); transition: 0.3s; display: flex; flex-direction: column; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,0,0,0.1); }}
            
            .thumb-box {{ position: relative; aspect-ratio: 16/9; }}
            .thumb-box img {{ width: 100%; height: 100%; object-fit: cover; }}
            .badge {{ position: absolute; top: 15px; right: 15px; background: #ff0000; color: white; padding: 5px 12px; border-radius: 8px; font-size: 12px; font-weight: bold; animation: pulse 1.5s infinite; }}
            @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.6; }} 100% {{ opacity: 1; }} }}
            .org-tag {{ position: absolute; top: 15px; left: 15px; background: rgba(0,0,0,0.6); color: white; padding: 5px 12px; border-radius: 8px; font-size: 10px; font-weight: bold; }}

            .info {{ padding: 25px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 12px; color: var(--holo); font-weight: 900; margin-bottom: 10px; }}
            .highlight {{ font-size: 1.3rem; font-weight: 900; line-height: 1.3; margin-bottom: 10px; }}
            .ai-msg {{ font-size: 14px; color: #4a5568; line-height: 1.5; margin-bottom: 20px; padding: 15px; background: #f8fafc; border-radius: 15px; border-left: 5px solid var(--holo); }}

            .actions {{ margin-top: auto; }}
            .btn-main {{ display: block; text-decoration: none; background: var(--holo); color: white; text-align: center; padding: 15px; border-radius: 15px; font-weight: 900; margin-bottom: 10px; transition: 0.2s; }}
            .btn-share {{ display: block; text-decoration: none; background: #000; color: white; text-align: center; padding: 12px; border-radius: 15px; font-size: 13px; font-weight: bold; margin-bottom: 20px; }}
            
            .support-section {{ border-top: 2px dashed #edf2f7; padding-top: 20px; }}
            .section-title {{ font-size: 11px; text-align: center; color: #a0aec0; font-weight: bold; margin-bottom: 12px; }}
            .support-grid {{ display: flex; gap: 8px; }}
            .s-link {{ flex: 1; text-decoration: none; text-align: center; padding: 10px 5px; border-radius: 10px; font-size: 11px; font-weight: bold; background: #f1f5f9; color: #4a5568; }}
            .s-link.amz {{ border-bottom: 3px solid #ff9900; }}
            .s-link.rak {{ border-bottom: 3px solid #bf0000; }}

            footer {{ text-align: center; padding: 80px 20px; color: #a0aec0; font-size: 14px; }}
        </style>
        <script>
            function tab(id) {{
                document.querySelectorAll('.grid').forEach(g => g.classList.remove('active'));
                document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
                document.getElementById(id).classList.add('active');
                document.getElementById('btn-' + id).classList.add('active');
            }}
        </script>
    </head>
    <body onload="tab('holo')">
        <header>
            <h1>💙 {SITE_NAME}</h1>
            <p>AIが魅力を精査。推しを広め、活動を支える応援ポータル</p>
        </header>
        <div class="container">
            <div class="nav">
                <button id="btn-holo" class="nav-btn active" onclick="tab('holo')">Hololive</button>
                <button id="btn-stars" class="nav-btn" onclick="tab('stars')">Holostars</button>
            </div>
            <div id="holo" class="grid active">{content_holo}</div>
            <div id="stars" class="grid">{content_stars}</div>
        </div>
        <footer>
            <p>© 2026 {SITE_NAME} | 非公式応援プロジェクト</p>
            <p style="font-size: 10px;">当サイトはAIを用いて情報を整理しています。最新の公式情報は各チャンネルをご確認ください。</p>
        </footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    main()
