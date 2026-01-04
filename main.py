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
    # 1. Holodexからデータ取得（HololiveとHolostarsの両方を取得するため件数を50にアップ）
    url = "https://holodex.net/api/v2/videos"
    # 特定のグループを指定せず、上位組織として取得して後で振り分ける
    params = {
        "org": "Hololive", 
        "limit": 50, 
        "sort": "published_at", 
        "order": "desc", 
        "type": "placeholder,stream,clip"
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
        <title>{SITE_NAME} | AIホロライブ・スターズ最新ポータル</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00c2ff; --sub: #ff66b2; --stars: #ffb800; --dark: #1a202c; --light: #f7fafc; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--light); margin: 0; color: var(--dark); line-height: 1.6; }}
            
            header {{ 
                background: linear-gradient(135deg, var(--main) 0%, var(--sub) 100%); 
                color: white; padding: 60px 20px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.15); 
            }}
            header h1 {{ margin: 0; font-size: 3rem; font-weight: 900; letter-spacing: -1px; text-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
            
            .container {{ max-width: 1200px; margin: 30px auto; padding: 0 20px; }}

            /* フィルターセクション */
            .filter-box {{ background: white; padding: 20px; border-radius: 20px; shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 30px; text-align: center; }}
            .filter-group {{ margin-bottom: 15px; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }}
            .filter-label {{ font-size: 0.8rem; font-weight: bold; color: #999; display: block; margin-bottom: 8px; width: 100%; }}

            .btn-filter {{ 
                padding: 10px 20px; border: 2px solid #eee; background: white; cursor: pointer; border-radius: 50px; 
                font-weight: bold; transition: 0.3s; color: #666;
            }}
            .btn-filter.active {{ border-color: var(--main); background: var(--main); color: white; }}
            .btn-stars.active {{ border-color: var(--stars); background: var(--stars); color: white; }}

            /* カード表示制御 */
            .video-card {{ display: none; }}
            .video-card.show {{ display: flex; flex-direction: column; }}

            /* グリッドレイアウト */
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 30px; }}

            /* カードデザイン */
            .card {{ background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); transition: 0.3s; height: 100%; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,0,0,0.12); }}
            .thumb-container {{ position: relative; width: 100%; aspect-ratio: 16/9; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            
            .badge {{ position: absolute; top: 12px; left: 12px; padding: 4px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: bold; color: white; background: rgba(0,0,0,0.7); }}
            .org-badge {{ position: absolute; top: 12px; right: 12px; padding: 4px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: bold; color: white; }}
            .badge-holo {{ background: var(--main); }}
            .badge-stars {{ background: var(--stars); }}
            .live {{ background: #e53e3e !important; }}
            
            .info {{ padding: 20px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 0.9rem; font-weight: bold; color: #4a5568; margin-bottom: 8px; }}
            .cat-tag {{ display: inline-block; background: var(--sub); color: white; padding: 2px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; margin-bottom: 10px; align-self: flex-start; }}
            .video-title {{ font-weight: bold; font-size: 1.05rem; color: var(--dark); margin-bottom: 12px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 2.8em; }}
            .ai-desc {{ background: #f1f5f9; padding: 15px; border-radius: 12px; font-size: 0.9rem; color: #475569; margin-bottom: 20px; border-left: 4px solid var(--main); flex-grow: 1; font-weight: bold; }}
            
            .links {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: auto; }}
            .btn {{ text-decoration: none; padding: 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; text-align: center; transition: 0.2s; }}
            .btn-yt {{ background: var(--dark); color: white; grid-column: span 2; margin-bottom: 5px; }}
            .btn-amz {{ background: #ff9900; color: white; }}
            .btn-rak {{ background: #bf0000; color: white; }}
            
            footer {{ text-align: center; padding: 60px 20px; background: white; margin-top: 60px; color: #a0aec0; border-top: 1px solid #edf2f7; }}
        </style>
        <script>
            let currentOrg = 'all';
            let currentLang = 'ja';

            function filterVideos(type, value) {{
                if (type === 'org') currentOrg = value;
                if (type === 'lang') currentLang = value;

                // ボタンの見た目を更新
                document.querySelectorAll('.btn-org').forEach(b => b.classList.remove('active'));
                document.getElementById('org-' + currentOrg).classList.add('active');
                document.querySelectorAll('.btn-lang').forEach(b => b.classList.remove('active'));
                document.getElementById('lang-' + currentLang).classList.add('active');

                // カードの表示切り替え
                document.querySelectorAll('.video-card').forEach(card => {{
                    const matchOrg = (currentOrg === 'all' || card.dataset.org === currentOrg);
                    const matchLang = card.dataset.lang === currentLang;
                    if (matchOrg && matchLang) {{
                        card.classList.add('show');
                    }} else {{
                        card.classList.remove('show');
                    }}
                }});
            }}
        </script>
    </head>
    <body onload="filterVideos('lang', 'ja')">
        <header>
            <h1>🌟 {SITE_NAME}</h1>
            <p style="font-weight: bold; opacity: 0.9;">AI解析 | 推し活を加速させる最新ポータル</p>
        </header>

        <div class="container">
            <div class="filter-box">
                <div class="filter-group">
                    <span class="filter-label">グループを選択</span>
                    <button id="org-all" class="btn-filter btn-org active" onclick="filterVideos('org', 'all')">すべて表示</button>
                    <button id="org-hololive" class="btn-filter btn-org" onclick="filterVideos('org', 'hololive')">ホロライブのみ</button>
                    <button id="org-holostars" class="btn-filter btn-org btn-stars" onclick="filterVideos('org', 'holostars')">ホロスターズのみ</button>
                </div>
                <div class="filter-group">
                    <span class="filter-label">言語を選択</span>
                    <button id="lang-ja" class="btn-filter btn-lang active" onclick="filterVideos('lang', 'ja')">🇯🇵 日本語</button>
                    <button id="lang-en" class="btn-filter btn-lang" onclick="filterVideos('lang', 'en')">🇺🇸 English</button>
                    <button id="lang-id" class="btn-filter btn-lang" onclick="filterVideos('lang', 'id')">🇮🇩 Indonesia</button>
                </div>
            </div>

            <div class="grid">
    """

    for v in videos:
        title, v_id, ch_name = v['title'], v['id'], v['channel']['name']
        lang = v.get('lang', 'ja')
        # 所属判定
        org_type = "holostars" if "Holostars" in v['channel'].get('sub_org', '') or "HOLOSTARS" in v['channel'].get('name', '').upper() else "hololive"
        org_label = "HOLO" if org_type == "hololive" else "STARS"
        org_class = "badge-holo" if org_type == "hololive" else "badge-stars"

        status = v.get('status', 'upcoming')
        status_label, status_class = ("LIVE中", "live") if status == "live" else ("予約枠", "") if status == "upcoming" else ("アーカイブ", "")
        
        # AI解析
        prompt = f"Categorize into [Original Song, Cover Song, Singing Stream, Other] and write a short catchphrase. Format: Category | Catchphrase. Title: {title}"
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            ai = res.text.strip().split('|')
            cat, desc = (ai[0].strip(), ai[1].strip()) if len(ai) > 1 else ("Other", "最新情報をチェック！")
        except:
            cat, desc = "Other", "配信情報をチェックしよう！"

        search = requests.utils.quote(f"ホロライブ {ch_name}")
        amz_url = f"https://www.amazon.co.jp/s?k={search}&tag={AMAZON_ID}"
        # 楽天市場の検索クエリを「ホロライブ」または「ホロスターズ」に合わせて最適化
        org_search = "ホロライブ" if org_type == "hololive" else "ホロスターズ"
        rak_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{org_search}%20{requests.utils.quote(ch_name)}%2F"

        html_content += f"""
        <div class="video-card card" data-org="{org_type}" data-lang="{lang}">
            <div class="thumb-container">
                <img src="https://img.youtube.com/vi/{v_id}/maxresdefault.jpg" class="thumb" onerror="this.src='https://img.youtube.com/vi/{v_id}/mqdefault.jpg'">
                <div class="badge {status_class}">{status_label}</div>
                <div class="org-badge {org_class}">{org_label}</div>
            </div>
            <div class="info">
                <div class="ch-name">👤 {ch_name}</div>
                <span class="cat-tag">{cat}</span>
                <div class="video-title">{title}</div>
                <div class="ai-desc">🤖 {desc}</div>
                <div class="links">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-yt">視聴する</a>
                    <a href="{amz_url}" target="_blank" class="btn btn-amz">Amazon</a>
                    <a href="{rak_url}" target="_blank" class="btn btn-rak">楽天市場</a>
                </div>
            </div>
        </div>"""

    html_content += f"""
            </div>
        </div>
        <footer>
            <p>© {datetime.now().year} {SITE_NAME} | AI分析ポータル</p>
        </footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    main()
