import sys
from pathlib import Path
# 把 qwen_agent 的父目录（即 UserAgent&TravelAgent 的父目录）临时塞进 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from qwen_agent.agents import Assistant
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict
from datetime import datetime

ROOT_RESOURCE = os.path.join(os.path.dirname(__file__), "resource")

class TravelAgent:
    def __init__(self):
        load_dotenv(dotenv_path="/home/JingpengQin/travel_guide/code/UserAgent&TravelAgent/.env")

        self.model_name = os.getenv("MODEL_NAME")
        self.model_api_key = os.getenv("API_KEY")
        self.amap_api_key = os.getenv("AMAP_MAPS_API_KEY")
        self.baidu_map_api_key = os.getenv("BAIDU_MAP_API_KEY")
        self.bot = self.init_agent_service()
        self.conversation_history = []
        self.mcp_calls = []

    def init_agent_service(self):
        llm_cfg = {
            "model": self.model_name,
            "model_server": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": self.model_api_key,
        }
        system = "你扮演一个旅游规划助手，你具有调用各种工具以获取信息的能力"
        tools = [
            {
            "mcpServers": {
                "amap-maps": {
                    "command": "npx",
                    "args": ["-y", "@amap/amap-maps-mcp-server"],
                    "env": {"AMAP_MAPS_API_KEY": self.amap_api_key},
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
                    "env":  {"BAIDU_MAP_API_KEY":  self.baidu_map_api_key}
                }
            }
            }
        ]
        bot = Assistant(
            llm=llm_cfg,
            name="旅游规划助手",
            description="你是一个旅游规划助手，你需要根据用户的需求制定旅行计划。可以调用高德地图mcp(景点、市内交通、酒店餐饮)、my-12306-mcp(火车高铁)、my-flight-mcp(飞机)、百度地图mcp(景点、市内交通、酒店餐饮等)来获取相关信息，要尽可能满足用户需求。",
            system_message=system,
            function_list=tools,
        )
        return bot
    
    def get_user_question_from_user_agent(self, query: Optional[str] = None) -> None:
        assert query is not None, "Query must not be None"
        base_prompt ="""
        根据用户的需求制定旅行计划。可以调用高德地图mcp(景点、市内交通、酒店餐饮)、my-12306-mcp(火车高铁)、my-flight-mcp(飞机)、百度地图mcp(景点、市内交通、酒店餐饮等)来获取相关信息，要尽可能满足用户需求。
        
        示例：
# 白银市7日游旅游攻略

## Day 01 银川-入住酒店
### **08:00** 【早餐】 自助早餐
  > 用餐时间约30分钟
### **10:00** 【自由活动】 推荐：鼓楼、玉皇阁、承天寺塔、览山公园
  > 您可自行前往，无导游司机陪同
### **12:00** 【午餐】 自行解决
### **13:00** 【自由活动】 推荐：鼓楼、玉皇阁、承天寺塔、览山公园
  > 您可自行前往，无导游司机陪同
### **19:10** 【晚餐】 自行解决

## Day 02 银川-66号公路-沙坡头-中卫腾格里沙漠酒店
### **07:30** 【早餐】 自助早餐
  > 用餐时间约30分钟
### **08:00** 【交通】 前往中卫
  > 行程时间约2小时30分钟
### **10:30** 【景点】- **66号公路** (4.5/5)
  ⌚ 活动时间：约1小时
  > 宁夏网红打卡地，感受大漠与乡村风光
### **12:30** 【午餐】 自行解决
### **13:30** 【景点】- **沙坡头** (4.8/5)
  ⌚ 活动时间：约3小时30分钟
  > 包含黄河区+沙漠区，体验滑沙、骑骆驼等项目
### **17:00** 【酒店】 自选酒店
### **18:00** 【晚餐】 自行解决

## Day 03 中卫腾格里沙漠酒店-景泰黄河石林-中卫
### **05:30** 【自由活动】 沙海日出
  > 观赏沙漠日出，拍摄浪漫瞬间
### **08:00** 【早餐】 自助早餐
  > 用餐时间约30分钟
### **08:30** 【交通】 前往景泰黄河石林
  > 行程时间约3小时
### **11:30** 【午餐】 自行解决
### **12:00** 【景点】- **黄河石林国家地质公园** (4.3/5)
  ⌚ 活动时间：约4小时30分钟
  > 感受黄河石林的壮丽地貌
### **16:00** 【交通】 返回中卫
  > 行程时间约3小时
### **19:00** 【酒店】 自选酒店
### **19:00** 【晚餐】 自行解决

## Day 04 中卫-青铜峡黄河大峡谷-西夏陵-银川
### **07:30** 【早餐】 自助早餐
  > 用餐时间约30分钟
### **08:30** 【交通】 前往青铜峡黄河大峡谷
  > 行程时间约1小时40分钟
### **10:00** 【景点】- **青铜峡黄河大峡谷旅游区** (4.8/5)
  ⌚ 活动时间：约3小时
  > 包含景区观光车、青铜峡108塔等
### **13:00** 【午餐】 自行解决
### **13:30** 【交通】 前往西夏陵
  > 行程时间约1小时30分钟
### **15:00** 【景点】- **西夏陵** (4.5/5)
  ⌚ 活动时间：约3小时
  > 参观西夏王朝遗址，了解历史
### **18:30** 【酒店】 自选酒店
### **19:00** 【晚餐】 自行解决

## Day 05 银川-镇北堡西部影视城-贺兰山岩画-览山公园-银川酒店
### **08:00** 【早餐】 自助早餐
  > 用餐时间约30分钟
### **08:30** 【景点】- **镇北堡西部影城** (4.5/5)
  ⌚ 活动时间：约2小时30分钟
  > 感受西部电影场景，参观明城堡、清城堡等
### **12:00** 【午餐】 自行解决
### **13:30** 【景点】- **贺兰山岩画** (4.5/5)
  ⌚ 活动时间：约2小时30分钟
  > 参观古代岩画，了解史前文化
### **16:00** 【景点】- **览山公园** (4.7/5)
  ⌚ 活动时间：约1小时
  > 欣赏古罗马风格建筑和自然景观
### **18:30** 【酒店】 自选酒店
### **19:00** 【晚餐】 自行解决

## Day 06 银川-沙湖-水洞沟-银川
### **07:30** 【早餐】 自助早餐
  > 用餐时间约30分钟
### **08:30** 【景点】- **沙湖生态旅游区** (4.5/5)
  ⌚ 活动时间：约3小时
  > 欣赏湖泊与沙漠交织的自然风光
### **12:30** 【午餐】 自行解决
### **15:00** 【景点】- **宁夏水洞沟旅游区** (4.5/5)
  ⌚ 活动时间：约3小时30分钟
  > 探索史前考古遗址，体验藏兵洞、游船等
### **19:00** 【酒店】 自选酒店
### **19:30** 【晚餐】 自行解决

## Day 07 银川-返程
### **08:00** 【早餐】 自助早餐
  > 用餐时间约30分钟
### **12:00** 【午餐】 自行解决
### **18:00** 【交通】 送机或送站
  > 行程时间约35分钟
        如果你认为用户目前提供的信息不足以制定旅行计划（缺少如几日游），可以询问用户更多信息，提问方式自定。
        如果你认为用户提供的信息已经足以生成攻略，那么按照上面的示例生成一篇旅游攻略，回答的时候必须包含上文所有的约束条件，即你回答的内容需要考虑到上文用户的提问的所有约束条件。
        如果需要查询更多景点的信息，你需要使用百度的mcp工具来查询，获得景点的位置、评分、特色等信息，在规划路径的时候需要考虑到景点之间的距离和交通方式。
        如果需要查询交通信息，你需要使用高德地图的mcp工具来查询，获得交通方式、时间、费用等信息。
        你需要回答的问题如下：
        """
        full_prompt = base_prompt + query if query else base_prompt
        self.conversation_history.append({"role": "user",
                                          "content": full_prompt                                                                               
                                           })

    def get_response(self) -> Dict[str, str]:
        messages = self.conversation_history
        for response in self.bot.run(messages):
            #print(f"Bot response: {response}")
            continue
        data = response

        with open("/home/JingpengQin/travel_guide/code/UserAgent&TravelAgent/full_TravelAgent_log.txt", "a", encoding="utf-8") as f:
            f.write(f"Bot response: {data}\n\n")
            f.write("-"*200 + "\n\n")

# 3. 一次遍历，配对 function_call 与 function 返回
        for i, item in enumerate(data):
            if item.get("function_call"):
                call = item["function_call"]
        # 找下一条 role == 'function' 的返回
                for j in range(i + 1, len(data)):
                    if data[j]["role"] == "function":
                        ret = data[j]
                        self.mcp_calls.append(
                    {
                        "call_no": len(self.mcp_calls) + 1,
                        "tool": call["name"],
                        "arguments": call["arguments"],
                        "return": ret["content"],
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                    }
                )
                        break  # 只取紧随的那一条

        if response and isinstance(response, list):
        # 如果 response 是 list，取最后一个
            response = response[-1]
        if isinstance(response, dict):
            self.conversation_history.append(response)
        return response
    
