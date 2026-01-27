import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://lib.ustc.edu.cn/weixin/%E6%A0%A1%E5%9B%AD%E7%8F%AD%E8%BD%A6%E6%97%B6%E5%88%BB%E8%A1%A8"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 尝试找到文章正文内容，通常在 article 或者 post 相关的 class 中
    # WordPress 常见的 class 有 .entry-content, .post-content 等
    content_div = soup.find('div', class_='entry-content')
    if not content_div:
        print("Could not find .entry-content, searching all images...")
        images = soup.find_all('img')
    else:
        print("Found .entry-content, searching images within it...")
        images = content_div.find_all('img')

    for img in images:
        src = img.get('src')
        if src:
            full_url = urljoin(url, src)
            print(f"Index: {img} \n URL: {full_url}\n")

except Exception as e:
    print(f"Error: {e}")
