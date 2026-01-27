import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

def download_bus_schedule():
    url = "https://lib.ustc.edu.cn/weixin/%E6%A0%A1%E5%9B%AD%E7%8F%AD%E8%BD%A6%E6%97%B6%E5%88%BB%E8%A1%A8"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"Fetching page: {url}")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch page: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 查找所有居中显示的图片，通常这类重要图片会有 aligncenter 类
    # 或者我们可以根据 alt 属性或者文件名包含 "校车" 来判断
    # 这里根据刚才的探索结果，使用 class="aligncenter" 比较准确
    images = soup.find_all('img', class_='aligncenter')

    if not images:
        print("No images with class 'aligncenter' found. Trying to find images with '校车' in src...")
        images = [img for img in soup.find_all('img') if '校车' in img.get('src', '')]

    print(f"Found {len(images)} potential schedule images.")

    for i, img in enumerate(images):
        # 尝试从 srcset 获取最高分辨率图片
        best_url = None
        srcset = img.get('srcset')
        
        if srcset:
            # srcset 格式形如: "url1 300w, url2 1024w, url3 2048w"
            # 我们分割并找到宽度最大的
            variants = srcset.split(',')
            max_width = 0
            
            for variant in variants:
                parts = variant.strip().split()
                if len(parts) >= 2 and parts[1].endswith('w'):
                    try:
                        width = int(parts[1][:-1])
                        if width > max_width:
                            max_width = width
                            best_url = parts[0]
                    except ValueError:
                        continue
            
            if best_url:
                print(f"Selected high-res image from srcset (width: {max_width}w)")
        
        # 如果没有 srcset 或者解析失败，回退到 src
        if not best_url:
            best_url = img.get('src')
            if not best_url:
                continue
            print("Selected image from src")

        # 确保是绝对链接
        full_url = urljoin(url, best_url)
        
        # 提取文件名
        filename = full_url.split('/')[-1]
        # 如果文件名太长或奇怪，可以用 generic name
        if not filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            filename = f"schedule_{i+1}.jpg"
            
        print(f"Downloading {filename} from {full_url}...")
        
        try:
            img_data = requests.get(full_url, headers=headers).content
            with open(filename, 'wb') as f:
                f.write(img_data)
            print(f"Saved to {filename}")
        except Exception as e:
            print(f"Failed to download image {full_url}: {e}")

if __name__ == "__main__":
    download_bus_schedule()
