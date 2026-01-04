import os
import requests
import google.generativeai as genai

# 金庫から鍵を取り出す設定
HOLODEX_API_KEY = os.getenv("HOLODEX_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    # 1. Holodexから最新動画を取得
    url = "https://holodex.net/api/v2/videos"
    params = {"org": "Hololive", "limit": 5, "sort": "published_at", "order": "desc", "type": "placeholder,stream"}
    headers = {"X-APIKEY": HOLODEX_API_KEY}
    
    print("🚀 データを取得中...")
    response = requests.get(url, params=params, headers=headers)
    videos = response.json()

    # Geminiの設定
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    print("🤖 AI判定を開始します...\n")
    for v in videos:
        title = v['title']
        prompt = f"以下の動画タイトルを[Original Song, Cover Song, Singing Stream, Other]から1つ選んで出力して。解説は不要。\nタイトル: {title}"
        result = model.generate_content(prompt)
        print(f"タイトル: {title}")
        print(f"AI判定  : {result.text.strip()}")
        print("-" * 20)

if __name__ == "__main__":
    main()
