import os
import requests
from google import genai
from datetime import datetime
import urllib.parse

# ==========================================
# 🌟 ID固定設定済み
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_data(org):
    """APIから確実にデータを取得する（不純物が入っても壊れないガード付き）"""
    url = "https://holodex.net/api/v2/videos"
    params = {
        "org": org, "limit": 50, "sort": "view_count", 
        "order": "desc", "type": "stream,clip"
    }
    try:
        res = requests.get(url, params=params, headers={"X-APIKEY": HOLODEX_API_KEY}, timeout=15)
        data = res.json()
        # APIがリストではなく「エラー文字列」を返してきた場合、空リストにする
        if not isinstance(data, list):
            return []
        # 動画データ（辞書型）のみを抽出し、それ以外は捨てる
        return [v for v in data if isinstance(v, dict)]
    except Exception as e:
        print(f"API Fetch Error for {org}: {e}")
        return []

def main():
    # 1. データの取得
    list_holo = fetch_data("Hololive")
    list_stars = fetch_data("Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    # カード生成用の内部関数
    def make_card(v, org_tag):
        # 徹底ガード：v自体が辞書でない、またはchannelがない場合は即終了
        if not isinstance(v, dict) or not isinstance(v.get('channel'), dict):
            return ""
        
        v_id = v.get('id')
        title = v.get('title', 'No Title')
        views = v.get('view_count', 0)
        ch_name = v['channel'].get('name', 'Unknown')
        
        if not v_id: return ""

        # AI解析（失敗してもサイトが止まらないようガード）
        m_info, ai_desc = "None", "分析中..."
        try:
            prompt = f"Extract if music: [Song - Artist]. Summary: 15 chars. Format: Music|Summary. Title: {title}"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res and res.text:
                parts = res.text.strip().split('|')
                m_info = parts[0].strip()
                ai_desc = parts[1].strip() if len(parts) > 1 else "注目の配信"
        except: pass

        m_html = f'<div class="music-tag">🎵 {m_info}</div>' if "None" not in m_info else ""
        query = urllib.parse.quote(f"{org_tag} {ch_name}")

        return f"""
        <div class="card">
            <div class="thumb-box">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" class="thumb" loading="lazy">
                <div class="v-badge">👀 {views:,} views</div>
            </div>
            <div class="info">
                <div class="title">{title}</div>
                <div class="ch">👤 {ch_name}</div>
                {m_html}
                <div class="ai-desc">🤖 {ai_desc}</div>
                <div class="links">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-watch">Watch</a>
                    <a href="https://www.amazon.co.jp/s?k={query}&tag={AMAZON_ID}" target="_blank" class="btn">Amazon</a>
                    <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{query}%2F" target="_blank" class="btn">楽天</a>
                </div>
            </div>
        </div>"""

    # 各タブのコンテンツを生成
    # フィルターを緩くして、とにかくデータがあれば入れる
    content_holo = "".join([make_card(v, "ホロライブ") for v in list_holo])
    content_stars = "".join([make_card(v, "ホロスターズ") for v in list_stars])

    # もしデータがゼロだった時のメッセージ
    if not content_holo: content_holo = "<p style='color:#666; text-align:center; grid-column:1/-1;'>Hololiveの動画が見つかりませんでした。時間をおいて再試行してください。</p>"
    if not content_stars: content_stars = "<p style='color:#666; text-align:center; grid-column:1/-1;'>Holostarsの動画が見つかりませんでした。</p>"

    # 最終HTML
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
        .nav-item.active {{ background: #f0f9ff; color: var(--accent); border-left-color: var(--accent); }}
        .nav-stars.active {{ background: #fffbeb; color: var(--stars); border-left-color: var(--stars); }}
        main {{ flex: 1; overflow-y: auto; padding: 25px; }}
        .grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }}
        .grid.active {{ display: grid; }}
        .card {{ background: #fff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; display: flex; flex-direction: column; transition: 0.2s; }}
        .card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.05); }}
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
            document.querySelectorAll('.grid').forEach(g => g.style.display = 'none');
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            document.getElementById(id).style.display = 'grid';
            document.getElementById('btn-' + id).classList.add('active');
        }}
    </script>
</head>
<body onload="tab('holo')">
    <nav>
        <div class="logo">Navi</div>
        <div id="btn-holo" class="nav-item active" onclick="tab('holo')">Hololive TOP 50</div>
        <div id="btn-stars" class="nav-item nav-stars" onclick="tab('stars')">Holostars TOP 50</div>
    </nav>
    <main>
        <div class="grid active" id="holo">{content_holo}</div>
        <div class="grid" id="stars">{content_stars}</div>
    </main>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    main()
