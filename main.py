import os
import requests
from google import genai # 書き方を最新版に変更

HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    # 1. Holodexからデータ取得
    url = "https://holodex.net/api/v2/videos"
    params = {"org": "Hololive", "limit": 5, "sort": "published_at", "order": "desc", "type": "placeholder,stream"}
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    print("🚀 データを取得中...")
    response = requests.get(url, params=params, headers=headers)
    videos = response.json()

    # 2. 最新のGemini設定
    client = genai.Client(api_key=GEMINI_API_KEY)

    print("🤖 最新版AI判定を開始します...\n")
    for v in videos:
        title = v['title']
        prompt = f"以下の動画タイトルを[Original Song, Cover Song, Singing Stream, Other]から1つ選んで出力して。解説は不要。\nタイトル: {title}"
        
        # 最新の呼び出し方式に変更
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        print(f"タイトル: {title}")
        print(f"AI判定  : {response.text.strip()}")
        print("-" * 20)

if __name__ == "__main__":
    main()
