# Copyright 2023 The Qwen team, Alibaba Group. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A sqlite database assistant implemented by assistant"""

import asyncio
import json
import os
from typing import Optional
import sys
from pathlib import Path
# 把 qwen_agent 的父目录（即 UserAgent&TravelAgent 的父目录）临时塞进 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI

ROOT_RESOURCE = os.path.join(os.path.dirname(__file__), "resource")


def init_agent_service():
    llm_cfg = {
        "model": "qwen3-32b",
        "model_server": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": "sk-64a82ccb98a940adba327b16c0e75631",
    }
    system = "你扮演一个旅游规划助手，你具有调用各种工具以获取信息的能力"
    tools = [
        {
            "mcpServers": {
                "amap-maps": {
                    "command": "npx",
                    "args": ["-y", "@amap/amap-maps-mcp-server"],
                    "env": {"AMAP_MAPS_API_KEY": "0d3895f85a136933e4383ad4e8025546"},
                },
                "my-12306-mcp": {
                    "command": "/home/DanSu/anaconda3/envs/dol/bin/python",
                    "args": ["/home/DanSu/Travel/12306-mcp/my_12306_mcp.py"],
                },
                "my-flight-mcp": {
                    "command": "/home/DanSu/anaconda3/envs/dol/bin/python",
                    "args": ["/home/DanSu/Travel/flight-mcp/my_flight_mcp.py"],
                },
                 "baidu-map": {
                    "command": "npx",
                    "args": [ "-y",   "@baidumap/mcp-server-baidu-map"],
                    "env":  {"BAIDU_MAP_API_KEY": "KltqWh3dLf9GAepmG9N533LmJ53l9ngC" }
                }
        }
        }
    ]
    bot = Assistant(
        llm=llm_cfg,
        name="旅游规划助手",
        description="你是一个旅游规划助手，你需要根据用户的需求制定旅行计划。可以调用高德地图mcp(景点、市内交通、酒店餐饮)、my-12306-mcp(火车高铁)、my-flight-mcp(飞机)来获取相关信息，要尽可能满足用户需求。",
        system_message=system,
        function_list=tools,
    )

    return bot


def test(
    query="我住在北京，打算明天去绵阳玩两天，后天晚上返回，帮我制定旅游计划。需要来回的交通信息、景点信息、游览顺序、餐饮推荐等。你可以调用工具查询信息，形成一个完整的旅游计划，格式公正整洁，便于用户查看",
    # query='我明天早上从北京去南京，帮我查一下合适的飞机票。',
    # file: Optional[str] = os.path.join(ROOT_RESOURCE, 'poem.pdf')
):
    # Define the agent
    bot = init_agent_service()

    # Chat
    messages = []
    query = "用百度地图查询一下海淀区的景点，然后给我推荐几个评分最高的景点"
    # if not file:
    messages.append({"role": "user", "content": query})
    # else:
    # messages.append({'role': 'user', 'content': [{'text': query}, {'file': file}]})

    # with open("my_log.json", "w") as f:
    #     for response in bot.run(messages):
    #         json.dump(response, f, ensure_ascii=False)
    for response in bot.run(messages):
        continue
    print(response)
    print(response[-1]["content"])


def app_tui():
    # Define the agent
    bot = init_agent_service()

    # Chat
    messages = []
    while True:
        # Query example: 数据库里有几张表
        query = input("user question: ")
        # File example: resource/poem.pdf
        file = input("file url (press enter if no file): ").strip()
        if not query:
            print("user question cannot be empty！")
            continue
        if not file:
            messages.append({"role": "user", "content": query})
        else:
            messages.append(
                {"role": "user", "content": [{"text": query}, {"file": file}]}
            )

        response = []
        for response in bot.run(messages):
            print("bot response:", response)
        messages.extend(response)


def app_gui():
    # Define the agent
    bot = init_agent_service()
    chatbot_config = {
        "prompt.suggestions": [
            "数据库里有几张表",
            "创建一个学生表包括学生的姓名、年龄",
            "增加一个学生名字叫韩梅梅，今年6岁",
        ]
    }
    WebUI(
        bot,
        chatbot_config=chatbot_config,
    ).run()


if __name__ == "__main__":
    test()
    # app_tui()
    # app_gui()
