from nonebot import on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
from nonebot import logger
from datetime import datetime
from nonebot.rule import to_me
from .ai_service import get_ai_response

# 全局数据结构：按群号保存最近15条消息
# 结构: {group_id: [msg1, msg2, ...]}
recent_messages = {}

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

    msg = {
        "time": datetime.now(),
        "user_id": event.user_id,
        "nickname": event.sender.nickname or "未知用户",
        "message": text
    }
    
    recent_messages[group_id].append(msg)
    if len(recent_messages[group_id]) > 15:
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
                f"{msg['time'].strftime('%H:%M:%S')} {msg['nickname']}: {msg['message']}"
                for msg in group_history[-10:]
            ])
            await reply_matcher.send(f"本群最近消息：\n{history_text}")
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
                
                bot_msg = {
                    "time": datetime.now(),
                    "user_id": event.self_id,  # 机器人的 QQ 号
                    "nickname": "让风吹过",
                    "message": ai_reply
                }
                recent_messages[group_id].append(bot_msg)
                if len(recent_messages[group_id]) > 15:
                    recent_messages[group_id].pop(0)
                
                logger.info(f"群 {group_id} 记录机器人回复: {ai_reply}")
    except Exception as e:
        logger.error(f"处理 @ 消息错误: {e}")
    except Exception as e:
        logger.error(f"处理 @ 消息错误: {e}")
