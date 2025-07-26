import requests
import zipfile
import os

url = "https://www.minecraft.net/bedrockdedicatedserver/bin-win/bedrock-server-1.21.95.1.zip"
filename = "server.zip"

if not os.path.exists(filename):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/114.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers, stream=True)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print("HTTPエラー:", e)
        print("ステータスコード:", response.status_code)
        print("レスポンス本文:", response.text)
        exit()

    # ダウンロード処理
    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"ファイルを保存しました: {filename}")

path = "server"
os.makedirs(path, exist_ok=True)

with zipfile.ZipFile(filename, 'r') as zip_ref:
    zip_ref.extractall(path)

os.remove(filename)
