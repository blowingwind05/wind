import os
from datetime import datetime
from openai import OpenAI
from nonebot import logger, get_plugin_config
from .config import Config

# 加载插件配置
plugin_config = get_plugin_config(Config)

api_key = plugin_config.llm_api_key
base_url = plugin_config.llm_base_url
model_name = plugin_config.llm_model_name

client = OpenAI(api_key=api_key, base_url=base_url)

def load_system_prompt():
    """从插件目录或运行目录加载系统提示"""
    # 尝试在当前工作目录寻找，如果找不到则使用默认
    try:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "你是一个可爱的猫娘助手，名叫小喵，喜欢用喵~结尾。"

def format_history_for_ai(history):
    """将历史记录格式化为上下文文本"""
    if not history:
        return "（暂无历史记录）"
    
    formatted = "这是最近的群聊记录（背景信息）：\n"
    for msg in history:
        time_str = msg["time"].strftime("%H:%M:%S") if isinstance(msg["time"], datetime) else msg["time"]
        formatted += f"[{time_str}] {msg['nickname']}: {msg['message']}\n"
    formatted += "--- 记录结束 ---\n"
    return formatted

async def get_ai_response(current_msg, history, bot_id):
    """调用 API 获取 AI 回复"""
    system_prompt = load_system_prompt()
    # 让 AI 知道自己的身份 ID
    system_prompt += f"\n你的 QQ 号是 {bot_id}。"
    
    history_context = format_history_for_ai(history)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{history_context}\n用户当前说：{current_msg}\n请直接回复用户。"}
    ]
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"AI 接口调用失败: {e}")
        return f"呜呜，出错了：{e}"
