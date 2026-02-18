# wind

## ✨ 项目介绍

本项目是一个基于 [NoneBot2](https://github.com/nonebot/nonebot2) 框架的聊天机器人，初衷是自娱自乐。本项目符合 [OneBot](https://github.com/howmanybots/onebot) 标准，可利用 [Napcat](https://github.com/NapNeko/NapCatQQ) bot协议端部署到QQ平台。

## 🛠️ 部署方法

1. 创建虚拟环境并安装依赖

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/MacOS
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. 编辑 `.env.prod.example` 文件，将其重命名为 `.env.prod`，并根据需要修改其中的配置项。(如 `SUPERUSERS`、`LLM_API_KEY` 等)

3. 通过 `nb run` 或 启动入口文件 `bot.py` 来启动机器人
> 如果使用 `nb run`，请确保已安装 NoneBot2 的cli工具，详情见[NoneBot2快速上手文档](https://nonebot.dev/docs/quick-start)
```bash
source .venv/bin/activate  # Linux/MacOS
.venv\Scripts\activate  # Windows
python bot.py
```

## 🐱 与Napcat对接

文档等待完善中...

## 💬 功能介绍

文档等待完善中...