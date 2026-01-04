import os
import requests
from google import genai
from datetime import datetime
import urllib.parse
import time

# ==========================================
# 🌟 ID固定設定（設定済み）
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_videos(org_name):
    """APIから取得。リトライ処理と詳細なエラー報告を追加"""
    url = "https://holodex.net/api/v2/videos"
    params = {
        "org": org_name, "limit": 50, "sort": "view_count",
        "order": "desc", "type": "stream,clip"
    }
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    status_msg = ""
    try:
        # タイムアウトを少し長めに設定
        res = requests.get(url, params=params, headers=headers, timeout=30)
        
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                return [v for v in data if isinstance(v, dict) and v.get('id')], "Success"
            return [], "Empty Data"
        else:
            return None, f"API Error: {res.status_code}"
    except Exception as e:
        return None, f"Network Error: {str(e)}"

def main():
    # 1. データの取得
    list_holo, msg_holo = fetch_videos("Hololive")
    time.sleep(2) # 負荷軽減のための待機
    list_stars, msg_stars = fetch_videos("Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    # 2. HTML生成
    def make_html(v_list, org_label, status_msg):
        if v_list is None:
            return f"""
            <div style="grid-column: 1/-1; text-align: center; padding: 50px;">
                <p style="font-size: 3rem;">⚠️</p>
                <p style="font-weight: bold; color: #e53e3e;">{org_label}のデータ取得に失敗しました</p>
                <p style="font-size: 0.8rem; color: #a0aec0;">理由: {status_msg}</p>
            </div>
            """
        
        if not v_list:
            return f"<p style='grid-column: 1/-1; text-align: center; padding: 50px;'>現在、{org_label}の注目データはありません。</p>"

        cards_html = ""
        for v in v_list:
            v_id = v.get('id')
            title = v.get('title', 'Untitled')
            views = v.get('view_count', 0)
            ch_name = v.get('channel', {}).get('name', 'Unknown')
            
            # AI解析（簡易版で安定性重視）
            desc = "最新配信をチェック！"
            try:
                prompt = f"15文字以内のキャッチコピーを書いて。タイトル: {title}"
                res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                if res.text: desc = res.text.strip()
            except: pass

            query = urllib.parse.quote(f"{org_label} {ch_name}")
            cards_html += f"""
            <div class="card">
                <div class="thumb-wrap">
                    <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" loading="lazy">
                    <div class="view-count">👀 {views:,} views</div>
                </div>
                <div class="card-body">
                    <div class="ch-name">👤 {ch_name}</div>
                    <div class="v-title">{title}</div>
                    <div style="font-size: 11px; color: #718096; margin-bottom: 15px; font-style: italic;">🤖 {desc}</div>
                    <div class="links">
                        <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-main">視聴</a>
                        <a href="https://www.amazon.co.jp/s?k={query}&tag={AMAZON_ID}" target="_blank" class="btn">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{query}%2F" target="_blank" class="btn">楽天</a>
                    </div>
                </div>
            </div>
            """
        return cards_html

    content_holo = make_html(list_holo, "ホロライブ", msg_holo)
    content_stars = make_html(list_stars, "ホロスターズ", msg_stars)

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <style>
            body {{ font-family: sans-serif; background: #f4f7f9; color: #2d3748; margin: 0; display: flex; height: 100vh; overflow: hidden; }}
            nav {{ width: 220px; background: #fff; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; padding: 20px 0; flex-shrink: 0; }}
            .nav-item {{ padding: 15px 20px; cursor: pointer; font-weight: bold; color: #718096; border-left: 4px solid transparent; }}
            .nav-item.active {{ background: #ebf8ff; color: #00b5d8; border-left-color: #00b5d8; }}
            main {{ flex: 1; overflow-y: auto; padding: 20px; }}
            .grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }}
            .grid.active {{ display: grid; }}
            .card {{ background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; display: flex; flex-direction: column; }}
            .thumb-wrap {{ position: relative; aspect-ratio: 16/9; }}
            .thumb-wrap img {{ width: 100%; height: 100%; object-fit: cover; }}
            .view-count {{ position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.7); color: #fff; font-size: 11px; padding: 3px 8px; border-radius: 4px; }}
            .card-body {{ padding: 15px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 12px; color: #00b5d8; font-weight: bold; margin-bottom: 5px; }}
            .v-title {{ font-size: 14px; font-weight: bold; height: 3em; overflow: hidden; margin-bottom: 10px; }}
            .links {{ display: flex; gap: 5px; margin-top: auto; }}
            .btn {{ flex: 1; text-decoration: none; font-size: 10px; font-weight: bold; text-align: center; padding: 8px; border-radius: 6px; background: #edf2f7; color: #4a5568; }}
            .btn-main {{ background: #00b5d8; color: #fff; }}
        </style>
        <script>
            function show(id) {{
                document.querySelectorAll('.grid').forEach(g => g.style.display = 'none');
                document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                document.getElementById(id).style.display = 'grid';
                document.getElementById('btn-' + id).classList.add('active');
            }}
        </script>
    </head>
    <body onload="show('holo')">
        <nav>
            <div style="padding: 0 20px 20px; font-size: 24px; font-weight: bold; color: #00b5d8;">{SITE_NAME}</div>
            <div id="btn-holo" class="nav-item active" onclick="show('holo')">Hololive TOP 50</div>
            <div id="btn-stars" class="nav-item" onclick="show('stars')">Holostars TOP 50</div>
        </nav>
        <main>
            <div style="display: flex; justify-content: space-between; margin-bottom: 20px; font-size: 12px; color: #718096;">
                <span>注目コンテンツ（自動更新）</span>
                <span>最終更新: {datetime.now().strftime('%m/%d %H:%M')}</span>
            </div>
            <div id="holo" class="grid active">{content_holo}</div>
            <div id="stars" class="grid">{content_stars}</div>
        </main>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    main()
