import os
import requests
from google import genai
from datetime import datetime

# ==========================================
# 🌟 設定済みID
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_top_videos(org, total_limit=100):
    """API上限を回避し、指定組織から再生数上位を確実に取得"""
    url = "https://holodex.net/api/v2/videos"
    collected = []
    # 50件ずつ取得
    for offset in range(0, total_limit, 50):
        params = {
            "org": org, "limit": 50, "offset": offset,
            "sort": "view_count", "order": "desc", "type": "stream,clip"
        }
        try:
            res = requests.get(url, params=params, headers={"X-APIKEY": HOLODEX_API_KEY}, timeout=10)
            data = res.json()
            if isinstance(data, list):
                # 辞書形式でない不純物を除去
                collected.extend([v for v in data if isinstance(v, dict)])
        except:
            continue
    return collected

def main():
    # 1. データの取得
    list_holo = fetch_top_videos("Hololive", 100)
    list_stars = fetch_top_videos("Holostars", 100)
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    # JavaScript部分をPythonのf-string干渉から守るために分離
    js_code = """
    function switchTab(targetId) {
        document.querySelectorAll('.video-grid').forEach(el => el.style.display = 'none');
        document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
        document.getElementById(targetId).style.display = 'grid';
        document.getElementById('btn-' + targetId).classList.add('active');
    }
    """

    # HTMLヘッダー
    html_start = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} | Portal</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --bg: #f8fafc; --side: #ffffff; --card: #ffffff; --text: #1e293b; --sub: #64748b; --accent: #0ea5e9; --stars: #f59e0b; --music: #8b5cf6; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--bg); color: var(--text); margin: 0; display: flex; height: 100vh; overflow: hidden; }}
            nav {{ width: 220px; background: var(--side); border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; padding-top: 20px; flex-shrink: 0; }}
            .logo {{ padding: 0 20px 30px; font-size: 24px; font-weight: 900; color: var(--accent); }}
            .nav-item {{ padding: 15px 20px; cursor: pointer; color: var(--sub); font-size: 14px; font-weight: bold; border-left: 4px solid transparent; transition: 0.2s; }}
            .nav-item:hover {{ background: #f1f5f9; }}
            .nav-item.active {{ background: #f0f9ff; color: var(--accent); border-left-color: var(--accent); }}
            .nav-stars.active {{ background: #fffbeb; color: var(--stars); border-left-color: var(--stars); }}
            main {{ flex: 1; overflow-y: auto; padding: 25px; }}
            .top-bar {{ display: flex; justify-content: space-between; margin-bottom: 25px; font-size: 13px; color: var(--sub); border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; font-weight: bold; }}
            .video-grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }}
            .card {{ background: var(--card); border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; display: flex; flex-direction: column; transition: 0.2s; }}
            .card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.05); }}
            .thumb-box {{ position: relative; aspect-ratio: 16/9; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .v-badge {{ position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.8); color: white; font-size: 11px; padding: 3px 8px; border-radius: 6px; }}
            .info {{ padding: 15px; flex-grow: 1; display: flex; flex-direction: column; }}
            .title {{ font-size: 14px; font-weight: bold; line-height: 1.5; height: 3em; overflow: hidden; margin-bottom: 8px; }}
            .ch {{ font-size: 12px; color: var(--sub); margin-bottom: 12px; font-weight: bold; }}
            .music-tag {{ color: var(--music); font-size: 11px; font-weight: 900; margin-bottom: 5px; border-top: 1px solid #f1f5f9; padding-top: 10px; }}
            .ai-desc {{ font-size: 11px; color: var(--sub); font-style: italic; }}
            .links {{ display: flex; gap: 8px; margin-top: auto; padding-top: 15px; }}
            .btn {{ flex: 1; text-decoration: none; font-size: 11px; font-weight: 900; text-align: center; padding: 10px; border-radius: 8px; color: #475569; background: #f1f5f9; }}
            .btn-watch {{ background: var(--accent); color: white; }}
        </style>
        <script>{js_code}</script>
    </head>
    <body onload="switchTab('holo')">
        <nav>
            <div class="logo">HoloNavi</div>
            <div id="btn-holo" class="nav-item active" onclick="switchTab('holo')">Hololive TOP 100</div>
            <div id="btn-stars" class="nav-item nav-stars" onclick="switchTab('stars')">Holostars TOP 100</div>
        </nav>
        <main>
            <div class="top-bar">
                <span>再生数上位ポータル (AI解析)</span>
                <span>最終更新: {datetime.now().strftime('%m/%d %H:%M')}</span>
            </div>
            <div id="holo" class="video-grid" style="display:grid;">
    """

    def create_card(v, org_name, accent_color):
        """動画データを安全にHTML化"""
        if not isinstance(v, dict): return ""
        v_id = v.get('id')
        title = v.get('title', 'No Title')
        views = v.get('view_count', 0)
        channel = v.get('channel')
        ch_name = channel.get('name', 'Unknown') if isinstance(channel, dict) else "Unknown"
        
        if not v_id: return ""

        # Gemini解析
        prompt = f"Music: [Song - Artist] or [None]. Summary: 15 chars. Format: Music|Summary. Title: {title}"
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            parts = res.text.strip().split('|')
            m_val, ai_txt = (parts[0].strip(), parts[1].strip()) if len(parts) > 1 else ("None", "最新情報をチェック")
        except: m_val, ai_txt = "None", "詳細分析中"

        m_html = f'<div class="music-tag">🎵 {m_val}</div>' if "None" not in m_val else ""
        q = requests.utils.quote(f"{org_name} {ch_name}")

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
                <div class="ai-desc">🤖 {ai_txt}</div>
                <div class="links">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-watch" style="background:{accent_color}">Watch</a>
                    <a href="https://www.amazon.co.jp/s?k={q}&tag={AMAZON_ID}" target="_blank" class="btn">Amazon</a>
                    <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{q}%2F" target="_blank" class="btn">楽天</a>
                </div>
            </div>
        </div>"""

    # ホロライブ出力
    content_holo = ""
    for v in list_holo:
        # スターズ混入防止
        sub = v.get('channel', {}).get('sub_org', '') if isinstance(v.get('channel'), dict) else ''
        if "stars" in str(sub).lower(): continue
        content_holo += create_card(v, "ホロライブ", "var(--accent)")
    
    # スターズ出力
    content_stars = ""
    for v in list_stars:
        content_stars += create_card(v, "ホロスターズ", "var(--stars)")

    html_end = f"""
            </div>
            <div id="stars" class="video-grid">
                {content_stars}
            </div>
        </main>
    </body>
    </html>"""

    # 最終書き出し
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_start + content_holo + html_end)

if __name__ == "__main__":
    main()
