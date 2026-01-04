import os
import requests
from google import genai
from datetime import datetime, timedelta
import urllib.parse
import re
import time

# ==========================================
# 🌟 設定・特選コレクション（ユーザー提供リンク）
# ==========================================
AMAZON_ID = "191383501790a-22"
RAKUTEN_ID = "4fb92fbd.48f820ce.4fb92fbe.82189b12"
SITE_NAME = "ホロ応援ナビ"
SITE_URL = "https://sakagamiyoshikawa-lang.github.io/my-hololive-bot/" 

# ユーザー提供の全商品をリスト化
FEATURED_ITEMS = [
    # 宝鐘マリン ラム酒
    '<table border="0" cellpadding="0" cellspacing="0"><tr><td><div style="border:1px solid #95a5a6;border-radius:.75rem;background-color:#FFFFFF;width:504px;margin:10px;padding:5px;text-align:center;overflow:hidden;"><table><tr><td style="width:240px"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-23%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><img src="https://hbb.afl.rakuten.co.jp/hgb/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?me_id=1375600&item_id=10001628&pc=https%3A%2F%2Fthumbnail.image.rakuten.co.jp%2F%400_mall%2Ff082015-mito%2Fcabinet%2F10011667%2Fdw-23-1.jpg%3F_ex%3D240x240&s=240x240&t=picttext" border="0" style="margin:2px" alt="マリンズラム"></a></td><td style="vertical-align:top;width:248px;display: block;"><p style="font-size:12px;line-height:1.4em;text-align:left;margin:0px;padding:2px 6px;word-wrap:break-word"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-23%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener">【ふるさと納税】マリンズラム ホロライブ 宝鐘マリン</a><br><span>価格：26,000円</span></p><div style="margin:10px;"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-23%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><div style="width:100%;height:27px;background-color:#bf0000;color:#fff;font-size:12px;line-height:27px;border-radius:16px;text-align:center;"> 楽天で購入 </div></a></div></td></tr></table></div></td></tr></table>',
    # さくらみこ 酔うたい焼き
    '<table border="0" cellpadding="0" cellspacing="0"><tr><td><div style="border:1px solid #95a5a6;border-radius:.75rem;background-color:#FFFFFF;width:504px;margin:10px;padding:5px;text-align:center;overflow:hidden;"><table><tr><td style="width:240px"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-19%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><img src="https://hbb.afl.rakuten.co.jp/hgb/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?me_id=1375600&item_id=10001383&pc=https%3A%2F%2Fthumbnail.image.rakuten.co.jp%2F%400_mall%2Ff082015-mito%2Fcabinet%2F10011667%2Fdw-19-1.jpg%3F_ex%3D240x240&s=240x240&t=picttext" border="0" style="margin:2px" alt="酔うたい焼き さくらみこ"></a></td><td style="vertical-align:top;width:248px;display: block;"><p style="font-size:12px;line-height:1.4em;text-align:left;margin:0px;padding:2px 6px;word-wrap:break-word"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-19%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener">【ふるさと納税】酔うたい焼き さくらみこすぺしゃる</a><br><span>価格：12,000円</span></p><div style="margin:10px;"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-19%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><div style="width:100%;height:27px;background-color:#bf0000;color:#fff;font-size:12px;line-height:27px;border-radius:16px;text-align:center;"> 楽天で購入 </div></a></div></td></tr></table></div></td></tr></table>',
    # 白上フブキ 酔う抹茶プディング
    '<table border="0" cellpadding="0" cellspacing="0"><tr><td><div style="border:1px solid #95a5a6;border-radius:.75rem;background-color:#FFFFFF;width:504px;margin:10px;padding:5px;text-align:center;overflow:hidden;"><table><tr><td style="width:240px"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-27%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><img src="https://hbb.afl.rakuten.co.jp/hgb/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?me_id=1375600&item_id=10001766&pc=https%3A%2F%2Fthumbnail.image.rakuten.co.jp%2F%400_mall%2Ff082015-mito%2Fcabinet%2F10011667%2Fdw-27-1.jpg%3F_ex%3D240x240&s=240x240&t=picttext" border="0" style="margin:2px" alt="酔う抹茶プディング"></a></td><td style="vertical-align:top;width:248px;display: block;"><p style="font-size:12px;line-height:1.4em;text-align:left;margin:0px;padding:2px 6px;word-wrap:break-word"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-27%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener">【ふるさと納税】フブキングダム御用達『酔う抹茶プディング』</a><br><span>価格：12,000円</span></p><div style="margin:10px;"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-27%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><div style="width:100%;height:27px;background-color:#bf0000;color:#fff;font-size:12px;line-height:27px;border-radius:16px;text-align:center;"> 楽天で購入 </div></a></div></td></tr></table></div></td></tr></table>',
    # 兎田ぺこら 百年梅酒
    '<table border="0" cellpadding="0" cellspacing="0"><tr><td><div style="border:1px solid #95a5a6;border-radius:.75rem;background-color:#FFFFFF;width:504px;margin:10px;padding:5px;text-align:center;overflow:hidden;"><table><tr><td style="width:240px"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-16%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><img src="https://hbb.afl.rakuten.co.jp/hgb/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?me_id=1375600&item_id=10000851&pc=https%3A%2F%2Fthumbnail.image.rakuten.co.jp%2F%400_mall%2Ff082015-mito%2Fcabinet%2F10011667%2Fdw-16-1.jpg%3F_ex%3D240x240&s=240x240&t=picttext" border="0" style="margin:2px" alt="百年梅酒ぺこらver"></a></td><td style="vertical-align:top;width:248px;display: block;"><p style="font-size:12px;line-height:1.4em;text-align:left;margin:0px;padding:2px 6px;word-wrap:break-word"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-16%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener">【ふるさと納税】百年梅酒ぺこらver（梅酒大会優勝）</a><br><span>価格：13,000円</span></p><div style="margin:10px;"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-16%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><div style="width:100%;height:27px;background-color:#bf0000;color:#fff;font-size:12px;line-height:27px;border-radius:16px;text-align:center;"> 楽天で購入 </div></a></div></td></tr></table></div></td></tr></table>',
    # 白銀ノエル ノエルのポーション
    '<table border="0" cellpadding="0" cellspacing="0"><tr><td><div style="border:1px solid #95a5a6;border-radius:.75rem;background-color:#FFFFFF;width:504px;margin:10px;padding:5px;text-align:center;overflow:hidden;"><table><tr><td style="width:240px"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-18%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><img src="https://hbb.afl.rakuten.co.jp/hgb/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?me_id=1375600&item_id=10000986&pc=https%3A%2F%2Fthumbnail.image.rakuten.co.jp%2F%400_mall%2Ff082015-mito%2Fcabinet%2F10011667%2Fimgrc0121998625.jpg%3F_ex%3D240x240&s=240x240&t=picttext" border="0" style="margin:2px" alt="ノエルのポーション"></a></td><td style="vertical-align:top;width:248px;display: block;"><p style="font-size:12px;line-height:1.4em;text-align:left;margin:0px;padding:2px 6px;word-wrap:break-word"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-18%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener">【ふるさと納税】プレミアムクラフトジン「ノエルのポーション」</a><br><span>価格：27,000円</span></p><div style="margin:10px;"><a href="https://hb.afl.rakuten.co.jp/ichiba/4fbe0f95.f3813a3e.4fbe0f96.1061a182/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ff082015-mito%2Fdw-18%2F&link_type=picttext&ut=eyJwYWdlIjoiaXRlbSIsInR5cGUiOiJwaWN0dGV4dCIsInNpemUiOiIyNDB4MjQwIiwibmFtIjoxLCJuYW1wIjoicmlnaHQiLCJjb20iOjEsImNvbXAiOiJkb3duIiwicHJpY2UiOjEsImJvciI6MSwiY29sIjoxLCJiYnRuIjoxLCJwcm9kIjowLCJhbXAiOmZhbHNlfQ%3D%3D" target="_blank" rel="nofollow sponsored noopener"><div style="width:100%;height:27px;background-color:#bf0000;color:#fff;font-size:12px;line-height:27px;border-radius:16px;text-align:center;"> 楽天で購入 </div></a></div></td></tr></table></div></td></tr></table>'
]

