import os
import requests
from google import genai
from datetime import datetime, timedelta
import urllib.parse
import re
import time

# ==========================================
# 🌟 応援・支援用設定
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロライブ応援ナビ"
SITE_URL = "https://sakagamiyoshikawa-lang.github.io/my-hololive-bot/" 
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def format_cal_time(iso_str):
    """ISO形式の時間をGoogleカレンダー形式(YYYYMMDDTHHMMSSZ)に変換"""
    try:
        dt = datetime.strptime(iso_str.replace('Z', ''), '%Y-%m-%dT%H:%M:%S.%f')
    except:
        try:
            dt = datetime.strptime(iso_str.replace('Z', ''), '%Y-%m-%dT%H:%M:%S')
        except:
            return None
    # Google CalendarはUTCを Z で受ける
    return dt.strftime('%Y%m%dT%H%M%SZ')

def super_clean_name(raw_name):
    name = re.sub(r'(?i)ch\.|channel|\s*-\s*.*|hololive|holoX|holoJP|holoEN|holoID', '', raw_name).strip()
    if re.search(r'[ぁ-んァ-ヶー一-龠]', name):
        name = re.sub(r'[a-zA-Z0-9\s!-/:-@[-`{-~]+', '', name).strip()
    return name if name else raw_name

def fetch_holo_only():
    url_live = "https://holodex.net/api/v2/live"
    url_videos = "https://holodex.net/api/v2/videos"
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    combined_data = []
    for url in [url_live, url_videos]:
        params = {"org": "Hololive", "limit": 40}
        try:
            res = requests.get(url, params=params, headers=headers, timeout=20)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    for v in data:
                        if v.get('channel', {}).get('org') == 'Hololive':
                            combined_data.append(v)
            time.sleep(1)
        except: pass
    return combined_data

def main():
    list_holo = fetch_holo_only()
    client = genai.Client(api_key=GEMINI_API_KEY)

    def create_card(v):
        if not isinstance(v, dict) or not v.get('id'): return ""
        v_id, title = v.get('id'), v.get('title', 'No Title')
        status = v.get('status', 'past')
        start_time_raw = v.get('start_scheduled') or v.get('start_actual')
        ch = v.get('channel', {})
        raw_ch_name, ch_id = ch.get('name', 'Unknown'), ch.get('id')
        
        clean_name = super_clean_name(raw_ch_name)
        
        # AI分析
        highlight, msg = "必見の配信！", "みんなで応援しましょう！"
        try:
            prompt = f"配信『{title}』の魅力をファン目線で要約。形式: 見出し(12字)|紹介文(20字)"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                highlight = parts[0].strip()
                msg = parts[1].strip() if len(parts) > 1 else msg
        except: pass

        # カレンダー予約URLの生成
        cal_link = ""
        if status == 'upcoming' and start_time_raw:
            st = format_cal_time(start_time_raw)
            if st:
                # 終了時間は1時間後と仮定
                et = (datetime.strptime(st, '%Y%m%dT%H%M%SZ') + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')
                cal_title = urllib.parse.quote(f"【応援】{clean_name}：{title}")
                cal_link = f"https://www.google.com/calendar/render?action=TEMPLATE&text={cal_title}&dates={st}/{et}&details=視聴URL: https://www.youtube.com/watch?v={v_id}"

        # ボタンの出し分け
        main_btn = f'<a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="main-btn">応援（視聴）する</a>'
        if cal_link:
            main_btn = f'<a href="{cal_link}" target="_blank" class="main-btn reserve">カレンダーに予約</a>' + main_btn

        share_text = urllib.parse.quote(f"✨{highlight}\n{msg}\n#ホロライブ応援ナビ #{clean_name}")
        share_url = f"https://twitter.com/intent/tweet?text={share_text}&url={SITE_URL}"
        search_query = urllib.parse.quote(clean_name)
        live_badge = '<div class="live-badge">LIVE</div>' if status == 'live' else ''
        
        return f"""
        <div class="card">
            <div class="thumb">
                <img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" loading="lazy">
                {live_badge}
            </div>
            <div class="card-info">
                <div class="liver-name">👤 {raw_ch_name}</div>
                <div class="catchphrase">{highlight}</div>
                <div class="desc">{msg}</div>
                <div class="action-area">
                    {main_btn}
                    <a href="{share_url}" target="_blank" class="share-btn">📢 布教する</a>
                    <div class="support-links">
                        <a href="https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}" target="_blank" class="s-link amz">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F" target="_blank" class="s-link rak">楽天</a>
                        <a href="https://www.youtube.com/channel/{ch_id}/join" target="_blank" class="s-link join">メン限</a>
                    </div>
                </div>
            </div>
        </div>"""

    seen_ids = set()
    cards_html = "".join([create_card(v) for v in list_holo if v.get('id') not in seen_ids and not seen_ids.add(v.get('id'))])

    # (HTML構造は維持... ボタンのCSSのみ追加)
    full_html = f"""<!DOCTYPE html>...（略）...
    <style>
        /* 前回のCSSに以下を追加 */
        .main-btn.reserve {{ background: #ffb800; margin-bottom: 8px; font-size: 14px; }}
        .main-btn.reserve:hover {{ background: #e6a700; }}
    </style>
    ...（略）...
    """
    # 実際にはフルのHTMLを書き出してください
