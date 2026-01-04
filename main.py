import os
import requests
from datetime import datetime
import urllib.parse

# ==========================================
# 🌟 ID固定設定
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")

def fetch_videos(org_name):
    """APIからデータを取得。型チェックを極限まで強化"""
    url = "https://holodex.net/api/v2/videos"
    params = {
        "org": org_name,
        "limit": 50,
        "sort": "view_count",
        "order": "desc",
        "type": "stream,clip"
    }
    try:
        res = requests.get(url, params=params, headers={"X-APIKEY": HOLODEX_API_KEY}, timeout=15)
        res.raise_for_status()
        data = res.json()
        # リスト形式で届いているか厳密に確認
        if isinstance(data, list):
            return [v for v in data if isinstance(v, dict) and v.get('id')]
        return []
    except Exception as e:
        print(f"Error fetching {org_name}: {e}")
        return []

def main():
    # 1. データの取得
    list_holo = fetch_videos("Hololive")
    list_stars = fetch_videos("Holostars")
    
    # 2. HTML生成
    html_cards_holo = ""
    html_cards_stars = ""

    def make_html(v, org_label):
        v_id = v.get('id')
        title = v.get('title', 'Untitled')
        views = v.get('view_count', 0)
        # チャンネル名取得のガード
        ch_dict = v.get('channel', {})
        ch_name = ch_dict.get('name', 'Unknown') if isinstance(ch_dict, dict) else 'Unknown'
        
        query = urllib.parse.quote(f"{org_label} {ch_name}")
        
        return f"""
        <div class="card">
            <div class="thumb-wrap">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" loading="lazy">
                <div class="view-count">👀 {views:,} views</div>
            </div>
            <div class="card-body">
                <div class="ch-name">👤 {ch_name}</div>
                <div class="v-title">{title}</div>
                <div class="links">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-main">視聴する</a>
                    <a href="https://www.amazon.co.jp/s?k={query}&tag={AMAZON_ID}" target="_blank" class="btn">Amazon</a>
                    <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{query}%2F" target="_blank" class="btn">楽天</a>
                </div>
            </div>
        </div>
        """

    # 各リストからカード作成
    for v in list_holo: html_cards_holo += make_html(v, "ホロライブ")
    for v in list_stars: html_cards_stars += make_html(v, "ホロスターズ")

    # 最終出力
    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <style>
            body {{ font-family: sans-serif; background: #f0f4f8; color: #2d3748; margin: 0; display: flex; height: 100vh; overflow: hidden; }}
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
            .v-title {{ font-size: 14px; font-weight: bold; height: 3em; overflow: hidden; margin-bottom: 15px; }}
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
            <div id="holo" class="grid active">{html_cards_holo or "<p>データ読み込み中、または取得失敗</p>"}</div>
            <div id="stars" class="grid">{html_cards_stars or "<p>データ読み込み中、または取得失敗</p>"}</div>
        </main>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    main()
