import os
from datetime import datetime
from openai import OpenAI
from nonebot import logger, get_plugin_config
from .config import Config
import json
from .tools.geocoding import get_location_info, get_location_by_coords

# 加载插件配置
plugin_config = get_plugin_config(Config)

api_key = plugin_config.llm_api_key
base_url = plugin_config.llm_base_url
model_name = plugin_config.llm_model_name

client = OpenAI(api_key=api_key, base_url=base_url)

# 工具定义
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_location_info",
            "description": "获取指定地点的地理信息，包括地址、经纬度和城市",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "要查询的地点名称，支持中文"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_location_by_coords",
            "description": "根据经纬度坐标获取地点信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {
                        "type": "number",
                        "description": "纬度"
                    },
                    "lon": {
                        "type": "number",
                        "description": "经度"
                    }
                },
                "required": ["lat", "lon"]
            }
        }
    }
]

def load_system_prompt():
    """从插件目录或运行目录加载系统提示"""
    # 尝试在当前工作目录寻找，如果找不到则使用默认
    try:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "你是一个可爱的猫娘助手，名叫小喵，喜欢用喵~结尾。在必要的时候可以使用 tool call 来帮助自己。"

def format_history_for_ai(history):
    """将历史记录格式化为上下文文本"""
    if not history:
        return "（暂无历史记录）"
    
    formatted = "这是最近的群聊记录（背景信息）：\n"
    for msg in history:
        date_str = msg.get("date", "")
        time_str = msg["time"].strftime("%H:%M:%S") if isinstance(msg["time"], datetime) else msg["time"]
        if date_str:
            time_display = f"{date_str} {time_str}"
        else:
            time_display = time_str
        formatted += f"[{time_display}] {msg['nickname']}: {msg['message']}\n"
    formatted += "--- 记录结束 ---\n"
    return formatted

async def get_ai_response(current_msg, history, bot_id):
    """调用 API 获取 AI 回复，支持工具调用"""
    system_prompt = load_system_prompt()
    system_prompt += f"\n你的 QQ 号是 {bot_id}。"
    
    history_context = format_history_for_ai(history)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{history_context}\n用户当前说：{current_msg}\n请直接回复用户。"}
    ]
    
    try:
        while True:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=500,
                tools=tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # 检查是否有工具调用
            if message.tool_calls:
                messages.append(message)  # 添加助手的消息
                
                for tool_call in message.tool_calls:
                    logger.info(f"AI 正在使用工具: {tool_call.function.name} (参数: {tool_call.function.arguments[:100]}...)")
                    if tool_call.function.name == "get_location_info":
                        args = json.loads(tool_call.function.arguments)
                        location = args.get("location")
                        result = get_location_info(location)
                        
                        # 添加工具结果
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })
                    elif tool_call.function.name == "get_location_by_coords":
                        args = json.loads(tool_call.function.arguments)
                        lat = args.get("lat")
                        lon = args.get("lon")
                        result = get_location_by_coords(lat, lon)
                        
                        # 添加工具结果
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })
                
                # 继续对话
                continue
            else:
                # 直接回复
                return message.content
    
    except Exception as e:
        logger.error(f"AI 接口调用失败: {e}")
        return f"呜呜，出错了：{e}"
