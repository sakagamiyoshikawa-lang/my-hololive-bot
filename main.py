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
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def clean_name_logic(raw_name):
    """プログラムでノイズを物理的に除去する (風真いろは ch. -> 風真いろは)"""
    # ch., Ch., -, hololive, holoX などのノイズを正規表現で除去
    name = re.sub(r'(?i)ch\.|channel|\s*-\s*.*|hololive|holoX|holoJP|holoEN|holoID', '', raw_name)
    return name.strip()

def fetch_data(endpoint, org):
    url = f"https://holodex.net/api/v2/{endpoint}"
    params = {"org": org, "limit": 40}
    if endpoint == "videos":
        params.update({"sort": "published_at", "order": "desc", "type": "clip,stream"})
    
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
        ch = v.get('channel', {})
        raw_ch_name = ch.get('name', 'Unknown')
        
        # 1. まずプログラムで物理的に名前を掃除する (これが検索用)
        base_clean_name = clean_name_logic(raw_ch_name)
        
        # 2. AIで見どころと「より自然な名前」を抽出
        highlight, msg = "見どころ満載の配信！", "みんなで視聴して応援しよう！"
        display_name = base_clean_name
        
        try:
            prompt = f"チャンネル名『{raw_ch_name}』から個人名のみ抽出して。また配信『{title}』の応援見出しと応援文を日本語で作って。形式: 名前|見出し(12字)|応援文(20字)"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                if len(parts) >= 3:
                    display_name = parts[0].strip()
                    highlight = parts[1].strip()
                    msg = parts[2].strip()
        except: pass

        # 検索用には「AIの結果」よりも「プログラムで削った確実な名前」を優先（失敗防止）
        search_query = urllib.parse.quote(base_clean_name)
        
        return f"""
        <div class="card">
            <div class="thumb-box">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" loading="lazy" onerror="this.src='https://placehold.jp/24/00c2ff/ffffff/320x180.png?text=Preview'">
                <div class="org-tag">{org_tag}</div>
            </div>
            <div class="info">
                <div class="ch-name">👤 {raw_ch_name}</div>
                <div class="highlight">✨ {highlight}</div>
                <div class="v-title">{title}</div>
                <div class="ai-msg">💬 {msg}</div>
                <div class="actions">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn-main">今すぐ応援（視聴）</a>
                    <div class="support-text">＼ {display_name}さんの活動を支援 ／</div>
                    <div class="merch-links">
                        <a href="https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}" target="_blank" class="btn-sub amz">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F" target="_blank" class="btn-sub rak">楽天市場</a>
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
        return html if html else "<p class='error-msg'>現在ライブ・新着データがありません。更新を待っています。</p>"

    content_holo = build_content(list_holo, "Hololive")
    content_stars = build_content(list_stars, "Holostars")

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <style>
            :root {{ --holo: #00c2ff; --bg: #f8fafc; --text: #1e293b; --sub: #64748b; }}
            body {{ font-family: sans-serif; background: var(--bg); color: var(--text); margin: 0; }}
            header {{ background: #fff; padding: 40px 20px; text-align: center; border-bottom: 3px solid var(--holo); }}
            h1 {{ margin: 0; font-size: 1.8rem; color: var(--holo); font-weight: 900; }}
            .motto {{ font-size: 0.85rem; color: var(--sub); margin-top: 10px; font-weight: bold; }}
            .container {{ max-width: 1200px; margin: 30px auto; padding: 0 15px; }}
            .tabs {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 30px; }}
            .tab-btn {{ padding: 12px 25px; border: none; background: #fff; border-radius: 50px; font-weight: 900; color: var(--sub); cursor: pointer; }}
            .tab-btn.active {{ background: var(--holo); color: #fff; }}
            .grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 25px; }}
            .grid.active {{ display: grid; }}
            .card {{ background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 16px rgba(0,0,0,0.04); display: flex; flex-direction: column; }}
            .thumb-box {{ position: relative; aspect-ratio: 16/9; background:#000; }}
            .thumb-box img {{ width: 100%; height: 100%; object-fit: cover; }}
            .org-tag {{ position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.7); color: #fff; padding: 4px 10px; border-radius: 8px; font-size: 10px; font-weight: bold; }}
            .info {{ padding: 20px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 11px; color: var(--sub); margin-bottom: 8px; }}
            .highlight {{ font-size: 1.1rem; font-weight: 900; margin-bottom: 8px; }}
            .v-title {{ font-size: 13px; color: var(--sub); height: 2.8em; overflow: hidden; margin-bottom: 15px; }}
            .ai-msg {{ background: #f0f9ff; padding: 12px; border-radius: 10px; font-size: 13px; font-weight: bold; border-left: 4px solid var(--holo); margin-bottom: 20px; }}
            .actions {{ margin-top: auto; padding-top: 15px; border-top: 1px solid #f1f5f9; }}
            .btn-main {{ display: block; text-decoration: none; background: var(--holo); color: #fff; text-align: center; padding: 12px; border-radius: 10px; font-weight: 900; margin-bottom: 15px; }}
            .support-text {{ font-size: 10px; color: var(--sub); text-align: center; margin-bottom: 8px; font-weight: bold; }}
            .merch-links {{ display: flex; gap: 5px; }}
            .btn-sub {{ flex: 1; text-decoration: none; background: #f8fafc; color: var(--sub); text-align: center; padding: 8px; border-radius: 8px; font-size: 11px; font-weight: bold; border: 1px solid #e2e8f0; }}
            .amz {{ border-bottom: 3px solid #ff9900; }}
            .rak {{ border-bottom: 3px solid #bf0000; }}
            .error-msg {{ grid-column: 1/-1; text-align: center; padding: 50px; color: var(--sub); font-weight: bold; }}
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
            <div class="motto">推しの素晴らしさを広め、みんなで活動を支援する</div>
        </header>
        <div class="container">
            <div class="tabs">
                <button id="btn-holo" class="tab-btn active" onclick="tab('holo')">Hololive</button>
                <button id="btn-stars" class="tab-btn" onclick="tab('stars')">Holostars</button>
            </div>
            <div id="holo" class="grid active">{content_holo}</div>
            <div id="stars" class="grid">{content_stars}</div>
        </div>
        <footer style="text-align: center; padding: 60px; font-size: 12px; color: #94a3b8;">© 2026 {SITE_NAME}</footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    main()
