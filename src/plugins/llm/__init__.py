from nonebot import on_message, get_plugin_config, logger, require
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot
from nonebot.rule import to_me
from .ai_service import get_ai_response
from .config import Config

# 确保上下文管理器插件已加载并导入接口
require("context_manager")
from ..context_manager import get_group_history, add_bot_message

# 加载插件配置
plugin_config = get_plugin_config(Config)

# 处理 @ 机器人的逻辑
reply_matcher = on_message(rule=to_me(), priority=10, block=True)

@reply_matcher.handle()
async def handle_reply(bot: Bot, event: GroupMessageEvent):
    try:
        group_id = event.group_id
        cmd = event.message.extract_plain_text().strip()
        logger.info(f"群 {group_id} 收到 @ 消息: '{cmd}'")
        
        # 移除了历史查看和长度设置逻辑，这些现在由 context_manager 处理
        
        if cmd:
            # 获取该群的历史记录
            group_history = get_group_history(group_id)
            
            # 调用 AI 接口，传入机器人 ID
            ai_reply = await get_ai_response(cmd, group_history, bot_id=event.self_id)
            
            # 发送 AI 回复
            await reply_matcher.send(ai_reply)

            # 将机器人说的话记录到历史中 (自动获取群昵称)
            await add_bot_message(
                bot=bot,
                group_id=group_id,
                text=ai_reply
            )
            
    except Exception as e:
        logger.error(f"处理 @ 消息错误: {e}")
