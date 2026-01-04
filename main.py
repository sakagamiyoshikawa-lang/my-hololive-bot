import os
import requests
from google import genai
from datetime import datetime
import urllib.parse
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

def fetch_content(org):
    """情報の精度を上げるため、再生数上位＋新着を織り交ぜて取得"""
    url = "https://holodex.net/api/v2/videos"
    params = {"org": org, "limit": 40, "sort": "view_count", "order": "desc"}
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    try:
        res = requests.get(url, params=params, headers=headers, timeout=20)
        return (res.json() if res.status_code == 200 else []), "OK"
    except:
        return [], "Error"

def main():
    list_holo, _ = fetch_content("Hololive")
    time.sleep(1)
    list_stars, _ = fetch_content("Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    def create_support_card(v, org_tag):
        if not v or not isinstance(v, dict): return ""
        v_id, title = v.get('id'), v.get('title', 'No Title')
        ch = v.get('channel', {})
        ch_name = ch.get('name', 'Unknown')
        
        # --- AIによる「尊いポイント」の抽出 ---
        highlight = "配信をチェックして見どころを見つけよう！"
        support_msg = "公式チャンネルを登録して応援しよう！"
        try:
            prompt = f"ホロライブファンとして、この配信タイトル『{title}』の『推しポイント』を熱く分析して。15文字以内のエモい見出し|20文字以内の応援コメント。形式: 見出し|コメント"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                highlight = parts[0].strip()
                support_msg = parts[1].strip() if len(parts) > 1 else support_msg
        except: pass

        query = urllib.parse.quote(f"{ch_name} 応援")
        
        return f"""
        <div class="card">
            <div class="thumb-area">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" loading="lazy">
                <div class="tag">{org_tag}</div>
            </div>
            <div class="body">
                <div class="ch-info">
                    <span class="ch-name">👤 {ch_name}</span>
                </div>
                <div class="highlight-title">✨ {highlight}</div>
                <div class="video-title">{title}</div>
                <div class="ai-support-msg">💬 {support_msg}</div>
                
                <div class="action-box">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn-primary">今すぐ応援しに行く</a>
                    <div class="support-label">ライバーの活動を支援する</div>
                    <div class="merch-links">
                        <a href="https://www.amazon.co.jp/s?k={query}&tag={AMAZON_ID}" target="_blank" class="btn-sub amz">関連アイテム (Amazon)</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{query}%2F" target="_blank" class="btn-sub rak">楽天で支援</a>
                    </div>
                </div>
            </div>
        </div>
        """

    content_holo = "".join([create_support_card(v, "Hololive") for v in list_holo])
    content_stars = "".join([create_support_card(v, "Holostars") for v in list_stars])

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --holo: #00c2ff; --stars: #ffb800; --txt: #2d3748; --sub-txt: #718096; --bg: #f7fafc; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--bg); color: var(--txt); margin: 0; }}
            header {{ background: #fff; padding: 40px 20px; text-align: center; border-bottom: 3px solid var(--holo); }}
            header h1 {{ margin: 0; font-size: 2rem; color: var(--holo); font-weight: 900; }}
            .motto {{ font-size: 0.9rem; color: var(--sub-txt); margin-top: 10px; font-weight: bold; }}
            
            .container {{ max-width: 1200px; margin: 30px auto; padding: 0 15px; }}
            .nav {{ display: flex; justify-content: center; gap: 15px; margin-bottom: 30px; }}
            .nav-btn {{ padding: 12px 30px; border: none; background: #fff; cursor: pointer; border-radius: 50px; font-weight: 900; color: var(--sub-txt); box-shadow: 0 4px 10px rgba(0,0,0,0.05); transition: 0.3s; }}
            .nav-btn.active {{ background: var(--holo); color: #fff; box-shadow: 0 4px 15px rgba(0,194,255,0.3); }}

            .grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 30px; }}
            .grid.active {{ display: grid; }}

            .card {{ background: #fff; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05); display: flex; flex-direction: column; transition: 0.3s; }}
            .card:hover {{ transform: translateY(-5px); box-shadow: 0 20px 40px rgba(0,0,0,0.1); }}
            
            .thumb-area {{ position: relative; aspect-ratio: 16/9; }}
            .thumb-area img {{ width: 100%; height: 100%; object-fit: cover; }}
            .tag {{ position: absolute; top: 12px; left: 12px; background: rgba(0,0,0,0.7); color: #fff; padding: 4px 12px; border-radius: 8px; font-size: 0.7rem; font-weight: bold; }}

            .body {{ padding: 25px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ color: var(--holo); font-weight: 900; font-size: 0.85rem; }}
            .highlight-title {{ font-size: 1.2rem; font-weight: 900; margin: 10px 0; color: #1a202c; }}
            .video-title {{ font-size: 0.9rem; color: var(--sub-txt); line-height: 1.4; height: 2.8em; overflow: hidden; margin-bottom: 15px; }}
            .ai-support-msg {{ background: #f0f9ff; padding: 15px; border-radius: 12px; font-size: 0.9rem; border-left: 5px solid var(--holo); font-weight: bold; margin-bottom: 20px; }}

            .action-box {{ margin-top: auto; border-top: 1px solid #edf2f7; padding-top: 20px; }}
            .btn-primary {{ display: block; text-decoration: none; background: var(--holo); color: #fff; text-align: center; padding: 12px; border-radius: 12px; font-weight: 900; transition: 0.2s; }}
            .support-label {{ font-size: 0.75rem; color: var(--sub-txt); text-align: center; margin: 15px 0 8px; font-weight: bold; }}
            .merch-links {{ display: flex; gap: 8px; }}
            .btn-sub {{ flex: 1; text-decoration: none; font-size: 0.7rem; text-align: center; padding: 8px; border-radius: 8px; font-weight: bold; background: #f8fafc; color: var(--sub-txt); border: 1px solid #edf2f7; }}
            .btn-sub:hover {{ background: #edf2f7; }}

            footer {{ text-align: center; padding: 60px; color: var(--sub-txt); font-size: 0.8rem; }}
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
            <div class="motto">推しを広め、活動を支える。ファンのための応援ポータル</div>
        </header>
        <div class="container">
            <div class="nav">
                <button id="btn-holo" class="nav-btn active" onclick="tab('holo')">Hololive</button>
                <button id="btn-stars" class="nav-btn" onclick="tab('stars')">Holostars</button>
            </div>
            <div id="holo" class="grid active">{content_holo}</div>
            <div id="stars" class="grid">{content_stars}</div>
        </div>
        <footer>© {datetime.now().year} {SITE_NAME} | 非公式ファンプロジェクト</footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    main()
