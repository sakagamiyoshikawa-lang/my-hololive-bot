import os
import requests
from google import genai
from datetime import datetime
import urllib.parse
import time

# ==========================================
# 🌟 設定済みアフィリエイトID
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ推しグッズNAVI"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_data(org_name):
    """ライブ中・予約枠から、今まさに話題のライバーを取得"""
    url = "https://holodex.net/api/v2/live"
    params = {"org": org_name, "limit": 40}
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    try:
        res = requests.get(url, params=params, headers=headers, timeout=20)
        if res.status_code == 200:
            data = res.json()
            return (data if isinstance(data, list) else []), "Success"
        return [], f"Status: {res.status_code}"
    except:
        return [], "Connection Error"

def main():
    list_holo, _ = fetch_data("Hololive")
    time.sleep(1)
    list_stars, _ = fetch_data("Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    def make_merch_card(v, org_label):
        if not v or not isinstance(v, dict): return ""
        v_id = v.get('id')
        title = v.get('title', 'No Title')
        channel = v.get('channel', {})
        ch_name = channel.get('name', 'Unknown')
        
        # AIが「今このライバーで買うべきもの」を提案
        merch_rec = "公式フィギュア・限定グッズ"
        catchphrase = "推しの最新アイテムをチェック！"
        try:
            prompt = f"このライバー '{ch_name}' のファンが欲しがりそうなグッズジャンル（フィギュア、ぬいぐるみ、等）を1つ選び、15文字以内の購入を促すキャッチコピーを作って。書式: ジャンル|コピー"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                merch_rec = parts[0].strip()
                catchphrase = parts[1].strip() if len(parts) > 1 else catchphrase
        except: pass

        query = urllib.parse.quote(f"{ch_name} グッズ")
        
        return f"""
        <div class="shop-card">
            <div class="image-area">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" loading="lazy">
                <div class="merch-tag">おすすめ: {merch_rec}</div>
            </div>
            <div class="shop-info">
                <div class="liver-name">👤 {ch_name}</div>
                <div class="ai-catch">{catchphrase}</div>
                <div class="v-ref">配信: {title[:30]}...</div>
                <div class="shop-links">
                    <a href="https://www.amazon.co.jp/s?k={query}&tag={AMAZON_ID}" target="_blank" class="s-btn amz">Amazonでお宝検索</a>
                    <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{query}%2F" target="_blank" class="s-btn rak">楽天ポイントでお得に</a>
                </div>
                <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="watch-link">▶ 配信を視聴する</a>
            </div>
        </div>
        """

    content_holo = "".join([make_merch_card(v, "ホロライブ") for v in list_holo])
    content_stars = "".join([make_merch_card(v, "ホロスターズ") for v in list_stars])

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00b5d8; --sub: #ff66b2; --amz: #ff9900; --rak: #bf0000; --bg: #fdfdfd; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--bg); color: #333; margin: 0; }}
            header {{ background: #fff; border-bottom: 2px solid #eee; padding: 20px; text-align: center; position: sticky; top: 0; z-index: 100; }}
            h1 {{ margin: 0; font-size: 1.5rem; color: var(--main); font-weight: 900; }}
            .subtitle {{ font-size: 0.8rem; color: #666; margin-top: 5px; }}
            
            .container {{ max-width: 1200px; margin: 20px auto; padding: 0 15px; }}
            .nav-tabs {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }}
            .tab-btn {{ padding: 10px 20px; border: 1px solid #ddd; background: #fff; cursor: pointer; border-radius: 8px; font-weight: bold; color: #666; }}
            .tab-btn.active {{ background: var(--main); color: #fff; border-color: var(--main); }}

            .shop-grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; }}
            .shop-grid.active {{ display: grid; }}

            .shop-card {{ background: #fff; border-radius: 15px; border: 1px solid #eee; overflow: hidden; transition: 0.3s; box-shadow: 0 4px 10px rgba(0,0,0,0.02); }}
            .shop-card:hover {{ transform: translateY(-5px); box-shadow: 0 15px 30px rgba(0,0,0,0.1); }}
            
            .image-area {{ position: relative; aspect-ratio: 16/9; }}
            .image-area img {{ width: 100%; height: 100%; object-fit: cover; }}
            .merch-tag {{ position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.7); color: #fff; font-size: 0.7rem; padding: 4px 10px; border-radius: 5px; font-weight: bold; }}

            .shop-info {{ padding: 20px; }}
            .liver-name {{ font-size: 0.85rem; font-weight: bold; color: var(--main); margin-bottom: 5px; }}
            .ai-catch {{ font-size: 1.1rem; font-weight: 900; color: #1a202c; margin-bottom: 10px; border-left: 4px solid var(--sub); padding-left: 10px; }}
            .v-ref {{ font-size: 0.75rem; color: #888; margin-bottom: 20px; line-height: 1.4; }}

            .shop-links {{ display: flex; flex-direction: column; gap: 10px; }}
            .s-btn {{ text-decoration: none; padding: 12px; border-radius: 10px; font-size: 0.9rem; font-weight: bold; text-align: center; color: #fff; transition: 0.2s; }}
            .amz {{ background: var(--amz); }}
            .rak {{ background: var(--rak); }}
            .watch-link {{ display: block; text-align: center; font-size: 0.75rem; color: #aaa; text-decoration: none; margin-top: 15px; }}
            .watch-link:hover {{ text-decoration: underline; }}

            footer {{ text-align: center; padding: 40px; color: #999; font-size: 0.8rem; }}
        </style>
        <script>
            function openTab(id) {{
                document.querySelectorAll('.shop-grid').forEach(g => g.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.getElementById(id).classList.add('active');
                document.getElementById('btn-' + id).classList.add('active');
            }}
        </script>
    </head>
    <body>
        <header>
            <h1>💎 {SITE_NAME}</h1>
            <div class="subtitle">AIが厳選。推しの最新限定グッズ最速ガイド</div>
        </header>
        <div class="container">
            <div class="nav-tabs">
                <button id="btn-holo" class="tab-btn active" onclick="openTab('holo')">Hololive</button>
                <button id="btn-stars" class="tab-btn" onclick="tab('stars')">Holostars</button>
            </div>
            <div id="holo" class="shop-grid active">{content_holo or "<p style='grid-column:1/-1;text-align:center;'>準備中...</p>"}</div>
            <div id="stars" class="shop-grid">{content_stars or "<p style='grid-column:1/-1;text-align:center;'>準備中...</p>"}</div>
        </div>
        <footer>© {datetime.now().year} {SITE_NAME} | Fan News</footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    main()
