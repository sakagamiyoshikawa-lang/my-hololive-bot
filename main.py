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
SITE_URL = "https://sakagamiyoshikawa-lang.github.io/my-hololive-bot/" 
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def super_clean_name(raw_name):
    """名前からノイズを削ぎ落とし、言語を一本化する"""
    name = re.sub(r'(?i)ch\.|channel|\s*-\s*.*|hololive|holoX|holoJP|holoEN|holoID', '', raw_name).strip()
    has_japanese = re.search(r'[ぁ-んァ-ヶー一-龠]', name)
    if has_japanese:
        name = re.sub(r'[a-zA-Z0-9\s!-/:-@[-`{-~]+', '', name).strip()
    return name if name else raw_name

def fetch_strict(org_id):
    """指定した組織のみを厳格に取得する（外部混入をブロック）"""
    url_live = "https://holodex.net/api/v2/live"
    url_videos = "https://holodex.net/api/v2/videos"
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    combined_data = []
    for url in [url_live, url_videos]:
        params = {"org": org_id, "limit": 40}
        if "videos" in url:
            params.update({"sort": "view_count", "order": "desc", "type": "stream"})
        try:
            res = requests.get(url, params=params, headers=headers, timeout=20)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    # 【重要】チャンネルの所属組織が一致するものだけを厳選
                    for v in data:
                        if v.get('channel', {}).get('org') == org_id:
                            combined_data.append(v)
            time.sleep(1) # API負荷軽減
        except: pass
    return combined_data

