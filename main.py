import os
import requests
from google import genai
from datetime import datetime

# ==========================================
# 🌟 設定済みID（スクリーンショットより）
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_videos(org):
    """APIから再生数順に動画を取得する（不完全なデータは除外）"""
    url = "https://holodex.net/api/v2/videos"
    results = []
    # 50件ずつ2回取得して合計100件を狙う
    for offset in [0, 50]:
        params = {
            "org": org, "limit": 50, "offset": offset,
            "sort": "view_count", "order": "desc", "type": "stream,clip"
        }
        try:
            res = requests.get(url, params=params, headers={"X-APIKEY": HOLODEX_API_KEY}, timeout=10)
            data = res.json()
            if isinstance(data, list):
                # 辞書形式でない不純なデータをこの時点で排除
                results.extend([v for v in data if isinstance(v, dict) and isinstance(v.get('channel'), dict)])
        except:
            continue
    return results

def main():
    # 1. データの取得（個別に取得することで表示漏れを防ぐ）
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
        <title>{SITE_NAME} | ポータル</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #f0f4f8; --side: #ffffff; --card: #ffffff;
                --text: #2d3748; --sub: #718096; --accent: #00b5d8;
                --stars: #fba919; --music: #9f7aea; --border: #e2e8f0;
            }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--bg); color: var(--text); margin: 0; display: flex; height: 100vh; overflow: hidden; }}
            nav {{ width: 200px; background: var(--side); border-right: 1px solid var(--border); display: flex; flex-direction: column; padding-top: 20px; flex-shrink: 0; }}
            .logo {{ padding: 0 20px 30px; font-size: 22px; font-weight: 900; color: var(--accent); }}
            .nav-item {{ padding: 12px 20px; cursor: pointer; color: var(--sub); font-size: 14px; font-weight: bold; border-left: 4px solid transparent; transition: 0.2s; }}
            .nav-item:hover {{ background: #f7fafc; }}
            .nav-item.active {{ background: #ebf8ff; color: var(--accent); border-left-color: var(--accent); }}
            .nav-stars.active {{ background: #fffaf0; color: var(--stars); border-left-color: var(--stars); }}
            main {{ flex: 1; overflow-y: auto; padding: 25px; }}
            .top-bar {{ display: flex; justify-content: space-between; margin-bottom: 25px; font-size: 13px; color: var(--sub); border-bottom: 1px solid var(--border); padding-bottom: 10px; font-weight: bold; }}
            .grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }}
            .grid.active {{ display: grid; }}
            .card {{ background: var(--card); border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid var(--border); display: flex; flex-direction: column; transition: 0.2s; }}
            .card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 15px rgba(0,0,0,0.1); }}
            .thumb-box {{ position: relative; aspect-ratio: 16/9; background: #000; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .v-badge {{ position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.8); color: white; font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: bold; }}
            .info {{ padding: 15px; flex-grow: 1; display: flex; flex-direction: column; }}
            .title {{ font-size: 14px; font-weight: bold; line-height: 1.5; height: 3em; overflow: hidden; margin-bottom: 8px; }}
            .ch {{ font-size: 12px; color: var(--sub); margin-bottom: 12px; font-weight: bold; }}
            .music-tag {{ color: var(--music); font-size: 11px; font-weight: 900; margin-bottom: 4px; border-top: 1px solid var(--border); padding-top: 10px; }}
            .ai-desc {{ font-size: 11px; color: var(--sub); font-style: italic; }}
            .links {{ display: flex; gap: 8px; margin-top: auto; padding-top: 15px; }}
            .btn {{ flex: 1; text-decoration: none; font-size: 11px; font-weight: 900; text-align: center; padding: 8px; border-radius: 8px; color: var(--sub); background: #f1f5f9; transition: 0.2s; }}
            .btn:hover {{ background: #e2e8f0; }}
            .btn-watch {{ background: var(--accent); color: white; }}
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
            <div id="btn-holo" class="nav-item active" onclick="tab('holo')">Hololive TOP 100</div>
            <div id="btn-stars" class="nav-item nav-stars" onclick="tab('stars')">Holostars TOP 100</div>
        </nav>
        <main>
            <div class="top-bar">
                <span>再生数上位ポータル × AI楽曲解析</span>
                <span>最終更新: {datetime.now().strftime('%m/%d %H:%M')}</span>
            </div>
            <div id="holo" class="grid active">
    """

    def create_card(v, org_name, accent_color):
        """動画カードを1枚ずつ安全に作成（エラー耐性強化）"""
        try:
            v_id = v.get('id')
            title = v.get('title', 'No Title')
            views = v.get('view_count', 0)
            ch_name = v.get('channel', {}).get('name', 'Unknown')
            
            if not v_id: return ""

            # AI解析
            prompt = f"Music: [Song - Artist] or [None]. Summary: 15 chars. Format: Music|Summary. Title: {title}"
            try:
                res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                parts = res.text.strip().split('|')
                m_val, ai_txt = (parts[0].strip(), parts[1].strip()) if len(parts) > 1 else ("None", "最新情報をチェック")
            except:
                m_val, ai_txt = "None", "詳細分析中"

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
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{q}%2F" target="_blank" class="btn">楽天市場</a>
                    </div>
                </div>
            </div>"""
        except:
            return ""

    # ホロライブ出力
    for v in v_holo:
        # スターズ混入防止
        if "stars" in str(v.get('channel', {}).get('sub_org', '')).lower(): continue
        html_content += create_card(v, "ホロライブ", "var(--accent)")
    
    html_content += """</div><div id="stars" class="grid">"""
    
    # スターズ出力
    for v in v_stars:
        html_content += create_card(v, "ホロスターズ", "var(--stars)")

    html_content += """</div></main></body></html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
