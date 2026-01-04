import os
import requests
from google import genai
from datetime import datetime
import urllib.parse

# ==========================================
# 🌟 設定済みID（固定）
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_safe(org):
    """APIからデータを取得し、辞書形式でない不純物を完全に除去する"""
    url = "https://holodex.net/api/v2/videos"
    params = {
        "org": org, "limit": 50, "sort": "view_count", 
        "order": "desc", "type": "stream,clip"
    }
    try:
        res = requests.get(url, params=params, headers={"X-APIKEY": HOLODEX_API_KEY}, timeout=15)
        data = res.json()
        # APIがエラーメッセージ（文字列）を返してきた場合のガード
        if not isinstance(data, list):
            return []
        # 各要素が辞書であることを確認
        return [v for v in data if isinstance(v, dict)]
    except:
        return []

def main():
    # 1. データの取得
    list_holo = fetch_safe("Hololive")
    list_stars = fetch_safe("Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    def make_card_html(v, org_tag):
        """1つの動画カードを生成。少しでもデータが変ならそのカードだけ飛ばす。"""
        try:
            # v自体が辞書か、channelキーが辞書か、idがあるかを厳格にチェック
            if not isinstance(v, dict): return ""
            channel = v.get('channel')
            if not isinstance(channel, dict): return ""
            
            v_id = v.get('id')
            if not v_id: return ""
            
            title = v.get('title', 'No Title')
            views = v.get('view_count', 0)
            ch_name = channel.get('name', 'Unknown')

            # AI解析（ここも失敗したらデフォルト値を出す）
            m_info, ai_desc = "None", "分析中..."
            try:
                prompt = f"Extract if music: [Song - Artist]. Summary: 15 chars. Format: Music|Summary. Title: {title}"
                res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                if res and res.text:
                    parts = res.text.strip().split('|')
                    m_info = parts[0].strip()
                    ai_desc = parts[1].strip() if len(parts) > 1 else "注目の配信"
            except: pass

            m_html = f'<div class="music-tag" style="color:#8b5cf6; font-size:11px; font-weight:bold; margin-bottom:5px;">🎵 {m_info}</div>' if "None" not in m_info else ""
            query = urllib.parse.quote(f"{org_tag} {ch_name}")

            return f"""
            <div class="card" style="background:#fff; border-radius:12px; border:1px solid #e2e8f0; overflow:hidden; display:flex; flex-direction:column; transition:0.2s;">
                <div style="position:relative; aspect-ratio:16/9; background:#000;">
                    <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" style="width:100%; height:100%; object-fit:cover;" loading="lazy">
                    <div style="position:absolute; bottom:8px; right:8px; background:rgba(0,0,0,0.8); color:#fff; font-size:11px; padding:3px 8px; border-radius:6px;">👀 {views:,} views</div>
                </div>
                <div style="padding:15px; flex-grow:1; display:flex; flex-direction:column;">
                    <div style="font-size:14px; font-weight:bold; height:3em; overflow:hidden; margin-bottom:8px;">{title}</div>
                    <div style="font-size:12px; color:#64748b; margin-bottom:10px;">👤 {ch_name}</div>
                    {m_html}
                    <div style="font-size:11px; color:#64748b; font-style:italic;">🤖 {ai_desc}</div>
                    <div style="display:flex; gap:5px; margin-top:auto; padding-top:15px;">
                        <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" style="flex:1; text-decoration:none; font-size:10px; font-weight:bold; text-align:center; padding:8px; border-radius:6px; color:#fff; background:#0ea5e9;">Watch</a>
                        <a href="https://www.amazon.co.jp/s?k={query}&tag={AMAZON_ID}" target="_blank" style="flex:1; text-decoration:none; font-size:10px; font-weight:bold; text-align:center; padding:8px; border-radius:6px; color:#475569; background:#f1f5f9;">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{query}%2F" target="_blank" style="flex:1; text-decoration:none; font-size:10px; font-weight:bold; text-align:center; padding:8px; border-radius:6px; color:#475569; background:#f1f5f9;">楽天</a>
                    </div>
                </div>
            </div>"""
        except: return ""

    content_holo = "".join([make_card_html(v, "ホロライブ") for v in list_holo])
    content_stars = "".join([make_card_html(v, "ホロスターズ") for v in list_stars])

    # 最終HTML
    full_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{SITE_NAME}</title>
    <style>
        body {{ font-family: sans-serif; background:#f8fafc; color:#1e293b; margin:0; display:flex; height:100vh; overflow:hidden; }}
        nav {{ width:200px; background:#fff; border-right:1px solid #e2e8f0; display:flex; flex-direction:column; padding-top:20px; flex-shrink:0; }}
        .nav-item {{ padding:15px 20px; cursor:pointer; color:#64748b; font-weight:bold; font-size:14px; border-left:4px solid transparent; }}
        .nav-item.active {{ background:#f0f9ff; color:#0ea5e9; border-left-color:#0ea5e9; }}
        main {{ flex:1; overflow-y:auto; padding:25px; }}
        .grid {{ display:none; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:20px; }}
        .grid.active {{ display:grid; }}
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
        <div style="padding:0 20px 30px; font-size:24px; font-weight:bold; color:#0ea5e9;">Navi</div>
        <div id="btn-holo" class="nav-item active" onclick="tab('holo')">Hololive TOP 50</div>
        <div id="btn-stars" class="nav-item" onclick="tab('stars')">Holostars TOP 50</div>
    </nav>
    <main>
        <div class="grid active" id="holo">{content_holo if content_holo else "<p>Hololiveのデータがありません</p>"}</div>
        <div class="grid" id="stars">{content_stars if content_stars else "<p>Holostarsのデータがありません</p>"}</div>
    </main>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    main()