def main():
    # 1. 組織別に厳格なリストを作成
    list_holo = fetch_strict("Hololive")
    list_stars = fetch_strict("Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    def create_card(v, org_label):
        if not isinstance(v, dict) or not v.get('id'): return ""
        v_id, title = v.get('id'), v.get('title', 'No Title')
        status = v.get('status', 'past')
        ch = v.get('channel', {})
        raw_ch_name = ch.get('name', 'Unknown')
        ch_id = ch.get('id')
        
        clean_name = super_clean_name(raw_ch_name)
        
        # AI分析（短くインパクト重視）
        highlight, msg = "必見の配信！", "みんなで応援しましょう！"
        try:
            prompt = f"配信タイトル『{title}』の魅力をファン目線で要約して。形式: 見出し(12字)|紹介文(20字)"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                highlight = parts[0].strip()
                msg = parts[1].strip() if len(parts) > 1 else msg
        except: pass

        share_text = urllib.parse.quote(f"✨{highlight}\n{msg}\n#ホロライブ応援ナビ #{clean_name}")
        share_url = f"https://twitter.com/intent/tweet?text={share_text}&url={SITE_URL}"
        search_query = urllib.parse.quote(clean_name)
        
        live_html = '<div class="live-badge">LIVE</div>' if status == 'live' else ''
        
        return f"""
        <div class="card">
            <div class="thumb">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" alt="thumbnail" loading="lazy">
                {live_html}
                <div class="tag-box">{org_label}</div>
            </div>
            <div class="card-info">
                <div class="liver-name">👤 {raw_ch_name}</div>
                <div class="catchphrase">{highlight}</div>
                <div class="desc">{msg}</div>
                <div class="action-area">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="main-btn">応援（視聴）する</a>
                    <a href="{share_url}" target="_blank" class="share-btn">📢 布教する</a>
                    <div class="support-label">ライバーの活動を直接支援</div>
                    <div class="support-links">
                        <a href="https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}" target="_blank" class="s-link amz">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F" target="_blank" class="s-link rak">楽天市場</a>
                        <a href="https://www.youtube.com/channel/{ch_id}/join" target="_blank" class="s-link join">メン限</a>
                    </div>
                </div>
            </div>
        </div>"""

    def build_grid(v_list, label):
        seen, html = set(), ""
        for v in v_list:
            v_id = v.get('id')
            if v_id and v_id not in seen:
                html += create_card(v, label)
                seen.add(v_id)
        return html if html else "<p class='empty-msg'>現在データ準備中です。リロードしてみてください。</p>"

    content_holo = build_grid(list_holo, "Hololive")
    content_stars = build_grid(list_stars, "Holostars")

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00c2ff; --stars: #ffb800; --bg: #f5f8fa; --card-bg: #ffffff; }}
            body {{ font-family: 'M PLUS Rounded 1c', sans-serif; background: var(--bg); margin: 0; color: #333; }}
            header {{ background: linear-gradient(135deg, #00c2ff, #0078ff); color: #fff; padding: 60px 20px; text-align: center; clip-path: polygon(0 0, 100% 0, 100% 85%, 0 100%); }}
            h1 {{ margin: 0; font-size: 2.2rem; font-weight: 900; letter-spacing: 1px; }}
            header p {{ margin-top: 10px; font-weight: bold; opacity: 0.9; }}
            
            .container {{ max-width: 1300px; margin: -40px auto 60px; padding: 0 20px; }}
            .nav-tabs {{ display: flex; justify-content: center; gap: 15px; margin-bottom: 40px; }}
            .tab-btn {{ padding: 15px 40px; border: none; background: #fff; border-radius: 50px; font-weight: 900; color: #718096; cursor: pointer; box-shadow: 0 10px 20px rgba(0,0,0,0.05); transition: 0.3s; }}
            .tab-btn.active {{ background: var(--main); color: #fff; transform: translateY(-3px); }}
            .tab-btn.stars.active {{ background: var(--stars); }}

            .grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 25px; }}
            .grid.active {{ display: grid; }}

            .card {{ background: var(--card-bg); border-radius: 24px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.03); transition: 0.3s; display: flex; flex-direction: column; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,0,0,0.08); }}
            .thumb {{ position: relative; aspect-ratio: 16/9; }}
            .thumb img {{ width: 100%; height: 100%; object-fit: cover; }}
            .live-badge {{ position: absolute; top: 15px; right: 15px; background: #ff0000; color: #fff; padding: 5px 12px; border-radius: 8px; font-size: 11px; font-weight: bold; animation: blink 1.2s infinite; }}
            @keyframes blink {{ 0% {{opacity: 1;}} 50% {{opacity: 0.6;}} 100% {{opacity: 1;}} }}
            .tag-box {{ position: absolute; top: 15px; left: 15px; background: rgba(0,0,0,0.6); color: #fff; padding: 5px 12px; border-radius: 8px; font-size: 10px; font-weight: bold; }}

            .card-info {{ padding: 25px; flex-grow: 1; display: flex; flex-direction: column; }}
            .liver-name {{ font-size: 11px; color: var(--main); font-weight: 900; margin-bottom: 10px; }}
            .catchphrase {{ font-size: 1.2rem; font-weight: 900; line-height: 1.3; margin-bottom: 10px; }}
            .desc {{ font-size: 13px; color: #4a5568; line-height: 1.5; margin-bottom: 20px; padding: 12px; background: #f8fafc; border-radius: 12px; border-left: 4px solid var(--main); }}
            
            .action-area {{ margin-top: auto; }}
            .main-btn {{ display: block; text-decoration: none; background: var(--main); color: #fff; text-align: center; padding: 14px; border-radius: 14px; font-weight: 900; margin-bottom: 10px; }}
            .share-btn {{ display: block; text-decoration: none; background: #000; color: #fff; text-align: center; padding: 10px; border-radius: 14px; font-size: 12px; font-weight: bold; margin-bottom: 20px; }}
            .support-label {{ font-size: 10px; color: #a0aec0; text-align: center; font-weight: bold; margin-bottom: 10px; }}
            .support-links {{ display: flex; gap: 6px; }}
            .s-link {{ flex: 1; text-decoration: none; font-size: 10px; font-weight: bold; text-align: center; padding: 8px 2px; border-radius: 8px; background: #f1f5f9; color: #4a5568; }}
            .s-link.amz {{ border-bottom: 2px solid #ff9900; }}
            .s-link.rak {{ border-bottom: 2px solid #bf0000; }}

            footer {{ text-align: center; padding: 80px 20px; color: #a0aec0; font-size: 12px; }}
            .empty-msg {{ grid-column: 1/-1; text-align: center; padding: 50px; color: #a0aec0; font-weight: bold; }}
        </style>
        <script>
            function tab(id) {{
                document.querySelectorAll('.grid').forEach(g => g.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.getElementById(id).classList.add('active');
                document.getElementById('btn-' + id).classList.add('active');
            }}
        </script>
    </head>
    <body onload="tab('holo')">
        <header>
            <h1>💙 {SITE_NAME}</h1>
            <p>推しの魅力をAIで精査。布教と支援のためのファンポータル</p>
        </header>
        <div class="container">
            <div class="nav-tabs">
                <button id="btn-holo" class="tab-btn active" onclick="tab('holo')">Hololive</button>
                <button id="btn-stars" class="tab-btn stars" onclick="tab('stars')">Holostars</button>
            </div>
            <div id="holo" class="grid active">{content_holo}</div>
            <div id="stars" class="grid">{content_stars}</div>
        </div>
        <footer>
            © 2026 {SITE_NAME} | 非公式応援プロジェクト
        </footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    main()
