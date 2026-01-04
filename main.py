import os
import requests
from google import genai
from datetime import datetime

# ==========================================
# 🌟 ID固定設定
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_videos(org, limit=100):
    """特定の組織から動画を取得するヘルパー関数"""
    url = "https://holodex.net/api/v2/videos"
    # APIの1回あたりの上限が50のため、2回に分けて取得
    all_videos = []
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
            res = requests.get(url, params=params, headers={"X-APIKEY": HOLODEX_API_KEY})
            data = res.json()
            if isinstance(data, list):
                all_videos.extend(data)
        except:
            pass
    return all_videos

def main():
    # 1. ホロライブとスターズをそれぞれ100件ずつ取得
    v_hololive = fetch_videos("Hololive")
    v_holostars = fetch_videos("Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTML構築
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} | 国内外トップ200 AI解析ポータル</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00c2ff; --sub: #ff66b2; --stars: #ffb800; --dark: #1a202c; --light: #f4f8fb; --music: #7e57c2; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--light); margin: 0; padding: 0; color: var(--dark); }}
            
            header {{ 
                background: linear-gradient(135deg, var(--main) 0%, var(--sub) 100%); 
                color: white; padding: 80px 20px; text-align: center; box-shadow: 0 4px 25px rgba(0,0,0,0.2); 
            }}
            header h1 {{ margin: 0; font-size: 3.5rem; font-weight: 900; letter-spacing: -2px; text-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
            .sub-title {{ font-weight: bold; font-size: 1.1rem; opacity: 0.9; margin-top: 10px; }}
            
            .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}

            /* ナビゲーション */
            .nav-box {{ 
                background: white; padding: 25px; border-radius: 30px; margin: -40px auto 30px; 
                text-align: center; box-shadow: 0 15px 40px rgba(0,0,0,0.1); position: relative; z-index: 100; max-width: 900px; 
            }}
            .nav-group {{ margin-bottom: 20px; }}
            .nav-label {{ font-size: 0.75rem; font-weight: 900; color: #cbd5e0; display: block; margin-bottom: 10px; letter-spacing: 2px; }}

            .btn-nav {{ 
                padding: 12px 30px; border: 2px solid #edf2f7; background: white; cursor: pointer; border-radius: 50px; 
                font-weight: 900; transition: 0.3s; color: #718096; margin: 5px;
            }}
            .btn-nav.active {{ border-color: var(--main); background: var(--main); color: white; box-shadow: 0 5px 20px rgba(0,194,255,0.4); }}
            .btn-stars.active {{ border-color: var(--stars); background: var(--stars); color: white; box-shadow: 0 5px 20px rgba(255,184,0,0.4); }}

            .video-list {{ display: none; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); gap: 30px; }}
            .video-list.active {{ display: grid; animation: fadeIn 0.5s ease; }}
            @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}

            /* カードデザイン */
            .card {{ background: white; border-radius: 25px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05); transition: 0.3s; display: flex; flex-direction: column; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 50px rgba(0,0,0,0.15); }}
            .thumb-container {{ position: relative; aspect-ratio: 16/9; background: #000; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .view-badge {{ position: absolute; bottom: 12px; right: 12px; background: rgba(0,0,0,0.8); color: white; padding: 4px 12px; border-radius: 8px; font-size: 0.8rem; font-weight: bold; }}

            .info {{ padding: 25px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 0.85rem; font-weight: 900; color: var(--main); margin-bottom: 8px; }}
            .video-title {{ font-weight: bold; font-size: 1.05rem; line-height: 1.5; margin-bottom: 15px; height: 3em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
            
            /* 🎵 楽曲情報 */
            .music-box {{ background: #f3e5f5; border-radius: 15px; padding: 15px; margin-bottom: 15px; border-left: 6px solid var(--music); }}
            .music-label {{ font-size: 0.65rem; color: var(--music); font-weight: 900; display: block; margin-bottom: 4px; }}
            .music-text {{ font-size: 0.85rem; font-weight: 900; color: #4a148c; }}
            
            .ai-comment {{ font-size: 0.85rem; color: #4a5568; background: #f8fafc; padding: 12px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #edf2f7; }}

            .links {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: auto; }}
            .btn-link {{ text-decoration: none; padding: 12px; border-radius: 15px; font-size: 0.8rem; font-weight: 900; text-align: center; transition: 0.2s; }}
            .btn-yt {{ background: var(--dark); color: white; grid-column: span 2; margin-bottom: 5px; }}
            .btn-amz {{ background: #ff9900; color: white; }}
            .btn-rak {{ background: #bf0000; color: white; }}
        </style>
        <script>
            function showTab(groupId) {{
                document.querySelectorAll('.video-list').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.btn-org').forEach(el => el.classList.remove('active'));
                document.getElementById(groupId).classList.add('active');
                document.getElementById('btn-' + groupId).classList.add('active');
            }}
        </script>
    </head>
    <body onload="showTab('holo')">
        <header>
            <h1>🌟 {SITE_NAME}</h1>
            <p class="sub-title">AI解析・再生数上位各100選ポータル</p>
            <div style="font-size:0.8rem; margin-top:15px; opacity:0.8;">最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </header>

        <div class="container">
            <div class="nav-box">
                <div class="nav-group">
                    <span class="nav-label">GROUP SELECT</span>
                    <button id="btn-holo" class="btn-nav btn-org active" onclick="showTab('holo')">HOLOLIVE (TOP 100)</button>
                    <button id="btn-stars" class="btn-nav btn-org btn-stars" onclick="showTab('stars')">HOLOSTARS (TOP 100)</button>
                </div>
            </div>

            <div id="holo" class="video-list active">
    """

    # --- カード生成関数 ---
    def create_card(v, org_name):
        try:
            ch_name = v['channel']['name']
            v_id = v['id']
            title = v['title']
            views = v.get('view_count', 0)
        except: return ""

        # AI楽曲解析
        prompt = f"Music info? [Song - Artist] or [None]. And 15-char catchphrase. Format: Music|Summary. Title: {title}"
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            parts = res.text.strip().split('|')
            m_val = parts[0].strip()
            ai_txt = parts[1].strip() if len(parts) > 1 else "人気動画をチェック！"
        except:
            m_val, ai_txt = "[None]", "ホロライブ最新情報を分析中"

        music_html = f'<div class="music-box"><span class="music-label">🎵 楽曲情報</span><div class="music-text">{m_val}</div></div>' if "[None]" not in m_val else ""

        search = requests.utils.quote(f"{org_name} {ch_name}")
        amz = f"https://www.amazon.co.jp/s?k={search}&tag={AMAZON_ID}"
        rak = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search}%2F"

        return f"""
        <div class="card">
            <div class="thumb-container">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" class="thumb" loading="lazy">
                <div class="view-badge">👀 {views:,} views</div>
            </div>
            <div class="info">
                <div class="ch-name">👤 {ch_name}</div>
                <div class="video-title">{title}</div>
                {music_html}
                <div class="ai-comment">🤖 {ai_txt}</div>
                <div class="links">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn-link btn-yt">YouTubeで視聴する</a>
                    <a href="{amz}" target="_blank" class="btn-link btn-amz">Amazon</a>
                    <a href="{rak}" target="_blank" class="btn-link btn-rak">楽天市場</a>
                </div>
            </div>
        </div>"""
    # -----------------------

    # ホロライブ100件を表示
    for v in v_hololive:
        html_content += create_card(v, "ホロライブ")

    html_content += """
            </div> <div id="stars" class="video-list">
    """

    # スターズ100件を表示
    for v in v_holostars:
        html_content += create_card(v, "ホロスターズ")

    html_content += f"""
            </div> </div>
        <footer style="text-align: center; padding: 100px; color: #a0aec0;">
            © {datetime.now().year} {SITE_NAME} | AI Analysis Fan Project
        </footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
