from nonebot import on_message, get_plugin_config
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
from nonebot import logger, get_driver
from datetime import datetime
from nonebot.rule import to_me
from .ai_service import get_ai_response
import json
import os
from .config import Config

# 加载插件配置
plugin_config = get_plugin_config(Config)

# 全局配置
driver = get_driver()
config = driver.config

# 数据目录
data_dir = "data/llm"
config_file = os.path.join(data_dir, "context_config.json")

# 全局数据结构：按群号保存最近消息
# 结构: {group_id: [msg1, msg2, ...]}
recent_messages = {}

# 上下文窗口长度配置
# 全局默认长度（从配置加载）
default_context_length = plugin_config.default_context_length
# 群特定长度: {group_id: length}
group_context_lengths = {}

# Superuser列表（从配置获取或硬编码）
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

# 监听所有群消息用于保存历史，不阻塞，优先级设为最高（1）
llm = on_message(priority=1, block=False)

@llm.handle()
async def _(event: GroupMessageEvent):
    logger.debug(f"llm saving matcher triggered for group {event.group_id}")
    text = event.message.extract_plain_text().strip()
    if not text:
        return

    group_id = event.group_id
    if group_id not in recent_messages:
        recent_messages[group_id] = []

    # 获取该群的上下文长度
    context_length = group_context_lengths.get(group_id, default_context_length)

    msg = {
        "date": datetime.now().strftime("%Y-%m-%d"),  # 添加日期
        "time": datetime.now(),
        "user_id": event.user_id,
        "nickname": event.sender.nickname or "未知用户",
        "message": text
    }
    
    recent_messages[group_id].append(msg)
    while len(recent_messages[group_id]) > context_length:
        recent_messages[group_id].pop(0)

    logger.info(f"群 {group_id} 保存消息: {msg['nickname']}: {msg['message']} (当前群共 {len(recent_messages[group_id])} 条)")

# 处理 @ 机器人的逻辑


reply_matcher = on_message(rule=to_me(), priority=10, block=True)

@reply_matcher.handle()
async def handle_reply(event: GroupMessageEvent):
    try:
        group_id = event.group_id
        cmd = event.message.extract_plain_text().strip()
        logger.info(f"群 {group_id} 收到 @ 消息: '{cmd}'")
        
        if cmd == "查看历史" or cmd == "history":
            group_history = recent_messages.get(group_id, [])
            if not group_history:
                await reply_matcher.send("本群暂无历史消息喵~")
                return
            history_text = "\n".join([
                f"{msg['date']} {msg['time'].strftime('%H:%M:%S')} {msg['nickname']}: {msg['message']}"
                for msg in group_history[-10:]
            ])
            await reply_matcher.send(f"本群最近消息：\n{history_text}")
        elif cmd.startswith("设置全局上下文长度"):
            # Superuser权限检查
            if str(event.user_id) not in superusers:
                await reply_matcher.send("只有超级用户才能更改全局上下文长度喵~")
                return
            try:
                new_length = int(cmd.split()[-1])
                if new_length < 1 or new_length > 100:
                    await reply_matcher.send("上下文长度必须在1-100之间喵~")
                    return
                global default_context_length
                default_context_length = new_length
                save_context_config()  # 保存配置
                await reply_matcher.send(f"全局上下文长度已设置为 {new_length} 喵~")
            except ValueError:
                await reply_matcher.send("请输入有效的数字喵~")
        elif cmd.startswith("设置群上下文长度"):
            # 群管理员权限检查
            if event.sender.role not in ["admin", "owner"]:
                await reply_matcher.send("只有群管理员才能更改本群上下文长度喵~")
                return
            try:
                new_length = int(cmd.split()[-1])
                if new_length < 1 or new_length > 100:
                    await reply_matcher.send("上下文长度必须在1-100之间喵~")
                    return
                group_context_lengths[group_id] = new_length
                save_context_config()  # 保存配置
                await reply_matcher.send(f"本群上下文长度已设置为 {new_length} 喵~")
            except ValueError:
                await reply_matcher.send("请输入有效的数字喵~")
        elif cmd == "查看上下文长度":
            global_length = default_context_length
            group_length = group_context_lengths.get(group_id, global_length)
            await reply_matcher.send(f"全局默认长度: {global_length}\n本群长度: {group_length} 喵~")
        else:
            if cmd:
                # 获取该群的历史记录
                group_history = recent_messages.get(group_id, [])
                
                # 调用 AI 接口，传入机器人 ID
                ai_reply = await get_ai_response(cmd, group_history, bot_id=event.self_id)
                
                # 发送 AI 回复
                await reply_matcher.send(ai_reply)

                # 将机器人说的话也记录到历史中
                if group_id not in recent_messages:
                    recent_messages[group_id] = []
                
                context_length = group_context_lengths.get(group_id, default_context_length)
                
                bot_msg = {
                    "date": datetime.now().strftime("%Y-%m-%d"),  # 添加日期
                    "time": datetime.now(),
                    "user_id": event.self_id,  # 机器人的 QQ 号
                    "nickname": "让风吹过",
                    "message": ai_reply
                }
                recent_messages[group_id].append(bot_msg)
                while len(recent_messages[group_id]) > context_length:
                    recent_messages[group_id].pop(0)
                
                logger.info(f"群 {group_id} 记录机器人回复: {ai_reply}")
    except Exception as e:
        logger.error(f"处理 @ 消息错误: {e}")
