import os
import requests
from google import genai

# 環境変数からAPIキーを取得
HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    # 1. Holodexからデータ取得
    url = "https://holodex.net/api/v2/videos"
    params = {
        "org": "Hololive", 
        "limit": 5, 
        "sort": "published_at", 
        "order": "desc", 
        "type": "placeholder,stream"
    }
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    print("🚀 Holodexからデータを取得中...")
    response = requests.get(url, params=params, headers=headers)
    videos = response.json()

    # 2. 最新のGemini設定
    client = genai.Client(api_key=GEMINI_API_KEY)

    print("🤖 AI判定を開始します...\n")
    for v in videos:
        title = v['title']
        prompt = f"以下の動画タイトルを[Original Song, Cover Song, Singing Stream, Other]から1つ選んで出力して。解説は不要。\nタイトル: {title}"
        
        try:
            # モデル名の指定を修正（最新の安定版 ID）
            response = client.models.generate_content(
                model='gemini-1.5-flash', 
                contents=prompt
            )
            
            print(f"タイトル: {title}")
            # .text が空の場合の対策を追加
            category = response.text.strip() if response.text else "判定不能"
            print(f"AI判定  : {category}")
            print("-" * 20)
        except Exception as e:
            print(f"❌ AI判定でエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
