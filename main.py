import os
import requests
from google import genai
from datetime import datetime
import urllib.parse
import time

# ==========================================
# 🌟 ID固定設定（設定済み）
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_resilient(org_name):
    """
    重い '/videos' ではなく、比較的軽い '/live' エンドポイントを試す
    """
    # 案1: ライブ配信・予約枠を優先して取得（サーバー負荷が低い）
    url = "https://holodex.net/api/v2/live"
    params = {"org": org_name, "limit": 50}
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    try:
        res = requests.get(url, params=params, headers=headers, timeout=20)
        
        # もし '/live' も500エラーなら、一応 '/videos' も再試行
        if res.status_code != 200:
            url_alt = "https://holodex.net/api/v2/videos"
            params_alt = {"org": org_name, "limit": 20, "sort": "view_count", "order": "desc"}
            res = requests.get(url_alt, params=params_alt, headers=headers, timeout=20)

        if res.status_code == 200:
            data = res.json()
            return (data if isinstance(data, list) else []), "Success"
        
        return None, f"Server Still Busy ({res.status_code})"
    except Exception as e:
        return None, f"Connection Failed: {str(e)}"

def main():
    list_holo, msg_holo = fetch_resilient("Hololive")
    time.sleep(1)
    list_stars, msg_stars = fetch_resilient("Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    def make_card(v, org_label):
        if not v or not isinstance(v, dict): return ""
        v_id = v.get('id')
        title = v.get('title', 'No Title')
        ch_name = v.get('channel', {}).get('name', 'Unknown')
        views = v.get('view_count', 0)
        
        # AI解析
        desc = "注目情報をチェック！"
        try:
            prompt = f"15文字以内でこの動画を紹介して: {title}"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text: desc = res.text.strip()
        except: pass

        query = urllib.parse.quote(f"{org_label} {ch_name}")
        return f"""
        <div class="card" style="background:white; border-radius:12px; border:1px solid #e2e8f0; overflow:hidden;">
            <div style="position:relative; aspect-ratio:16/9; background:black;">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" style="width:100%; height:100%; object-fit:cover;">
                <div style="position:absolute; bottom:5px; right:5px; background:rgba(0,0,0,0.8); color:white; font-size:10px; padding:2px 6px; border-radius:4px;">👀 {views:,}</div>
            </div>
            <div style="padding:15px;">
                <div style="font-size:12px; color:#00b5d8; font-weight:bold;">{ch_name}</div>
                <div style="font-size:13px; font-weight:bold; height:3em; overflow:hidden; margin:5px 0;">{title}</div>
                <div style="font-size:11px; color:#64748b; font-style:italic;">🤖 {desc}</div>
                <div style="display:flex; gap:5px; margin-top:10px;">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" style="flex:1; background:#00b5d8; color:white; text-decoration:none; font-size:10px; text-align:center; padding:8px; border-radius:6px; font-weight:bold;">Watch</a>
                    <a href="https://www.amazon.co.jp/s?k={query}&tag={AMAZON_ID}" target="_blank" style="flex:1; background:#f1f5f9; color:#475569; text-decoration:none; font-size:10px; text-align:center; padding:8px; border-radius:6px;">Amazon</a>
                </div>
            </div>
        </div>
        """

    content_holo = "".join([make_card(v, "ホロライブ") for v in list_holo]) if list_holo else f"<p style='grid-column:1/-1; text-align:center; padding:50px;'>⚠️ {msg_holo}<br>サーバー混雑中のため、少し時間をおいてください。</p>"
    content_stars = "".join([make_card(v, "ホロスターズ") for v in list_stars]) if list_stars else f"<p style='grid-column:1/-1; text-align:center; padding:50px;'>⚠️ {msg_stars}</p>"

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <style>
            body {{ font-family: sans-serif; background:#f8fafc; margin:0; display:flex; height:100vh; }}
            nav {{ width:200px; background:white; border-right:1px solid #e2e8f0; padding-top:20px; }}
            .nav-item {{ padding:15px 20px; cursor:pointer; color:#64748b; font-weight:bold; font-size:14px; }}
            .nav-item.active {{ background:#f0f9ff; color:#00b5d8; border-left:4px solid #00b5d8; }}
            main {{ flex:1; overflow-y:auto; padding:20px; }}
            .grid {{ display:none; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:20px; }}
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
            <div style="padding:0 20px 20px; font-size:24px; font-weight:bold; color:#00b5d8;">{SITE_NAME}</div>
            <div id="btn-holo" class="nav-item active" onclick="tab('holo')">Hololive</div>
            <div id="btn-stars" class="nav-item" onclick="tab('stars')">Holostars</div>
        </nav>
        <main>
            <div style="font-size:12px; color:#64748b; margin-bottom:20px;">更新: {datetime.now().strftime('%H:%M')}</div>
            <div id="holo" class="grid active">{content_holo}</div>
            <div id="stars" class="grid">{content_stars}</div>
        </main>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    main()
