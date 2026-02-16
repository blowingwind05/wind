from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Event
from nonebot import logger

llm = on_message(rule=to_me(), priority=100, block=True)

@llm.handle()
async def _(event: Event):
    text = event.message.extract_plain_text()
    logger.info(f"LLM received text: '{text}'")
    if text:
        char_count = len(text)
        logger.info(f"Sending response: 复读：{text}\n字数：{char_count}")
        await llm.send(f'复读：{text}\n字数：{char_count}')