FEATURE_ITEM_SECTION = f"""
<div class="featured-section">
    <h2 class="section-title">✨ 推しの活動を支える特選アイテム</h2>
    <div class="featured-scroll">
        <div class="featured-container">
            {"".join(FEATURED_ITEMS)}
        </div>
    </div>
</div>
"""
# ==========================================

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def super_clean_name(raw_name):
    name = re.sub(r'(?i)ch\.|channel|\s*-\s*.*|hololive|holoX|holoJP|holoEN|holoID', '', raw_name).strip()
    if re.search(r'[ぁ-んァ-ヶー一-龠]', name):
        name = re.sub(r'[a-zA-Z0-9\s!-/:-@[-`{-~]+', '', name).strip()
    return name if name else raw_name

def fetch_pure_holo():
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    combined = []
    for ep in ["live", "videos"]:
        params = {"org": "Hololive", "limit": 40}
        if ep == "videos": params.update({"sort": "view_count", "order": "desc", "type": "stream"})
        try:
            res = requests.get(f"https://holodex.net/api/v2/{ep}", params=params, headers=headers, timeout=20)
            if res.status_code == 200:
                data = res.json()
                combined.extend([v for v in data if isinstance(data, list) and v.get('channel', {}).get('org') == 'Hololive'])
            time.sleep(1)
        except: pass
    return combined

