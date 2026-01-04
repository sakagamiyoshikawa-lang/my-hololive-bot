import os
import requests
from google import genai
from datetime import datetime
import urllib.parse
import time

# ==========================================
# 🌟 応援・支援用設定
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロライブ応援ナビ"
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def fetch_data(endpoint, org):
    url = f"https://holodex.net/api/v2/{endpoint}"
    params = {"org": org, "limit": 40}
    if endpoint == "videos":
        params.update({"sort": "published_at", "order": "desc", "type": "clip,stream"})
    
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    try:
        res = requests.get(url, params=params, headers=headers, timeout=20)
        return res.json() if res.status_code == 200 else []
    except:
        return []

def main():
    list_holo = fetch_data("live", "Hololive") + fetch_data("videos", "Hololive")
    time.sleep(1)
    list_stars = fetch_data("live", "Holostars") + fetch_data("videos", "Holostars")
    
    client = genai.Client(api_key=GEMINI_API_KEY)

    def create_card(v, org_tag):
        if not v or not isinstance(v, dict) or not v.get('id'): return ""
        v_id, title = v.get('id'), v.get('title', 'No Title')
        ch = v.get('channel', {})
        raw_ch_name = ch.get('name', 'Unknown')
        
        # --- AIによる高度な分析 (多言語対応) ---
        clean_name = raw_ch_name 
        highlight, msg = "見どころ満載の配信！", "みんなで視聴して応援しよう！"
        
        try:
            # ENメンバー等も含め、名前をきれいに抜き出すための指示を強化
            prompt = f"""
            以下のチャンネル名から『個人名』のみを抽出してください。
            （英語表記のメンバーは英語のまま、日本語のメンバーは日本語で抽出）
            また、配信タイトルが英語であっても、日本のファンが喜ぶ『応援見出し』と『応援文』を日本語で作ってください。
            
            チャンネル名: {raw_ch_name}
            タイトル: {title}
            
            出力形式(区切り文字|を使用): 名前|見出し(12字以内)|応援文(20字以内)
            """
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                if len(parts) >= 3:
                    clean_name = parts[0].strip()
                    highlight = parts[1].strip()
                    msg = parts[2].strip()
        except: pass

        search_query = urllib.parse.quote(f"{clean_name}")
        
        return f"""
        <div class="card">
            <div class="thumb-box">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" loading="lazy">
                <div class="org-tag">{org_tag}</div>
            </div>
            <div class="info">
                <div class="ch-name">👤 {raw_ch_name}</div>
                <div class="highlight">✨ {highlight}</div>
                <div class="v-title">{title}</div>
                <div class="ai-msg">💬 {msg}</div>
                <div class="actions">
                    <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn-main">今すぐ応援（視聴）</a>
                    <div class="support-text">＼ {clean_name}さんの活動を支援 ／</div>
                    <div class="merch-links">
                        <a href="https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}" target="_blank" class="btn-sub amz">Amazonで支援</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F" target="_blank" class="btn-sub rak">楽天で支援</a>
                    </div>
                </div>
            </div>
        </div>
        """

    def build_content(v_list, tag):
        seen, html = set(), ""
        for v in v_list:
            if v.get('id') not in seen:
                html += create_card(v, tag)
                seen.add(v.get('id'))
        return html if html else "<p class='error-msg'>データ更新中です。しばらくお待ちください。</p>"

    content_holo = build_content(list_holo, "Hololive")
    content_stars = build_content(list_stars, "Holostars")

    # (HTML/CSS部分は以前と同じため省略... 必要であれば再度提示します)
    # ... 以下、以前のコードのHTML出力部分をそのまま使用 ...
