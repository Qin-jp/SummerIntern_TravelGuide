import os
import json
import time
import random
from typing import List, Dict, Optional
from datetime import datetime
import requests
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv(dotenv_path="/home/JingpengQin/travel_guide/code/UserAgent&TravelAgent/.env")

# Constants
API_URL = os.getenv("API_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = os.getenv("API_KEY")


class ErrorLogger:
    """Handles error logging functionality"""
    
    def __init__(self, log_file: str = "/home/JingpengQin/travel_guide/code/UserAgent&TravelAgent/error_log.txt"):
        self.log_file = log_file
        
    def log_error(self, error_type: str, error_msg: str, payload: Optional[Dict] = None) -> None:
        """Log errors to file with timestamp"""
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error_type": error_type,
            "error_message": error_msg,
            "payload": payload if payload else None
        }
        
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Failed to write to log file: {str(e)}")


class APIClient:
    """Handles API communication with retry mechanism"""
    
    def __init__(self, logger: ErrorLogger = ErrorLogger(), max_retries: int = 3, initial_delay: float = 1):
        self.logger = logger
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        
    def send_request(self, messages: List[Dict], temperature: float = 0.7, 
                    max_tokens: int = 8192) -> Dict:
        """Send API request with retry mechanism"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "enable_thinking": False,  # 禁用思考模式
            "enable_streaming": False,  # 禁用流式输出
        }

        # if API_KEY:
        #     headers["Authorization"] = f"Bearer {API_KEY}"

        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                assert API_URL is not None, "API_URL not configured"
                #print("API URL:", API_URL)  # Debugging line
                #print("Request Payload:", json.dumps(payload, indent=2))  # Debugging line

                response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
                
                response.raise_for_status()
                
                return response.json()

            except requests.exceptions.HTTPError as e:
                last_exception = e
                if e.response.status_code == 429:
                    delay = min(self.initial_delay * (2 ** attempt), 30)
                    error_msg = f"API rate limit (HTTP 429), waiting {delay} seconds (attempt {attempt + 1}/{self.max_retries})"
                else:
                    delay = random.uniform(1, 5)
                    error_msg = f"HTTP error {e.response.status_code}, waiting {delay:.1f} seconds"
                
                self.logger.log_error("HTTPError", error_msg, payload)
                print(error_msg)
                time.sleep(delay)

            except requests.exceptions.RequestException as e:
                last_exception = e
                delay = random.uniform(1, 15)
                error_msg = f"Request exception: {type(e).__name__}, waiting {delay:.1f} seconds"
                self.logger.log_error("RequestException", error_msg, payload)
                print(error_msg)
                time.sleep(delay)

            except Exception as e:
                last_exception = e
                self.logger.log_error("UnexpectedError", str(e), payload)
                print(f"Unexpected error: {str(e)}")
                break

        error_msg = f"All retries failed: {str(last_exception)}" if last_exception else "Unknown error"
        self.logger.log_error("FinalFailure", error_msg, payload)
        print(error_msg)
        return {}


class ConstraintsManager:
    """Manages constraints loading and processing"""
    
    def __init__(self, logger: ErrorLogger = ErrorLogger()):
        self.logger = logger
        self.constraints = {}
        self.x1_constraints = {}
        self.xn_constraints = []
        
    def load_constraints(self, constraints_file: str) -> None:
        """Load constraints from JSON file"""
        try:
            with open(constraints_file, 'r', encoding='utf-8') as f:
                self.constraints = json.load(f)
        except Exception as e:
            print(f"Failed to load constraints file: {str(e)}")
            self.logger.log_error("LoadConstraintsError", str(e), {"constraints_file": constraints_file})
            raise
            
    def split_constraints(self, N: int) -> None:
        """Split constraints into x1 and xn constraints"""
        if not self.constraints:
            raise ValueError("No constraints loaded")
            
        fixed_constraints = {
            'departure': self.constraints['departure'],
            'destination': self.constraints['destination'],
        }
        other_constraints = {k: v for k, v in self.constraints.items() if k not in fixed_constraints}
        
        other_constraints_list = []
        for key, value in other_constraints.items():
            if isinstance(value, list):
                for item in value:
                    other_constraints_list.append({key: item})
            else:
                other_constraints_list.append({key: value})
       
        random.shuffle(other_constraints_list)

        if len(other_constraints_list) < N - 1:
            raise ValueError(f"Not enough constraints to split into {N} parts")

        split_points = sorted(random.sample(range(1, len(other_constraints_list)), N - 1))
        sizes = [split_points[0]] + [
            split_points[i+1] - split_points[i] 
            for i in range(len(split_points)-1)
        ] + [len(other_constraints_list) - split_points[-1]]
     
        divided = []
        start = 0
        for size in sizes:
            divided.append(other_constraints_list[start:start+size])
            start += size

        self.x1_constraints = self._merge_dicts(fixed_constraints, divided[0])
        self.xn_constraints = [self._merge_dicts({}, part) for part in divided[1:]]
        
    @staticmethod
    def _merge_dicts(base_dict: Dict, dict_list: List[Dict]) -> Dict:
        """Merge multiple dictionaries into one"""
        result = base_dict.copy()
        for d in dict_list:
            for key, value in d.items():
                if key in result:
                    if not isinstance(result[key], list):
                        result[key] = [result[key]]
                    result[key].append(value)
                else:
                    result[key] = value
        return result


class UserAgent:
    """Generates questions based on constraints"""
    
    def __init__(self, api_client: APIClient = APIClient(), constraints_manager: ConstraintsManager = ConstraintsManager()):
        self.api_client = api_client
        self.constraints_manager = constraints_manager
        self.conversation_history: List[Dict] = []
        
    def generate_x1_question(self) -> str:
        """Generate the first question with x1 constraints"""
        if not self.constraints_manager.x1_constraints:
            raise ValueError("x1 constraints not initialized")
            
        prompt = {
            "role": "user",
            "content": f"""基于以下约束生成一个陈述式问题：
            {json.dumps(self.constraints_manager.x1_constraints, ensure_ascii=False)}
            
            要求：
            1. 生成问题的时候用多样化和口语化的形式描述，不要总是用"我需要..."开头
            2. 包含所有非空约束，描述约束的时候必须使用同义词替换，但是不要改变原意
            3. 示例：
               "我需要为55岁以上老人在北京安排2天的自然景观低强度活动"
               "我需要在北京安排3日游，主要包含人文景观和历史文化景点的游览，还要适合55岁以上老人"
               "我想要在上海规划一次为期一天的旅行，这次旅行主要涵盖大自然的美丽景色和丰富的文化历史景点，适合年龄在十二周岁以上的游客参与，并且活动强度适中，没有特别的偏好需要考虑"
            4. 不要用问号
            5. 用中文回答
            """
        }
        
        response = self.api_client.send_request([prompt], max_tokens=8192)
        if response and 'choices' in response:
            content = response['choices'][0]['message']['content'].strip('"')
            content = self.strip_think(content)
            self._update_conversation("user", content)
            return content
        return ""
        
    def generate_xn_question(self, n: int) -> str:
        """Generate nth question with xn constraints"""
        if not (1 <= n <= len(self.constraints_manager.xn_constraints)):
            raise ValueError(f"n must be between 1 and {len(self.constraints_manager.xn_constraints)}")
            
        prompt = {
            "role": "user",
            "content": f"""根据上文对话内容以及以下约束生成一个陈述式的追问的问题：
            {json.dumps(self.constraints_manager.xn_constraints[n-1], ensure_ascii=False)}
            
            要求：
            1. 保持与之前问题一致的口语化风格
            2. 包含所有新约束条件，新约束条件应当作为增加的约束条件，之前提问的约束条件仍然有效
            3. 与之前的得到的回答进行比较，根据之前的回答内容进行调整提问的方式
            3. 用中文回答
            """
        }
        
        messages = self.conversation_history[-10:] + [prompt] if self.conversation_history else [prompt]
        response = self.api_client.send_request(messages, max_tokens=8192)
        if response and 'choices' in response:
            content = response['choices'][0]['message']['content'].strip('"')
            content = self.strip_think(content)
            self._update_conversation("user", content)
            return content
        return ""
    
    def strip_think(self, content: str) -> str:
        clean_str = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        return clean_str.strip()    
    
    def get_answer(self, question: str) -> str:
        """Get answer for a question"""
        prompt = {
            "role": "user",
            "content": f"""基于上文，请回答以下问题：
            {question}
            
            要求：
            1. 回答必须包含所有约束条件
            2. 回答必须是中文
            3. 保持专业和友好的语气
            4. 示例输出
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
            """
        }
        
        messages = self.conversation_history[-4:] + [prompt] if self.conversation_history else [prompt]
        response = self.api_client.send_request(messages, max_tokens=8192)
        if response and 'choices' in response:
            content = response['choices'][0]['message']['content'].strip('"')
            self._update_conversation(prompt, content)
            return content
        return ""
        
    def get_answer_from_travel_agent(self,answer: str = None) -> str:
        self._update_conversation("assistant", answer)
        return answer
    
    # def _update_conversation(self, prompt: Dict, response_content: str) -> None:
    #     """Update conversation history"""
    #     self.conversation_history.extend([
    #         prompt,
    #         {"role": "assistant", "content": response_content}
    #     ])

    def _update_conversation(self, role: str, response_content: str) -> None:
        """Update conversation history"""
        assert role in ["user", "assistant"], "Role must be 'user' or 'assistant'"
        assert type(response_content) is str, "Response content must be a string"
        self.conversation_history.extend([
            {"role": role, "content": response_content}
        ])

def save_qa_to_file(qa_pairs: List[Dict], output_file: str) -> None:
    """Save question-answer pairs to a JSON file"""
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved QA pairs to {output_file}")
    except Exception as e:
        print(f"Failed to save QA pairs: {str(e)}")
        raise

def main(N: int = 4):
    # 初始化各个模块
    logger = ErrorLogger("/home/JingpengQin/travel_guide/code/UserAgent/error_log.txt")
    api_client = APIClient(logger)
    constraints_manager = ConstraintsManager(logger)
    
    # 设置输出文件路径
    output_file = "/home/JingpengQin/travel_guide/code/UserAgent/qa_pairs.json"
    qa_pairs = []
    
    try:
        # 加载和分割约束
        constraints_manager.load_constraints(
            "/home/JingpengQin/travel_guide/final_data/处理结果/白银市旅游攻略/攻略_22816725s2_7日游/攻略_22816725s2_7日游_constraints.json"
        )
        constraints_manager.split_constraints(N=N)
        
        # 初始化问题生成器
        question_generator = UserAgent(api_client, constraints_manager)
        
        # 生成X1问题和答案
        x1_question = question_generator.generate_x1_question()
        print(f"X1 Question: {x1_question}")
        x1_answer = question_generator.get_answer(x1_question)
        print(f"Answer: {x1_answer}")
        
        qa_pairs.append({
            "question_type": "x1",
            "question": x1_question,
            "answer": x1_answer,
            "constraints": constraints_manager.x1_constraints
        })

        # 生成Xn问题和答案
        for i in range(1, N):
            xn_question = question_generator.generate_xn_question(i)
            print(f"X{i + 1} Question: {xn_question}")
            xn_answer = question_generator.get_answer(xn_question)
            print(f"Answer: {xn_answer}")
            
            qa_pairs.append({
                "question_type": f"x{i + 1}",
                "question": xn_question,
                "answer": xn_answer,
                "constraints": constraints_manager.xn_constraints[i-1]
            })

        # 保存所有QA对到文件
        save_qa_to_file(qa_pairs, output_file)

    except Exception as e:
        logger.log_error("RuntimeError", str(e))
        print(f"Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    N = 3  # 设置你的N值
    main(N = N)