def main():
    list_holo = fetch_pure_holo()
    client = genai.Client(api_key=GEMINI_API_KEY)

    def create_card(v):
        v_id, title = v.get('id'), v.get('title', 'No Title')
        status = v.get('status', 'past')
        raw_start = v.get('start_scheduled') or v.get('start_actual')
        ch = v.get('channel', {})
        raw_ch_name, ch_id = ch.get('name', 'Unknown'), ch.get('id')
        clean_name = super_clean_name(raw_ch_name)
        
        highlight, msg = "必見の配信！", "みんなで応援しましょう！"
        try:
            prompt = f"配信『{title}』の魅力を10文字程度の見出し|15文字の紹介文で書いて。"
            res = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            if res.text:
                parts = res.text.strip().split('|')
                highlight, msg = parts[0].strip(), parts[1].strip() if len(parts) > 1 else msg
        except: pass

        badge = '<div class="badge live">LIVE中</div>' if status == 'live' else ''
        main_btn = f'<a href="https://www.youtube.com/watch?v={v_id}" target="_blank" class="btn watch">📺 視聴・応援に行く</a>'
        
        if status == 'upcoming' and raw_start:
            badge = '<div class="badge upcoming">配信予定</div>'
            try:
                st_dt = datetime.strptime(raw_start.replace('Z', '')[:19], '%Y-%m-%dT%H:%M:%S')
                st, et = st_dt.strftime('%Y%m%dT%H%M%SZ'), (st_dt + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')
                cal_url = f"https://www.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote('【視聴予約】'+title)}&dates={st}/{et}&details={urllib.parse.quote('出演: '+raw_ch_name)}"
                main_btn = f'<a href="{cal_url}" target="_blank" class="btn reserve">📅 予約 (Googleカレンダー)</a>' + main_btn
            except: pass

        share_text = urllib.parse.quote(f"✨{highlight}\n{msg}\n#ホロライブ応援ナビ #{clean_name}")
        search_query = urllib.parse.quote(clean_name)
        
        return f"""
        <div class="card">
            <div class="thumb-box"><img src="https://img.youtube.com/vi/{v_id}/mqdefault.jpg" loading="lazy">{badge}</div>
            <div class="card-body">
                <p class="ch-name">👤 {raw_ch_name}</p>
                <h3 class="highlight-txt">{highlight}</h3>
                <div class="quote-box">{msg}</div>
                <div class="actions">
                    {main_btn}
                    <a href="https://twitter.com/intent/tweet?text={share_text}&url={SITE_URL}" target="_blank" class="btn share">📢 この配信を布教する</a>
                    <div class="support-grid">
                        <a href="https://www.amazon.co.jp/s?k={search_query}&tag={AMAZON_ID}" target="_blank" class="s-link amz">Amazon</a>
                        <a href="https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_ID}/?pc=https%3A%2F%2Fsearch.rakuten.co.jp%2Fsearch%2Fmall%2F{search_query}%2F" target="_blank" class="s-link rak">楽天</a>
                        <a href="https://www.youtube.com/channel/{ch_id}/join" target="_blank" class="s-link join">メン限</a>
                    </div>
                </div>
            </div>
        </div>"""

    seen_ids = set()
    cards_html = "".join([create_card(v) for v in list_holo if v.get('id') not in seen_ids and not seen_ids.add(v.get('id'))])

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{SITE_NAME}</title>
        <link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@700;900&display=swap" rel="stylesheet">
        <style>
            :root {{ --main: #00c2ff; --bg: #f0f4f8; --card: #fff; }}
            body {{ font-family: 'M PLUS Rounded 1c', sans-serif; background: var(--bg); margin: 0; padding-bottom: 50px; }}
            header {{ background: linear-gradient(135deg, #00c2ff, #0078ff); color: #fff; padding: 40px 20px; text-align: center; clip-path: polygon(0 0, 100% 0, 100% 90%, 0 100%); }}
            h1 {{ margin: 0; font-size: 2rem; font-weight: 900; }}
            
            .featured-section {{ max-width: 1400px; margin: 40px auto; padding: 0 20px; }}
            .section-title {{ font-size: 1.2rem; font-weight: 900; color: #4a5568; margin-bottom: 20px; text-align:center; }}
            .featured-scroll {{ overflow-x: auto; padding-bottom: 20px; -webkit-overflow-scrolling: touch; }}
            .featured-container {{ display: flex; gap: 20px; width: max-content; }}
            
            .container {{ max-width: 1400px; margin: 40px auto; padding: 0 20px; display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 30px; }}
            .card {{ background: var(--card); border-radius: 30px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); display: flex; flex-direction: column; }}
            .thumb-box {{ position: relative; aspect-ratio: 16/9; background:#000; }}
            .thumb-box img {{ width: 100%; height: 100%; object-fit: cover; }}
            .badge {{ position: absolute; top: 15px; right: 15px; padding: 6px 12px; border-radius: 10px; font-size: 10px; font-weight: 900; color: #fff; }}
            .badge.live {{ background: #ff0000; }}
            .badge.upcoming {{ background: #ffb800; }}
            .card-body {{ padding: 25px; flex-grow: 1; display: flex; flex-direction: column; }}
            .ch-name {{ font-size: 11px; color: var(--main); font-weight: 900; margin-bottom: 8px; }}
            .highlight-txt {{ font-size: 1.3rem; font-weight: 900; margin-bottom: 12px; line-height: 1.2; }}
            .quote-box {{ background: #f8fafc; padding: 12px; border-radius: 15px; font-size: 13px; border-left: 5px solid var(--main); margin-bottom: 20px; }}
            .btn {{ display: block; text-decoration: none; text-align: center; padding: 12px; border-radius: 15px; font-weight: 900; font-size: 13px; margin-bottom: 8px; }}
            .btn.watch {{ background: var(--main); color: #fff; }}
            .btn.reserve {{ background: #ffb800; color: #fff; }}
            .btn.share {{ background: #000; color: #fff; }}
            .support-grid {{ display: flex; gap: 5px; }}
            .s-link {{ flex: 1; text-decoration: none; font-size: 10px; font-weight: 900; text-align: center; padding: 8px 2px; border-radius: 8px; background: #f1f5f9; color: #475569; border-bottom: 3px solid #ddd; }}
        </style>
    </head>
    <body>
        <header><h1>💙 {SITE_NAME}</h1></header>
        {FEATURE_ITEM_SECTION}
        <div class="container">{cards_html}</div>
        <footer style="text-align: center; padding: 60px; color: #a0aec0; font-size: 12px;">© 2026 {SITE_NAME}</footer>
    </body>
    </html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__": main()
