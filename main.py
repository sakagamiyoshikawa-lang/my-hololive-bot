import os
import requests
from google import genai
from datetime import datetime

# ==========================================
# 🌟 ID固定設定（このままでOK！）
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ活ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    # 1. Holodexからデータ取得（情報量を確保するため30件に増量）
    url = "https://holodex.net/api/v2/videos"
    params = {
        "org": "Hololive", 
        "limit": 30, 
        "sort": "published_at", 
        "order": "desc", 
        "type": "placeholder,stream,clip"
    }
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    response = requests.get(url, params=params, headers=headers)
    videos = response.json()

    client = genai.Client(api_key=GEMINI_API_KEY)

    # HTMLヘッダー・デザイン（タブ機能付き）
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME} | AIが届けるホロライブ最新情報</title>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00c2ff; --sub: #ff66b2; --dark: #1a202c; --light: #f7fafc; }}
            body {{ font-family: 'Noto Sans JP', sans-serif; background: var(--light); margin: 0; color: var(--dark); line-height: 1.6; }}
            
            /* バナー風ヘッダー */
            header {{ background: linear-gradient(135deg, var(--main), var(--sub)); color: white; padding: 60px 20px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            header h1 {{ margin: 0; font-size: 3rem; font-weight: 900; letter-spacing: -1px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }}
            .hero-text {{ font-size: 1.2rem; margin-top: 10px; font-weight: bold; opacity: 0.9; }}
            
            .container {{ max-width: 1200px; margin: 30px auto; padding: 0 20px; }}

            /* 言語フィルター（タブ） */
            .tabs {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 30px; }}
            .tab-btn {{ padding: 10px 20px; border: none; background: #eee; cursor: pointer; border-radius: 8px; font-weight: bold; transition: 0.3s; }}
            .tab-btn.active {{ background: var(--main); color: white; }}
            .video-list {{ display: none; }} /* 初期は非表示 */
            .video-list.active {{ display: grid; }} /* activeクラスがついたら表示 */

            /* グリッド・カード */
            .grid {{ grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 30px; }}
            .card {{ background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); transition: 0.3s; display: flex; flex-direction: column; height: 100%; }}
            .card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,0,0,0.12); }}
            .thumb-container {{ position: relative; width: 100%; aspect-ratio: 16/9; }}
            .thumb {{ width: 100%; height: 100%; object-fit: cover; }}
            .status-badge {{ position: absolute; top: 12px; left: 12px; padding: 4px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: bold; color: white; background: rgba(0,0,0,0.7); }}
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
            .btn:hover {{ opacity: 0.8; filter: brightness(1.1); }}
            footer {{ text-align: center; padding: 60px 20px; background: white; margin-top: 60px; color: #a0aec0; border-top: 1px solid #edf2f7; }}
        </style>
        <script>
            // タブ切り替えのJavaScript
            function openTab(lang) {
                document.querySelectorAll('.video-list').forEach(list => list.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById(lang).classList.add('active');
                document.getElementById('btn-' + lang).classList.add('active');
            }
        </script>
    </head>
    <body onload="openTab('ja')"> <header>
            <h1>🌟 {SITE_NAME}</h1>
            <p class="hero-text">AIが最新のホロライブ配信を分析・ナビゲート</p>
            <div style="font-size: 0.8rem; color: rgba(255,255,255,0.8); margin-top: 15px;">最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </header>
        <div class="container">
            <div class="tabs">
                <button class="tab-btn" id="btn-ja" onclick="openTab('ja')">🇯🇵 日本語</button>
                <button class="tab-btn" id="btn-en" onclick="openTab('en')">🇺🇸 英語 (EN)</button>
                <button class="tab-btn" id="btn-id" onclick="openTab('id')">🇮🇩 インドネシア語 (ID)</button>
            </div>

            <div id="ja" class="video-list grid active"> """

    # 動画を言語ごとに仕分けるリスト
    videos_ja = []
    videos_en = []
    videos_id = []

    for v in videos:
        # Holodexの言語情報から仕分け
        lang = v.get('lang', 'ja') 
        if lang == 'ja': videos_ja.append(v)
        elif lang == 'en': videos_en.append(v)
        elif lang == 'id': videos_id.append(v)
        else: videos_ja.append(v) # その他の言語は日本語に入れておく

    # --- 動画カード生成関数 ---
    def create_video_card(v):
        title = v['title']
        v_id = v['id']
        ch_name = v['channel']['name']
        status = v.get('status', 'upcoming')
        
        status_label = "アーカイブ"
        status_class = ""
        if status == "live": status_label = "LIVE中"; status_class = "live"
        elif status == "upcoming": status_label = "予約枠"

        # AI解析（キャッチコピーを生成）
        prompt = f"Categorize into [Original Song, Cover Song, Singing Stream, Other] and write a short attractive catchphrase in Japanese. Format: Category | Catchphrase. Title: {title}"
        try:
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            ai_output = res.text.strip().split('|')
            cat = ai_output[0].strip()
            desc = ai_output[1].strip() if len(ai_output) > 1 else "推しの最新情報をチェック！"
        except:
            cat, desc = "Other", "配信情報をチェックしよう！"

        # 収益化リンク（楽天は「楽天市場」の公式グッズ検索に変更）
        search_query = requests.utils.quote(f"ホロライブ {ch_name}")
        amz_url = f"https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}"
        rak_url = f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2Fホロライブ公式%20{ch_name}%2F"

        return f"""
        <div class="card">
            <div class="thumb-container">
                <img src="https://img.youtube.com/vi/{v_id}/maxresdefault.jpg" class="thumb" onerror="this.src='https://img.youtube.com/vi/{v_id}/mqdefault.jpg'">
                <div class="status-badge {status_class}">{status_label}</div>
            </div>
            <div class="info">
                <div class="ch-name">👤 {ch_name}</div>
                <span class="cat-tag">{cat}</span>
                <div class="video-title">{title}</div>
                <div class="ai-desc">🤖 {desc}</div>
                <div class="links">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn btn-yt">YouTubeで視聴</a>
                    <a href="{amz_url}" target="_blank" class="btn btn-amz">Amazonグッズ</a>
                    <a href="{rak_url}" target="_blank" class="btn btn-rak">楽天市場グッズ</a>
                </div>
            </div>
        </div>
        """
    # -----------------------

    # 日本語の動画を表示
    for v in videos_ja:
        html_content += create_video_card(v)

    html_content += """
            </div> <div id="en" class="video-list grid"> """
    # 英語の動画を表示
    for v in videos_en:
        html_content += create_video_card(v)

    html_content += """
            </div> <div id="id" class="video-list grid"> """
    # インドネシア語の動画を表示
    for v in videos_id:
        html_content += create_video_card(v)

    html_content += f"""
            </div> </div>
        <footer>
            <p>© {datetime.now().year} {SITE_NAME} | AI分析ポータル</p>
            <p style="font-size: 0.7rem;">当サイトはファンプロジェクトです。紹介リンクを通じて収益が発生する場合があります。</p>
        </footer>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
