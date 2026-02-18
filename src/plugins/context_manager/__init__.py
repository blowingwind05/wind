from nonebot import on_message, get_plugin_config, get_driver, logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from datetime import datetime
import json
import os
from .config import Config

# 加载插件配置
plugin_config = get_plugin_config(Config)

# 全局配置
driver = get_driver()
config = driver.config

# 数据目录
data_dir = "data/context_manager"
config_file = os.path.join(data_dir, "context_config.json")

# 全局数据结构：按群号保存最近消息
# 结构: {group_id: [msg1, msg2, ...]}
recent_messages = {}

# 上下文窗口长度配置
default_context_length = plugin_config.default_context_length
# 群特定长度: {group_id: length}
group_context_lengths = {}

# Superuser列表
superusers = config.superusers if hasattr(config, 'superusers') else []

def load_context_config():
    """加载上下文配置"""
    global default_context_length, group_context_lengths
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_context_length = data.get("default_context_length", plugin_config.default_context_length)
                group_context_lengths = data.get("group_context_lengths", {})
            logger.info(f"加载上下文配置: 全局默认 {default_context_length}, 群配置 {len(group_context_lengths)} 个")
        except Exception as e:
            logger.error(f"加载上下文配置失败: {e}")

def save_context_config():
    """保存上下文配置"""
    os.makedirs(data_dir, exist_ok=True)
    data = {
        "default_context_length": default_context_length,
        "group_context_lengths": group_context_lengths
    }
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("上下文配置已保存")
    except Exception as e:
        logger.error(f"保存上下文配置失败: {e}")

# 启动时加载配置
load_context_config()

# 监听所有群消息用于保存历史，不阻塞，优先级设为最小（1）
history_tracker = on_message(priority=1, block=False)

@history_tracker.handle()
async def _(event: GroupMessageEvent):
    text = event.message.extract_plain_text().strip()
    if not text:
        return

    group_id = event.group_id
    add_message(group_id, event.user_id, event.sender.nickname or "未知用户", text)

def add_message(group_id, user_id, nickname, text):
    """保存一条消息"""
    if group_id not in recent_messages:
        recent_messages[group_id] = []

    context_length = group_context_lengths.get(group_id, default_context_length)

    msg = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now(),
        "user_id": user_id,
        "nickname": nickname,
        "message": text
    }
    
    recent_messages[group_id].append(msg)
    while len(recent_messages[group_id]) > context_length:
        recent_messages[group_id].pop(0)

# 提供给外部插件调用的接口
def get_group_history(group_id: int):
    """获取指定群的历史记录"""
    return recent_messages.get(group_id, [])

def add_bot_message(group_id: int, bot_id: int, nickname: str, text: str):
    """保存机器人的回复"""
    add_message(group_id, bot_id, nickname, text)
    logger.info(f"群 {group_id} 记录机器人回复: {text}")

# 历史查看和管理命令
history_cmd = on_message(priority=10, block=False)

@history_cmd.handle()
async def handle_history_cmd(event: GroupMessageEvent):
    cmd = event.message.extract_plain_text().strip()
    group_id = event.group_id

    if cmd == "查看历史" or cmd == "history":
        group_history = recent_messages.get(group_id, [])
        if not group_history:
            await history_cmd.send("本群暂无历史消息喵~")
            return
        history_text = "\n".join([
            f"{msg['date']} {msg['time'].strftime('%H:%M:%S')} {msg['nickname']}: {msg['message']}"
            for msg in group_history[-10:]
        ])
        await history_cmd.send(f"本群最近消息：\n{history_text}")
    
    elif cmd.startswith("设置全局上下文长度"):
        if str(event.user_id) not in superusers:
            await history_cmd.send("只有超级用户才能更改全局上下文长度喵~")
            return
        try:
            new_length = int(cmd.split()[-1])
            if new_length < 1 or new_length > 100:
                await history_cmd.send("上下文长度必须在1-100之间喵~")
                return
            global default_context_length
            default_context_length = new_length
            save_context_config()
            await history_cmd.send(f"全局上下文长度已设置为 {new_length} 喵~")
        except ValueError:
            await history_cmd.send("请输入有效的数字喵~")
            
    elif cmd.startswith("设置群上下文长度"):
        if event.sender.role not in ["admin", "owner"] and str(event.user_id) not in superusers:
            await history_cmd.send("只有群管理员才能更改本群上下文长度喵~")
            return
        try:
            new_length = int(cmd.split()[-1])
            if new_length < 1 or new_length > 100:
                await history_cmd.send("上下文长度必须在1-100之间喵~")
                return
            group_context_lengths[group_id] = new_length
            save_context_config()
            await history_cmd.send(f"本群上下文长度已设置为 {new_length} 喵~")
        except ValueError:
            await history_cmd.send("请输入有效的数字喵~")
            
    elif cmd == "查看上下文长度":
        global_length = default_context_length
        group_length = group_context_lengths.get(group_id, global_length)
        await history_cmd.send(f"全局默认长度: {global_length}\n本群长度: {group_length} 喵~")
