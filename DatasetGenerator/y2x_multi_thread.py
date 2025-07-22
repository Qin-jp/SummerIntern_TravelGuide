import os
import json
import time
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import requests
from dotenv import load_dotenv
import random
from datetime import datetime
import re

load_dotenv()


API_URL = os.getenv("API_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = os.getenv("API_KEY")

class TravelGuideBatchProcessor:
    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.processed_files = set()  # 用于记录已处理的文件
        self.max_retries = 3  # 最大重试次数
        self.initial_delay = 1  # 初始延迟(秒)
        self.log_file = "/home/JingpengQin/travel_guide/final_data/processing_errors.log"

    def is_already_processed(self, base_name: str, output_dir: str) -> bool:
        """检查文件是否已经完整处理过"""
        target_dir = os.path.join(output_dir, base_name)
        if not os.path.exists(target_dir):
            return False
    
        required_files = [
        (f"{base_name}.md", False),           # 不检查内容是否为空
        (f"{base_name}_constraints.json", True),  # 需要检查内容是否为空
        #(f"{base_name}_question.txt", True)    # 需要检查内容是否为空
    ]
    
        for filename, check_content in required_files:
            filepath = os.path.join(target_dir, filename)
        
        # 检查文件是否存在
            if not os.path.exists(filepath):
                return False
        
        # 如果需要检查内容且文件为空
            if check_content:
                try:
                # 检查文件大小是否为0
                    if os.path.getsize(filepath) == 0:
                        return False
                
                # 对于JSON文件，额外验证内容是否有效
                    if filename.endswith('.json'):
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                            if not content:  # 检查JSON内容是否为空
                                return False
                
                # 对于TXT文件，检查是否有实际内容
                    elif filename.endswith('.txt'):
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if not content:  # 检查TXT内容是否为空
                                return False
                except (json.JSONDecodeError, IOError):
                # 如果文件损坏或读取失败，视为未处理
                    return False
    
    # 所有文件都存在且非空
        return True

    def process_single_guide(self, guide_path: str, output_dir: str):
        """处理单篇攻略并保存结果"""
        parent_dir_name = os.path.basename(os.path.dirname(guide_path))
        
        base_name = os.path.basename(guide_path).replace('.md', '')
        
        # 检查是否已处理
        #if self.is_already_processed(base_name, output_dir):
        if self.is_already_processed(base_name, os.path.join(output_dir, parent_dir_name)):
            print(f"⏩ 跳过已处理文件: {base_name}")
            return True, base_name


        try:
            with open(guide_path, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"开始处理: {base_name}")
            
            # 为每个线程创建独立的处理器实例
            processor = TravelGuideBatchProcessor()
            
            # 提取约束
            constraints = processor.extract_constraints(content)
            
            
            # 生成需求陈述
            # statement = processor.generate_statement_x1_question(constraints)
            # print(f"✅ 生成需求完成: {base_name}")
            
            # 创建输出目录
            output_subdir = os.path.join(output_dir, parent_dir_name, base_name)
            os.makedirs(output_subdir, exist_ok=True)
            
            # 保存结果
            # if not statement:
            #     print(f"❌ 生成需求失败，跳过文件: {base_name}")
            #     time.sleep(float(random.randint(1,15)))  # 控制处理速度，避免过快提交请求
            #     return False, base_name
            if not constraints:
                print(f"❌ 提取约束失败，跳过文件: {base_name}")
                time.sleep(float(random.randint(1,5)))  # 控制处理速度，避免过快提交请求
                return False, base_name

            with open(os.path.join(output_subdir, f"{base_name}_constraints.json"), 'w', encoding='utf-8') as f:
                print(f"✅ 提取约束完成: {base_name}")
                formatted_json = json.dumps(constraints, indent=2, ensure_ascii=False)
                f.write(formatted_json)
                #json.dump(constraints, f, indent=2, ensure_ascii=False)
            
            # with open(os.path.join(output_subdir, f"{base_name}_question.txt"), 'w', encoding='utf-8') as f:
            #     f.write(statement)
            
            shutil.copy(guide_path, os.path.join(output_subdir, f"{base_name}.md"))
            
            print(f"🎉 处理完成: {base_name}")
            return True, base_name
            
        except Exception as e:
            print(f"❌ 处理失败 {base_name}: {str(e)}")
            # 记录失败日志
            error_log = os.path.join(output_dir, "processing_errors.log")
            with open(error_log, 'a', encoding='utf-8') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {base_name} | {str(e)}\n")
            return False, base_name

    def process_directory(self, input_dir: str, output_dir: str, max_workers: int = 5):
        """递归处理目录中的所有Markdown文件（多线程版本）"""
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 收集所有需要处理的Markdown文件
        md_files = []
        for root, _, files in os.walk(input_dir):
            for file in files:
                if file.endswith('.md'):
                    md_files.append(os.path.join(root, file))
        
        print(f"🔍 找到 {len(md_files)} 个Markdown文件待处理")
        
        # 使用线程池处理文件
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for file_path in md_files:
                futures.append(executor.submit(
                    self.process_single_guide,
                    file_path,
                    output_dir
                ))
                #time.sleep(0.01)  # 控制任务提交速度
            
            # 统计结果
            total_files = len(md_files)
            success_count = 0
            skip_count = 0
            
            for future in as_completed(futures):
                try:
                    success, filename = future.result()
                    if success == "skipped":
                        skip_count += 1
                    elif success:
                        success_count += 1
                except Exception as e:
                    print(f"任务执行出错: {str(e)}")
            
        print("\n" + "="*50)
        print(f"处理完成！\n总文件数: {total_files}")
        print(f"成功处理: {success_count}")
        print(f"跳过已处理: {skip_count}")
        print(f"失败数量: {total_files - success_count - skip_count}")
        print("="*50)

    def _log_error(self, error_type: str, error_msg: str, payload: Dict = None):
        """记录错误日志到文件"""
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
            print(f"无法写入日志文件: {str(e)}")

    def send_request(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 8192) -> Dict:
        """发送API请求并保存到历史记录（带重试机制）"""
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"

        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                assert API_URL is not None, "API_URL未配置"
                #response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
                response.raise_for_status()
                
                result = response.json()
                if 'choices' in result:
                    self.conversation_history.extend([
                        messages[-1],
                        {"role": "assistant", "content": result['choices'][0]['message']['content']}
                    ])
                return result

            except requests.exceptions.HTTPError as e:
                last_exception = e
                if e.response.status_code == 429:
                    # 429错误使用指数退避
                    delay = min(self.initial_delay * (2 ** attempt), 30)  # 最大不超过60秒
                    error_msg = f"API限流 (HTTP 429)，等待 {delay}秒后重试 (尝试 {attempt + 1}/{self.max_retries})"
                else:
                    delay = random.uniform(1, 5)
                    error_msg = f"HTTP错误 {e.response.status_code}，等待 {delay:.1f}秒后重试"
                
                self._log_error("HTTPError", error_msg, payload)
                print(error_msg)
                time.sleep(delay)

            except requests.exceptions.RequestException as e:
                last_exception = e
                delay = random.uniform(1, 15)
                error_msg = f"请求异常: {type(e).__name__}，等待 {delay:.1f}秒后重试"
                self._log_error("RequestException", error_msg, payload)
                print(error_msg)
                time.sleep(delay)

            except Exception as e:
                last_exception = e
                self._log_error("UnexpectedError", str(e), payload)
                print(f"意外错误: {str(e)}")
                break  # 非网络错误立即终止

        # 所有重试失败后的处理
        error_msg = f"所有重试失败: {str(last_exception)}" if last_exception else "未知错误"
        self._log_error("FinalFailure", error_msg, payload)
        print(error_msg)
        return {}

    def extract_constraints(self, guide_content: str) -> Dict:
        """提取旅行约束条件"""
        prompt = {
    "role": "user",
    "content": f"""请从以下攻略中提取关键约束信息，返回JSON，不要有任何解释，在开头不要加'''json,结尾不要加上'''：
    {guide_content}
    
    要求：
    1. 包含字段：
    - "departure": "出发地"（如未明确说明则和destination保持一致）
    - "destination": "目标地"（主要旅游目的地，保留最主要的一个目的地即可）
    - "attractions": ["景点列表"]（攻略中提到的景点名称，按照景点出现的顺序进行排列）
    - "time": "几日游"
    - "type": ["旅游类型列表"]（包括自然景观、人文景观、历史文化、美食、购物、娱乐，包含多种旅游类型的时候，消耗时间最长的旅游类型放在最前面）
    - "age_limit": "年龄限制"（只用给出年龄段的限制，不需要给出是哪些项目存在年龄限制，如果存在多个年龄段限制，取可以游玩的人群的年龄段的交集）
    - "intensity": "活动总体强度"（包括低（散步、观光巴士、轻松徒步等轻松活动）、中（包含短途骑行、3-5小时徒步等中程徒步活动）、高（包含长途徒步、登山、马拉松等高强度活动等））
    - "city": "城市"（存在多个城市的时候要包含所有城市）
    
    
    2. 没有的信息留空（如 "age_limit": ""）
    
    3. 示例输出：
        {{
        "departure": "上海",
        "destination": "北京",
        "attractions": ["故宫", "长城", "天安门广场", "颐和园"],
        "city": "北京",
        "time": "3日游",
        "type": ["人文景观", "自然景观"]
        "age_limit": "18岁以上55岁以下",
        "intensity": "中"
        }}
    4. 在开头不要加'''json,结尾不要加上'''
    """
    }
        prompt["content"]  = prompt["content"] + "/no_think"  # 添加思考模式标记
        response = self.send_request([prompt], max_tokens=8192)
        if response and 'choices' in response:
            try:
                result = self.strip_think(response['choices'][0]['message']['content'])
                result = strip_json_fence(result)  # 去除可能的JSON围栏
                result = json.loads(result)
                for key, value in result.items():
                    if isinstance(value, list):  # 检查 value 是否是 list
                        result[key] = list(dict.fromkeys(value))  # 保持顺序去重
                return result if result else {}
                #return json.loads(response['choices'][0]['message']['content'])
            except json.JSONDecodeError:
                # 如果解析失败，打印错误信息
                error_log = os.path.join("/home/JingpengQin/travel_guide/final_data", "processing_errors.log")
                with open(error_log, 'a', encoding='utf-8') as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | 约束解析失败: {response['choices'][0]['message']['content']}\n")
                # 打印错误信息
                print("约束解析失败")
                print(response['choices'][0]['message']['content'])
                print(result)
        return {}

    def strip_think(self, content: str) -> str:
        clean_str = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        return clean_str.strip()

    def generate_statement_x1_question(self, constraints: Dict) -> str:
        """生成第一个陈述式问题"""
        # prompt = {
        #     "role": "user",
        #     "content": f"""基于以下约束生成一个陈述式问题：
        #     {json.dumps(constraints, ensure_ascii=False)}
            
        #     要求：
        #     1. 生成问题的时候用多样化的形式描述，不要总是用"我需要..."开头
        #     2. 包含所有非空约束，描述约束的时候必须使用同义词替换，但是不要改变原意
        #     3. 示例：
        #        "我需要为55岁以上老人在北京安排2天的自然景观低强度活动"
        #        "我需要在北京安排3日游，主要包含人文景观和历史文化景点的游览，还要适合55岁以上老人"
        #        "我想要在上海规划一次为期一天的旅行，这次旅行主要涵盖大自然的美丽景色和丰富的文化历史景点，适合年龄在十二周岁以上的游客参与，并且活动强度适中，没有特别的偏好需要考虑"
        #     4. 不要用问号
        #     5. 用中文回答
        #     """
        # }
    #     prompt = {
    # "role": "user",
    # "content": f"""基于以下旅行约束生成一个陈述式需求描述：
    # {json.dumps(constraints, ensure_ascii=False)}
    
    # 要求：
    # 1. 生成需求描述时采用多样化表达，避免固定句式开头
    # 2. 必须包含所有非空约束，描述时必须使用同义词替换但不改变原意，或者调整语序。
    # 3. 需要特别包含以下信息（如存在）：
    #    - 出发地和目的地（使用"从...出发前往..."、“从...启程去往...”等多样化表达）
    #    - 景点列表（使用"重点游览..."、"主要包含..."等表达，表达时要自然，不要简单罗列）
    #    - 其他原有约束条件
    
    # 4. 示例：
    #    "计划从上海启程前往北京，重点游览故宫和长城，为55岁以上长辈安排2天的自然景观低强度行程"
    #    "打算在北京规划3日游程，主要包含人文景观和历史文化景点的探访，适合55岁以上人士参与"
    #    "希望从广州出发到上海开展一日旅程，主要涵盖外滩和豫园等景点，欣赏都市风光与文化历史，适合12岁以上游客，活动强度适中"
    #    "期待在成都进行为期两天的美食探索之旅，特别包含宽窄巷子和锦里等知名景点，无特殊年龄限制"
    
    # 5. 禁止使用问号
    # 6. 使用自然流畅的中文表达
    # 7. 景点列表表达要自然，不要简单罗列
    # 8. 不要回答除了问题以外的内容
    # """
    #     }
        prompt = {
            "role": "user",
            "content": f"""请根据以下旅行约束条件，模拟一个普通用户在规划旅行时可能会提出的初步需求或问题。可以是简单陈述需求，也可以是直接提问，语气自然，体现随机性：
            {json.dumps(constraints, ensure_ascii=False)}
            要求：
            1. 生成内容可以是陈述句或疑问句，避免固定句式（如“请问”“计划”等模板化开头）。
            2. 回答的时候首先随机选择 1-3 个关键约束（如目的地、景点、天数、人群等），无需覆盖全部条件。
            3. 如果随机选择的约束中包含出发地/目的地，使用多样化表达：
                - 陈述句："想从...去..."、"打算在...玩..."、"需要安排..."
                - 疑问句："...怎么安排？"、"...推荐吗？"、"...合适吗？"
            4. 如果随机选择的约束中涉及景点时自然融入，例如：
                - 陈述句："重点想逛..."、"对...比较感兴趣"   
                - 疑问句："...值得去吗？"、"...时间够吗？"
            5. 示例：
                - 陈述句："想从上海去北京玩3天，主要逛故宫和长城。"   
                - 疑问句："北京3天行程适合老年人吗？"
                - 陈述句："需要安排一个轻松的杭州两日游，带12岁孩子。"
                - 疑问句："去成都吃美食，宽窄巷子推荐吗？"
            6. 保持口语化，避免罗列或僵硬表达。
            注意：仅输出需求或问题本身，不要解释或补充内容。首先随机选择关键约束，然后根据关键约束回答"""
        }
        
        # 不携带历史上下文
        # messages = self.conversation_history[-4:] + [prompt] if self.conversation_history else [prompt]
        messages = [prompt]
        
        response = self.send_request(messages, max_tokens=8192)
        if response and 'choices' in response:
            return response['choices'][0]['message']['content'].strip('"')
        return ""

import re

def strip_json_fence(text: str) -> str:
    """
    去掉最外层可能出现的 ```json  ... ``` 或 ```  ... ``` 包裹。
    仅处理开头、结尾紧邻的 fence，不影响内部内容。
    """
    # 统一去掉首尾空白字符
    text = text.strip()

    # 匹配 ``` 开头，可选 json 关键字，直到换行；或单独一行 ```
    start_pat = re.compile(r'^\s*```(?:json)?\s*\n?', re.IGNORECASE)

    # 匹配结尾处的单独一行 ```
    end_pat = re.compile(r'\n?\s*```\s*$')

    # 先去掉开头 fence
    text = start_pat.sub('', text)
    # 再去掉结尾 fence
    text = end_pat.sub('', text)

    # 再次清理首尾空白
    return text.strip()

if __name__ == "__main__":
    processor = TravelGuideBatchProcessor()
    
    INPUT_DIR = "/home/JingpengQin/travel_guide/process_data/输出结果/旅游攻略Markdown"
    OUTPUT_DIR = "/home/JingpengQin/travel_guide/final_data/处理结果"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 开始处理，使用5个线程
    processor.process_directory(INPUT_DIR, OUTPUT_DIR, max_workers=20)