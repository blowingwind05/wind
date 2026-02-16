from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import tempfile
import anyio

bus = on_command('校车', aliases={'bus', 'school bus', 'xiaoche'}, block=True, priority=5)

def download_bus_images():
    url = "https://lib.ustc.edu.cn/weixin/%E6%A0%A1%E5%9B%AD%E7%8F%AD%E8%BD%A6%E6%97%B6%E5%88%BB%E8%A1%A8"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException:
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    images = soup.find_all('img', class_='aligncenter')
    
    if not images:
        images = [img for img in soup.find_all('img') if '校车' in img.get('src', '')]
    
    downloaded_files = []
    for i, img in enumerate(images[:2]):  # 只下载前两张
        best_url = None
        srcset = img.get('srcset')
        if srcset:
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
        if not best_url:
            best_url = img.get('src')
        if not best_url:
            continue
        full_url = urljoin(url, best_url)
        filename = f"bus_{i+1}.jpg"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        try:
            img_data = requests.get(full_url, headers=headers).content
            with open(filepath, 'wb') as f:
                f.write(img_data)
            downloaded_files.append(filepath)
        except Exception:
            continue
    return downloaded_files

@bus.handle()
async def _handle():
    await bus.send('获取校车时刻表中...', at_sender=True)
    files = await anyio.to_thread.run_sync(download_bus_images)
    if files:
        for file in files:
            await bus.send(MessageSegment.image(file=f'file://{file}'), at_sender=True)
    else:
        await bus.send('获取图片失败，请稍后重试。', at_sender=True)



