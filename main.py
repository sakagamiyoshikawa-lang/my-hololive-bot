import os
import requests
from google import genai
from datetime import datetime

# ==========================================
# 🌟 ID設定済み（固定）
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_top_100(org):
    """API上限を考慮し、特定の組織から再生数上位100件を確実に取得する"""
    url = "https://holodex.net/api/v2/videos"
    combined = []
    # 50件ずつ2回に分けて取得（offsetを使用）
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
                combined.extend(data)
        except:
            continue
    return combined

def main():
    # 1. 各グループから100件ずつ、計200件を取得
    raw_holo = fetch_top_100("Hololive")
    raw_stars = fetch_top_100("Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTMLヘッダー（JavaScriptの波括弧 {{ }} をエスケープ）
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} | Holodex Clone Portal</title>
        <style>
            :root {{
                --bg-body: #0f0f0f; --bg-sidebar: #121212; --bg-card: #1c1c1c;
                --text-main: #ffffff; --text-sub: #aaaaaa; --accent: #00c2ff;
                --stars: #ffb800; --music: #bb86fc;
            }}
            body {{
                font-family: "Roboto", Arial, sans-serif; background-color: var(--bg-body); 
                color: var(--text-main); margin: 0; display: flex; overflow: hidden;
            }}
            
            /* 本家風サイドバー */
            nav {{
                width: 200px; height: 100vh; background: var(--bg-sidebar); 
                border-right: 1px solid #333; flex-shrink: 0; padding-top: 20px;
            }}
            .nav-logo {{
                padding: 0 20px 30px; font-size: 22px; font-weight: 900; color: var(--accent);
                text-decoration: none; display: block;
            }}
            .nav-item {{
                padding: 12px 20px; cursor: pointer; color: var(--text-sub); font-size: 14px;
                font-weight: bold; transition: 0.2s; border-left: 4px solid transparent;
            }}
            .nav-item:hover {{ background: #222; color: #fff; }}
            .nav-item.active {{ background: #262626; color: var(--accent); border-left-color: var(--accent); }}
            .nav-item-stars.active {{ color: var(--stars); border-left-color: var(--stars); }}

            /* メインエリア */
            main {{ flex: 1; height: 100vh; overflow-y: auto; padding: 20px; }}
            .top-bar {{ display: flex; justify-content: space-between; margin-bottom: 20px; font-size: 14px; color: var(--text-sub); }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }}

            /* 本家風カード */
            .card {{ background: var(--bg-card); border-radius: 8px; overflow: hidden; transition: transform 0.2s; }}
            .card:hover {{ transform: scale(1.02); background: #2a2a2a; }}
            .thumb-box {{ position: relative; aspect-ratio: 16/9; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .v-badge {{ position: absolute; bottom: 4px; right: 4px; background: rgba(0,0,0,0.8); font-size: 11px; padding: 2px 6px; border-radius: 4px; }}

            .info {{ padding: 12px; }}
            .video-title {{ font-size: 13px; font-weight: bold; line-height: 1.4; height: 2.8em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 6px; }}
            .ch-name {{ font-size: 12px; color: var(--text-sub); margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            
            /* AI・楽曲情報セクション */
            .ai-section {{ border-top: 1px solid #333; padding-top: 8px; margin-top: 8px; }}
            .music-tag {{ color: var(--music); font-size: 11px; font-weight: bold; margin-bottom: 4px; }}
            .ai-text {{ font-size: 11px; color: #888; line-height: 1.3; font-style: italic; }}

            .links {{ display: flex; gap: 8px; margin-top: 12px; }}
            .btn {{ flex: 1; text-decoration: none; font-size: 10px; font-weight: bold; text-align: center; padding: 6px; border-radius: 4px; color: #fff; background: #333; transition: 0.2s; }}
            .btn:hover {{ filter: brightness(1.3); }}
            .btn-yt {{ background: var(--accent); }}

            @media (max-width: 600px) {{
                nav {{ width: 60px; }} .nav-text {{ display: none; }}
            }}
        </style>
        <script>
            function switchTab(id) {{
                document.querySelectorAll('.video-list').forEach(el => el.style.display = 'none');
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                document.getElementById(id).style.display = 'grid';
                document.getElementById('btn-' + id).classList.add('active');
            }}
        </script>
    </head>
    <body onload="switchTab('holo')">
        <nav>
            <a href="#" class="nav-logo">HoloNavi</a>
            <div id="btn-holo" class="nav-item active" onclick="switchTab('holo')">
                <span class="nav-text">Hololive TOP 100</span>
            </div>
            <div id="btn-stars" class="nav-item nav-item-stars" onclick="switchTab('stars')">
                <span class="nav-text">Holostars TOP 100</span>
            </div>
        </nav>
        <main>
            <div class="top-bar">
                <span>再生数上位コンテンツをAIが解析</span>
                <span>最終更新: {datetime.now().strftime('%m/%d %H:%M')}</span>
            </div>

            <div id="holo" class="video-list grid">
    """

    def create_card_html(v, org_tag_name, accent_color):
        """1つの動画カードを安全に生成する"""
        try:
            # データ形式チェック（channelが文字列の場合はスキップ）
            channel = v.get('channel')
            if not isinstance(channel, dict): return ""
            
            ch_name = channel.get('name', 'Unknown')
            v_id = v.get('id')
            title = v.get('title', 'No Title')
            views = v.get('view_count', 0)
            if not v_id: return ""

            # Geminiによる解析
            prompt = f"Extract if music: [Song - Artist]. If not: [None]. Write 15-char catchphrase. Format: Music|Summary. Title: {title}"
            try:
                res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                ai_data = res.text.strip().split('|')
                music_info = ai_data[0].strip()
                ai_desc = ai_data[1].strip() if len(ai_data) > 1 else "注目の配信情報を分析"
            except:
                music_info, ai_desc = "None", "最新情報をチェック！"

            music_html = f'<div class="music-tag">🎵 {music_info}</div>' if "None" not in music_info else ""
            q = requests.utils.quote(f"{org_tag_name} {ch_name}")

            return f"""
            <div class="card">
                <div class="thumb-box">
                    <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" class="thumb" loading="lazy">
                    <div class="v-badge">{views:,} views</div>
                </div>
                <div class="info">
                    <div class="video-title">{title}</div>
                    <div class="ch-name">{ch_name}</div>
                    <div class="ai-section">
                        {music_html}
                        <div class="ai-text">🤖 {ai_desc}</div>
                    </div>
                    <div class="links">
                        <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-yt" style="background:{accent_color}">Watch</a>
                        <a href="https://www.amazon.co.jp/s?k={q}&tag={AMAZON_ID}" target="_blank" class="btn">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{q}%2F" target="_blank" class="btn">Rakuten</a>
                    </div>
                </div>
            </div>"""
        except:
            return ""

    # ホロライブカード生成
    for v in raw_holo:
        # スターズ混入防止
        sub = v.get('channel', {}).get('sub_org', '')
        if "stars" in str(sub).lower(): continue
        html_content += create_card_html(v, "ホロライブ", "var(--accent)")

    html_content += """</div><div id="stars" class="video-list grid" style="display:none;">"""

    # スターズカード生成
    for v in raw_stars:
        html_content += create_card_html(v, "ホロスターズ", "var(--stars)")

    html_content += """</main></body></html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
