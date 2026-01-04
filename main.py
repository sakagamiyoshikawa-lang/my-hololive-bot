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

def super_clean_name(raw_name):
    """
    プログラム側で強制的に名前を一本化するロジック。
    日本語があれば英語を消し、なければノイズだけを消す。
    """
    # ch. や hololive などの共通ノイズを消去
    name = re.sub(r'(?i)ch\.|channel|\s*-\s*.*|hololive|holoX|holoJP|holoEN|holoID', '', raw_name).strip()
    
    # 日本語が含まれているかチェック
    has_japanese = re.search(r'[ぁ-んァ-ヶー一-龠]', name)
    if has_japanese:
        # 日本語がある場合、英数字を消して日本語だけ残す（例: Iroha 風真いろは -> 風真いろは）
        name = re.sub(r'[a-zA-Z0-9]+', '', name).strip()
    
    return name if name else raw_name

def fetch_data(endpoint, org):
    url = f"https://holodex.net/api/v2/{endpoint}"
    params = {"org": org, "limit": 40}
    if endpoint == "videos":
        params.update({"sort": "published_at", "order": "desc", "type": "clip,stream"})
    
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    try:
        res = requests.get(url, params=params, headers=headers, timeout=20)
        return res.json() if res.status_code == 200 else []
    except:
        return []

def main():
    # 1. 多角的なデータ取得
    list_holo = fetch_data("live", "Hololive") + fetch_data("videos", "Hololive")
    time.sleep(1)
    list_stars = fetch_data("live", "Holostars") + fetch_data("videos", "Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    def create_card(v, org_tag):
        if not isinstance(v, dict) or not v.get('id'): return ""
        v_id, title = v.get('id'), v.get('title', 'No Title')
        ch = v.get('channel', {})
        raw_ch_name = ch.get('name', 'Unknown')
        
        # 検索ワードの最適化
        clean_name = super_clean_name(raw_ch_name)
        
        highlight, msg = "注目の配信！", "一緒に視聴して応援しましょう！"
        try:
            prompt = f"配信タイトル『{title}』から推しポイントを分析して。形式: 見出し(12字)|応援文(20字)"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                highlight = parts[0].strip()
                msg = parts[1].strip() if len(parts) > 1 else msg
        except: pass

        search_query = urllib.parse.quote(clean_name)
        
        return f"""
        <div class="card">
            <div class="thumb-box">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" loading="lazy" onerror="this.src='https://placehold.jp/24/00c2ff/ffffff/320x180.png?text=Hololive'">
                <div class="org-tag">{org_tag}</div>
            </div>
            <div class="info">
                <div class="ch-name">👤 {raw_ch_name}</div>
                <div class="highlight">✨ {highlight}</div>
                <div class="v-title">{title}</div>
                <div class="ai-msg">💬 {msg}</div>
                <div class="actions">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn-main">今すぐ応援（視聴）</a>
                    <div class="support-text">＼ {clean_name}さんの活動を支援 ／</div>
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
            v_id = v.get('id') if isinstance(v, dict) else None
            if v_id and v_id not in seen:
                html += create_card(v, tag)
                seen.add(v_id)
        return html if html else "<p style='grid-column:1/-1;text-align:center;padding:50px;'>ただいま応援データを準備中です...</p>"

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
            .highlight {{ font-size: 1.1rem; font-weight: 900; margin-bottom: 8px; }}
            .v-title {{ font-size: 13px; color: var(--sub); height: 2.8em; overflow: hidden; margin-bottom: 15px; line-height: 1.4; }}
            .ai-msg {{ background: #f0f9ff; padding: 12px; border-radius: 10px; font-size: 13px; font-weight: bold; border-left: 4px solid var(--holo); margin-bottom: 20px; }}
            .btn-main {{ display: block; text-decoration: none; background: var(--holo); color: #fff; text-align: center; padding: 12px; border-radius: 10px; font-weight: 900; margin-bottom: 15px; }}
            .merch-links {{ display: flex; gap: 5px; }}
            .btn-sub {{ flex: 1; text-decoration: none; background: #f8fafc; color: var(--sub); text-align: center; padding: 8px; border-radius: 8px; font-size: 11px; font-weight: bold; border: 1px solid #e2e8f0; }}
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
            <div style="font-size: 0.85rem; color: var(--sub); margin-top: 10px; font-weight: bold;">推しの素晴らしさを再発見し、活動を支援するファンポータル</div>
        </header>
        <div class="container">
            <div class="tabs">
                <button id="btn-holo" class="tab-btn active" onclick="tab('holo')">Hololive</button>
                <button id="btn-stars" class="tab-btn" onclick="tab('stars')">Holostars</button>
            </div>
            <div id="holo" class="grid active">{content_holo}</div>
            <div id="stars" class="grid">{content_stars}</div>
        </div>
        <footer style="text-align: center; padding: 40px; font-size: 12px; color: #94a3b8;">© 2026 {SITE_NAME}</footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    main()
