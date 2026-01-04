import os
import requests
from google import genai
from datetime import datetime
import urllib.parse

# ==========================================
# 🌟 設定済みID
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_data(org):
    """APIからデータを取得し、確実に辞書形式のものだけを50件返す"""
    url = "https://holodex.net/api/v2/videos"
    params = {
        "org": org, "limit": 50, "sort": "view_count", 
        "order": "desc", "type": "stream,clip"
    }
    try:
        res = requests.get(url, params=params, headers={"X-APIKEY": HOLODEX_API_KEY}, timeout=10)
        data = res.json()
        if isinstance(data, list):
            # 辞書型であり、かつchannel情報を持っているものだけを抽出
            return [v for v in data if isinstance(v, dict) and isinstance(v.get('channel'), dict)]
    except:
        pass
    return []

def main():
    # 1. データの取得
    list_holo = fetch_data("Hololive")
    list_stars = fetch_data("Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTML構築用のパーツ
    html_cards_holo = ""
    html_cards_stars = ""

    def generate_card_html(v, org_search_tag):
        """1つの動画カードを作成。失敗したら空文字を返す。"""
        try:
            v_id = v.get('id')
            title = v.get('title', 'No Title')
            views = v.get('view_count', 0)
            channel = v.get('channel', {})
            ch_name = channel.get('name', 'Unknown')
            
            if not v_id: return ""

            # AI解析 (失敗しても止まらないようにtry-except)
            m_info, ai_desc = "None", "分析中"
            try:
                prompt = f"Extract if music: [Song - Artist]. Summary: 15 chars. Format: Music|Summary. Title: {title}"
                res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                if res.text:
                    parts = res.text.strip().split('|')
                    m_info = parts[0].strip()
                    ai_desc = parts[1].strip() if len(parts) > 1 else "注目の配信"
            except:
                pass

            m_html = f'<div class="music-tag">🎵 {m_info}</div>' if "None" not in m_info else ""
            query = urllib.parse.quote(f"{org_search_tag} {ch_name}")

            return f"""
            <div class="card">
                <div class="thumb-box">
                    <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" class="thumb" loading="lazy">
                    <div class="v-badge">{views:,} views</div>
                </div>
                <div class="info">
                    <div class="title">{title}</div>
                    <div class="ch">{ch_name}</div>
                    {m_html}
                    <div class="ai-desc">🤖 {ai_desc}</div>
                    <div class="links">
                        <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-watch">Watch</a>
                        <a href="https://www.amazon.co.jp/s?k={query}&tag={AMAZON_ID}" target="_blank" class="btn">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{query}%2F" target="_blank" class="btn">楽天</a>
                    </div>
                </div>
            </div>
            """
        except:
            return ""

    # ホロライブ生成
    for v in list_holo:
        html_cards_holo += generate_card_html(v, "ホロライブ")
    
    # スターズ生成
    for v in list_stars:
        html_cards_stars += generate_card_html(v, "ホロスターズ")

    # 最終的なHTML
    # JavaScriptの波括弧は {{ }} でエスケープ
    full_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{SITE_NAME}</title>
    <style>
        :root {{ --bg: #f8fafc; --side: #ffffff; --accent: #0ea5e9; --stars: #f59e0b; --txt: #1e293b; --sub: #64748b; }}
        body {{ font-family: sans-serif; background: var(--bg); color: var(--txt); margin: 0; display: flex; height: 100vh; overflow: hidden; }}
        nav {{ width: 200px; background: var(--side); border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; padding-top: 20px; flex-shrink: 0; }}
        .logo {{ padding: 0 20px 30px; font-size: 24px; font-weight: bold; color: var(--accent); }}
        .nav-item {{ padding: 15px 20px; cursor: pointer; color: var(--sub); font-weight: bold; font-size: 14px; border-left: 4px solid transparent; }}
        .nav-item:hover {{ background: #f1f5f9; }}
        .nav-item.active {{ background: #f0f9ff; color: var(--accent); border-left-color: var(--accent); }}
        .nav-stars.active {{ background: #fffbeb; color: var(--stars); border-left-color: var(--stars); }}
        main {{ flex: 1; overflow-y: auto; padding: 20px; }}
        .grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }}
        .grid.active {{ display: grid; }}
        .card {{ background: #fff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; display: flex; flex-direction: column; }}
        .thumb-box {{ position: relative; aspect-ratio: 16/9; background: #000; }}
        .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
        .v-badge {{ position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.8); color: #fff; font-size: 11px; padding: 3px 8px; border-radius: 6px; }}
        .info {{ padding: 15px; flex-grow: 1; display: flex; flex-direction: column; }}
        .title {{ font-size: 14px; font-weight: bold; height: 3em; overflow: hidden; margin-bottom: 8px; }}
        .ch {{ font-size: 12px; color: var(--sub); margin-bottom: 10px; }}
        .music-tag {{ color: #8b5cf6; font-size: 11px; font-weight: bold; margin-bottom: 5px; }}
        .ai-desc {{ font-size: 11px; color: var(--sub); font-style: italic; }}
        .links {{ display: flex; gap: 5px; margin-top: auto; padding-top: 15px; }}
        .btn {{ flex: 1; text-decoration: none; font-size: 10px; font-weight: bold; text-align: center; padding: 8px; border-radius: 6px; color: #475569; background: #f1f5f9; }}
        .btn-watch {{ background: var(--accent); color: #fff; }}
    </style>
    <script>
        function tab(id) {{
            document.querySelectorAll('.grid').forEach(g => g.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            document.getElementById('btn-' + id).classList.add('active');
        }}
    </script>
</head>
<body onload="tab('holo')">
    <nav>
        <div class="logo">Navi</div>
        <div id="btn-holo" class="nav-item active" onclick="tab('holo')">HOLOLIVE</div>
        <div id="btn-stars" class="nav-item nav-stars" onclick="tab('stars')">HOLOSTARS</div>
    </nav>
    <main>
        <div id="holo" class="grid active">{html_cards_holo}</div>
        <div id="stars" class="grid">{html_cards_stars}</div>
    </main>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    main()
