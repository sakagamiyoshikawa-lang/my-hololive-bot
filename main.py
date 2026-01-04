import os
import requests
from google import genai
from datetime import datetime

# ==========================================
# 🌟 ID固定設定済み
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    # 1. 再生数上位100件を取得（limitはAPIの最大値50のため、2回に分けて取得するか、一括取得可能なエンドポイントを選択）
    # ここでは安定性を重視し、最新かつ人気の高い動画を最大100件取得する設定にします
    url = "https://holodex.net/api/v2/videos"
    params = {
        "org": "Hololive", 
        "limit": 100, 
        "sort": "view_count", # 再生数順
        "order": "desc",
        "type": "stream,clip" # 配信と切り抜きを対象
    }
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    response = requests.get(url, params=params, headers=headers)
    videos = response.json()

    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTML構築
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} | 再生数TOP100 AI解析ポータル</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00c2ff; --sub: #ff66b2; --stars: #ffb800; --dark: #1a202c; --light: #f0f4f8; --music: #7e57c2; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--light); margin: 0; color: var(--dark); }}
            header {{ background: linear-gradient(135deg, #00c2ff 0%, #ff66b2 100%); color: white; padding: 50px 20px; text-align: center; }}
            .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
            
            /* グループ切り替えスイッチ */
            .main-tabs {{ display: flex; justify-content: center; margin: -30px 0 30px; position: relative; z-index: 10; }}
            .m-tab {{ padding: 15px 40px; border: none; background: white; cursor: pointer; font-weight: 900; font-size: 1.1rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: 0.3s; }}
            .m-tab:first-child {{ border-radius: 50px 0 0 50px; border-right: 1px solid #eee; }}
            .m-tab:last-child {{ border-radius: 0 50px 50px 0; }}
            .m-tab.active {{ background: var(--main); color: white; }}
            .m-tab-stars.active {{ background: var(--stars); }}

            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 25px; }}
            .video-card {{ display: none; }}
            .video-card.show {{ display: flex; flex-direction: column; }}

            .card {{ background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.05); transition: 0.3s; height: 100%; }}
            .card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            
            .thumb-container {{ position: relative; aspect-ratio: 16/9; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .view-count {{ position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.8); color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }}
            
            .info {{ padding: 15px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 0.85rem; font-weight: bold; color: var(--main); margin-bottom: 5px; }}
            .video-title {{ font-weight: bold; font-size: 0.95rem; line-height: 1.4; margin-bottom: 10px; height: 2.8em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
            
            /* 楽曲・AI解析セクション */
            .music-box {{ background: #f3e5f5; border-radius: 10px; padding: 10px; margin-bottom: 10px; border-left: 4px solid var(--music); }}
            .music-label {{ font-size: 0.7rem; font-weight: bold; color: var(--music); display: block; }}
            .music-info {{ font-size: 0.85rem; font-weight: bold; color: #4a148c; }}
            
            .ai-desc {{ font-size: 0.8rem; color: #555; background: #f9f9f9; padding: 8px; border-radius: 8px; margin-bottom: 15px; }}
            
            .links {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: auto; }}
            .btn {{ text-decoration: none; padding: 8px; border-radius: 8px; font-size: 0.75rem; font-weight: bold; text-align: center; }}
            .btn-amz {{ background: #ff9900; color: white; }}
            .btn-rak {{ background: #bf0000; color: white; }}
        </style>
        <script>
            function switchGroup(group) {{
                document.querySelectorAll('.m-tab').forEach(t => t.classList.remove('active'));
                document.getElementById('tab-' + group).classList.add('active');
                document.querySelectorAll('.video-card').forEach(c => {{
                    if(c.dataset.group === group) c.classList.add('show');
                    else c.classList.remove('show');
                }});
            }}
        </script>
    </head>
    <body onload="switchGroup('hololive')">
        <header>
            <h1>🌟 {SITE_NAME}</h1>
            <p>再生数TOP100 × AI楽曲解析ポータル</p>
        </header>
        <div class="container">
            <div class="main-tabs">
                <button id="tab-hololive" class="m-tab active" onclick="switchGroup('hololive')">HOLOLIVE</button>
                <button id="tab-holostars" class="m-tab m-tab-stars" onclick="switchGroup('holostars')">HOLOSTARS</button>
            </div>
            <div class="grid">
    """

    for v in videos:
        # Holostarsかどうかの正確な判定
        sub_org = v['channel'].get('sub_org', '')
        group = "holostars" if "stars" in sub_org.lower() else "hololive"
        
        v_id, title, ch_name = v['id'], v['title'], v['channel']['name']
        views = v.get('view_count', 0)

        # AI解析：楽曲情報と紹介文を同時に取得
        prompt = (
            f"以下を解析して。1.音楽系なら[曲名 - アーティスト名]、違えば[なし]。"
            f"2.ファンの興味を惹く紹介文を15文字で。形式: 曲情報 | 紹介文。タイトル: {title}"
        )
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            ai_data = res.text.strip().split('|')
            song_info = ai_data[0].strip()
            desc = ai_data[1].strip() if len(ai_data) > 1 else "注目の配信をチェック！"
        except:
            song_info, desc = "なし", "人気配信をナビゲート"

        search = requests.utils.quote(f"ホロライブ {ch_name}")
        amz_url = f"https://www.amazon.co.jp/s?k={search}&tag={AMAZON_ID}"
        org_search = "ホロライブ" if group == "hololive" else "ホロスターズ"
        rak_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{org_search}%20{requests.utils.quote(ch_name)}%2F"

        music_html = f'<div class="music-box"><span class="music-label">🎵 楽曲情報</span><div class="music-info">{song_info}</div></div>' if "なし" not in song_info else ""

        html_content += f"""
        <div class="video-card card" data-group="{group}">
            <div class="thumb-container">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" class="thumb">
                <div class="view-count">👀 {views:,} views</div>
            </div>
            <div class="info">
                <div class="ch-name">👤 {ch_name}</div>
                <div class="video-title">{title}</div>
                {music_html}
                <div class="ai-desc">🤖 {desc}</div>
                <div class="links">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-amz" style="grid-column: span 2; background: #222; margin-bottom: 5px;">動画を視聴</a>
                    <a href="{amz_url}" target="_blank" class="btn btn-amz">Amazon</a>
                    <a href="{rak_url}" target="_blank" class="btn btn-rak">楽天市場</a>
                </div>
            </div>
        </div>"""

    html_content += f"""
            </div>
        </div>
        <footer style="text-align: center; padding: 40px; color: #999;">© {datetime.now().year} {SITE_NAME}</footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    main()
