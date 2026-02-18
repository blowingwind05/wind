import requests
import time
from typing import Dict, Optional
from nonebot import logger

class SimpleGeoCoder:
    """简化的地理编码工具"""
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.user_agent = "WeatherBot/1.0"
        self.last_request_time = 0
    
    def query_location(self, query: str) -> Optional[Dict]:
        """查询地点信息"""
        current_time = time.time()
        if current_time - self.last_request_time < 1.0:
            time.sleep(1.0 - (current_time - self.last_request_time))
        
        params = {
            "q": query,
            "format": "json",
            "addressdetails": 1,
            "limit": 1,
            "accept-language": "zh"
        }
        headers = {"User-Agent": self.user_agent}
        proxies = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
        
        try:
            response = requests.get(self.base_url, params=params, headers=headers, proxies=proxies, timeout=10)
            response.raise_for_status()
            self.last_request_time = time.time()
            data = response.json()
            if data:
                result = data[0]
                return {
                    "display_name": result.get("display_name"),
                    "latitude": float(result.get("lat", 0)),
                    "longitude": float(result.get("lon", 0)),
                    "city": result.get("address", {}).get("city") or result.get("address", {}).get("town"),
                    "postcode": result.get("address", {}).get("postcode")
                }
        except Exception as e:
            logger.error(f"地理编码失败: {e}")
        return None

    def reverse_query_location(self, lat: float, lon: float) -> Optional[Dict]:
        """反向地理编码：根据经纬度查询地点信息"""
        current_time = time.time()
        if current_time - self.last_request_time < 1.0:
            time.sleep(1.0 - (current_time - self.last_request_time))
        
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1,
            "accept-language": "zh"
        }
        headers = {"User-Agent": self.user_agent}
        proxies = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
        
        try:
            response = requests.get("https://nominatim.openstreetmap.org/reverse", params=params, headers=headers, proxies=proxies, timeout=10)
            response.raise_for_status()
            self.last_request_time = time.time()
            data = response.json()
            if data:
                return {
                    "display_name": data.get("display_name"),
                    "latitude": float(data.get("lat", 0)),
                    "longitude": float(data.get("lon", 0)),
                    "city": data.get("address", {}).get("city") or data.get("address", {}).get("town"),
                    "postcode": data.get("address", {}).get("postcode")
                }
        except Exception as e:
            logger.error(f"反向地理编码失败: {e}")
        return None

# 全局实例
geo_coder = SimpleGeoCoder()

def get_location_info(location: str) -> str:
    """获取地点信息的工具函数"""
    result = geo_coder.query_location(location)
    if result:
        postcode = result.get("postcode", "未知")
        return f"地点: {result['display_name']}\n经纬度: {result['longitude']}, {result['latitude']}\n城市: {result.get('city', '未知')}\n邮政编码: {postcode}"
    return f"无法找到地点: {location}"

def get_location_by_coords(lat: float, lon: float) -> str:
    """根据经纬度获取地点信息的工具函数"""
    result = geo_coder.reverse_query_location(lat, lon)
    if result:
        postcode = result.get("postcode", "未知")
        return f"地点: {result['display_name']}\n经纬度: {result['longitude']}, {result['latitude']}\n城市: {result.get('city', '未知')}\n邮政编码: {postcode}"
    return f"无法找到坐标 ({lat}, {lon}) 对应的地点"