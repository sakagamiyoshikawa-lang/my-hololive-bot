import os
import requests
from google import genai
from datetime import datetime

# ==========================================
# 🌟 設定済みID（画像から取得）
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_videos(org):
    """API上限を回避し、指定組織の再生数上位100件を確実に取得"""
    url = "https://holodex.net/api/v2/videos"
    all_videos = []
    # 50件ずつ2回に分けて取得
    for offset in [0, 50]:
        params = {
            "org": org,
            "limit": 50,
            "offset": offset,
            "sort": "view_count",
            "order": "desc",
            "type": "stream,clip"
        }
        try:
            res = requests.get(url, params=params, headers={"X-APIKEY": HOLODEX_API_KEY}, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    all_videos.extend(data)
        except Exception as e:
            print(f"Fetch error for {org}: {e}")
    return all_videos

def main():
    # 1. データの取得
    v_holo = fetch_videos("Hololive")
    v_stars = fetch_videos("Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTML構築（JSの波括弧は {{ }} でエスケープ）
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} | Holodex UI Version</title>
        <style>
            :root {{
                --bg-body: #0f0f0f; --bg-sidebar: #121212; --bg-card: #1c1c1c;
                --text-main: #ffffff; --text-sub: #aaaaaa; --accent: #00c2ff;
                --stars: #ffb800; --music: #bb86fc;
            }}
            body {{
                font-family: "Roboto", Arial, sans-serif; background: var(--bg-body); 
                color: var(--text-main); margin: 0; display: flex; height: 100vh;
            }}
            
            /* サイドバー */
            nav {{
                width: 220px; background: var(--bg-sidebar); border-right: 1px solid #333;
                flex-shrink: 0; display: flex; flex-direction: column;
            }}
            .nav-header {{ padding: 25px 20px; font-size: 22px; font-weight: 900; color: var(--accent); }}
            .nav-item {{
                padding: 15px 20px; cursor: pointer; color: var(--text-sub); font-size: 14px;
                font-weight: bold; border-left: 4px solid transparent; transition: 0.2s;
            }}
            .nav-item:hover {{ background: #222; color: #fff; }}
            .nav-item.active {{ background: #262626; color: var(--accent); border-left-color: var(--accent); }}
            .nav-item-stars.active {{ color: var(--stars); border-left-color: var(--stars); }}

            /* メインエリア */
            main {{ flex: 1; overflow-y: auto; padding: 20px; position: relative; }}
            .top-bar {{ display: flex; justify-content: space-between; margin-bottom: 25px; font-size: 13px; color: var(--text-sub); border-bottom: 1px solid #333; padding-bottom: 10px; }}
            
            .video-grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; }}
            .video-grid.active {{ display: grid; }}

            /* カードデザイン */
            .card {{ background: var(--bg-card); border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; transition: 0.2s; }}
            .card:hover {{ transform: scale(1.02); background: #2a2a2a; }}
            .thumb-box {{ position: relative; aspect-ratio: 16/9; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .v-badge {{ position: absolute; bottom: 6px; right: 6px; background: rgba(0,0,0,0.85); font-size: 11px; padding: 2px 8px; border-radius: 4px; }}

            .info {{ padding: 12px; flex-grow: 1; display: flex; flex-direction: column; }}
            .title {{ font-size: 14px; font-weight: bold; line-height: 1.4; height: 2.8em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 8px; }}
            .ch {{ font-size: 12px; color: var(--text-sub); margin-bottom: 10px; }}
            
            .ai-box {{ border-top: 1px solid #333; padding-top: 10px; margin-top: auto; }}
            .music {{ color: var(--music); font-size: 11px; font-weight: bold; margin-bottom: 5px; }}
            .desc {{ font-size: 11px; color: #888; line-height: 1.4; }}

            .links {{ display: flex; gap: 8px; margin-top: 12px; }}
            .btn {{ flex: 1; text-decoration: none; font-size: 11px; font-weight: bold; text-align: center; padding: 8px; border-radius: 4px; color: #fff; background: #333; }}
            .btn:hover {{ filter: brightness(1.3); }}
            .btn-watch {{ background: var(--accent); }}

            @media (max-width: 800px) {{
                nav {{ width: 70px; }} .nav-text, .nav-header {{ display: none; }}
            }}
        </style>
        <script>
            function switchTab(id) {{
                document.querySelectorAll('.video-grid').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                document.getElementById(id).classList.add('active');
                document.getElementById('btn-' + id).classList.add('active');
            }}
        </script>
    </head>
    <body onload="switchTab('holo')">
        <nav>
            <div class="nav-header">Navi</div>
            <div id="btn-holo" class="nav-item active" onclick="switchTab('holo')">
                <span class="nav-text">Hololive TOP 100</span>
            </div>
            <div id="btn-stars" class="nav-item nav-item-stars" onclick="switchTab('stars')">
                <span class="nav-text">Holostars TOP 100</span>
            </div>
        </nav>
        <main>
            <div class="top-bar">
                <span>再生数上位100選 × AI楽曲解析</span>
                <span>最終更新: {datetime.now().strftime('%m/%d %H:%M')}</span>
            </div>

            <div id="holo" class="video-grid active">
    """

    def create_card(v, org_name, color):
        """カード1枚を安全に生成"""
        # --- 堅牢なデータ取得チェック ---
        if not isinstance(v, dict): return ""
        v_id = v.get('id')
        title = v.get('title', 'No Title')
        views = v.get('view_count', 0)
        
        # channelが辞書でない場合をガード（これが重要！）
        channel = v.get('channel')
        ch_name = channel.get('name', 'Unknown') if isinstance(channel, dict) else "Unknown Artist"
        
        if not v_id: return ""

        # AI解析
        prompt = f"Music: [Song - Artist] or [None]. Summary: 15 chars. Format: Music|Summary. Title: {title}"
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            parts = res.text.strip().split('|')
            m_val, ai_txt = (parts[0].strip(), parts[1].strip()) if len(parts) > 1 else ("None", "最新情報を分析中")
        except: m_val, ai_txt = "None", "詳細をチェック"

        m_html = f'<div class="music">🎵 {m_val}</div>' if "None" not in m_val else ""
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
                <div class="ai-box">
                    {m_html}
                    <div class="desc">🤖 {ai_txt}</div>
                </div>
                <div class="links">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-watch" style="background:{color}">Watch</a>
                    <a href="https://www.amazon.co.jp/s?k={q}&tag={AMAZON_ID}" target="_blank" class="btn">Amazon</a>
                    <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{q}%2F" target="_blank" class="btn">Rakuten</a>
                </div>
            </div>
        </div>"""

    # 各グループのカードを生成
    for v in v_holo:
        html_content += create_card(v, "ホロライブ", "var(--accent)")
    
    html_content += """</div><div id="stars" class="video-grid">"""
    
    for v in v_stars:
        html_content += create_card(v, "ホロスターズ", "var(--stars)")

    html_content += """</main></body></html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
