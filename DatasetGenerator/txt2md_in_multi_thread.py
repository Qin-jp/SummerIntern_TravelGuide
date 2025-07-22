from dotenv import load_dotenv
import os
import requests
from typing import List, Dict
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

load_dotenv()

API_URL = os.getenv("API_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = os.getenv("API_KEY")

class AIChatAPI:
    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.processed_records_file = "/home/JingpengQin/travel_guide/process_data/processed_files.txt"
        self.processed_files = set()  # 新增：用于存储已处理文件名的集合
        self.load_processed_records()  # 初始化时加载已处理记录

    def load_processed_records(self):
        """加载已处理文件记录"""
        try:
            if os.path.exists(self.processed_records_file):
                with open(self.processed_records_file, 'r', encoding='utf-8') as f:
                    self.processed_files = {line.strip() for line in f if line.strip()}
            else:
                # 如果文件不存在，创建空文件
                with open(self.processed_records_file, 'w', encoding='utf-8') as f:
                    pass
        except Exception as e:
            print(f"加载已处理记录失败: {str(e)}")
            self.processed_files = set()

    def add_processed_record(self, filename):
        """添加新的已处理记录"""
        try:
            self.processed_files.add(filename)
            with open(self.processed_records_file, 'a', encoding='utf-8') as f:
                f.write(f"{filename}\n")
        except Exception as e:
            print(f"更新处理记录失败: {str(e)}")

    def send_request(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 8192 * 2) -> Dict:
        """发送API请求并保存到历史记录"""
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "enable_thinking": False  # 不启用思考模式
        }

        if API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"
        
        try:
            assert API_URL is not None
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            if 'choices' in result:
                self.conversation_history.extend([
                    messages[-1],  # 用户最后一条消息
                    {"role": "assistant", "content": result['choices'][0]['message']['content']}
                ])
            return result
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {str(e)}")
            with open(os.path.join("/home/JingpengQin/travel_guide/process_data/输出结果/旅游攻略Markdown", "error_log.txt"), 'a') as f:
                f.write(f"datetime: {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
                f.write(f"API请求失败: {str(e)}\n")
            # 控制处理速度，避免过快提交请求
            time.sleep(float(random.randint(1,5)))  # 等待2秒后重试
            return {}

def process_txt_file(txt_file, city_input_path, city_output_path, base_prompt, api_instance: AIChatAPI):
    """处理单个txt文件的函数，用于多线程"""
    if not txt_file.endswith('.txt'):
        return None
    
    # 获取基础文件名（不含扩展名）
    base_filename = os.path.splitext(txt_file)[0]
    
    # 检查是否已经处理过（新增检查）
    if base_filename in api_instance.processed_files:
        print(f"⏩ [记录跳过] 已处理过: {base_filename}")
        return "skipped"

    # 检查是否已存在同名文件（不考虑几日游标记）
    if is_file_processed(city_output_path, base_filename):
        print(f"⏩ 已存在相关文件: {base_filename}*.md")
        return None
    
    try:
        # 构造完整路径
        txt_path = os.path.join(city_input_path, "文本版本")
        txt_path = os.path.join(txt_path, txt_file)
        
        # 读取文本内容
        with open(txt_path, 'r', encoding='utf-8') as f:
            txt_content = f.read()
        
        # 构造完整Prompt
        full_prompt = base_prompt + "\n\n" + txt_content + "/no_think"
        #full_prompt = base_prompt + "\n\n" + txt_content

        # 调用API
        response = api_instance.send_request(
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7,
            max_tokens=8192
        )
        
        # 获取API返回内容
        if 'choices' not in response:
            time.sleep(float(random.randint(1,5)))  # 控制处理速度，避免过快提交请求
            raise ValueError("API响应中缺少choices字段")
        
        md_content = response['choices'][0]['message']['content']
        
        md_content = strip_think(md_content)  # 清理思考模式标记

        # 生成带几日游标记的文件名
        md_filename = get_output_filename(txt_file, md_content)
        md_path = os.path.join(city_output_path, md_filename)
        
        # 保存Markdown文件
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"✅ 转换成功: {txt_file} → {md_filename}")

        api_instance.add_processed_record(base_filename)

        # 礼貌延迟（避免API限流）
        #time.sleep(2)
        
        return True
    except Exception as e:
        print(f"❌ 处理失败 {txt_file}: {str(e)}")
        # 保存错误日志
        with open(os.path.join(city_output_path, "..", "error_log.txt"), 'a') as f:
            f.write(f"{os.path.basename(city_input_path)}/{txt_file} 处理失败: {str(e)}\n")
        return False

def count_days(md_content):
    """计算Markdown内容中包含的'Day'数量"""
    return len(re.findall(r'## Day \d+', md_content))

def get_output_filename(txt_filename, md_content):
    """生成带几日游标记的输出文件名"""
    base_name = os.path.splitext(txt_filename)[0]
    days = count_days(md_content)
    return f"{base_name}_{days}日游.md"

def is_file_processed(output_dir, base_filename):
    """检查是否已存在同名文件（不考虑几日游标记）"""
    for filename in os.listdir(output_dir):
        if filename.startswith(base_filename) and filename.endswith('.md'):
            return True
    return False

def txt_guide_to_md_guide(input_root, output_root, max_workers=3):
    with open("/home/JingpengQin/travel_guide/code/DatasetGenerator/txt2Markdown_Prompt.txt", "r", encoding="utf-8") as f:
        base_prompt = f.read()

    # 遍历所有城市文件夹
    for city_folder in os.listdir(input_root):
        city_input_path = os.path.join(input_root, city_folder)
        city_output_path = os.path.join(output_root, city_folder)
        
        # 跳过非目录文件
        if not os.path.isdir(city_input_path):
            continue
        
        print(f"\n{'='*40}")
        print(f"正在处理城市: {city_folder}")
        
        # 创建城市对应的输出目录
        os.makedirs(city_output_path, exist_ok=True)
        
        # 获取所有需要处理的txt文件
        #txt_files = [f for f in os.listdir(city_input_path) if f.endswith('.txt')]
        #txt_files = [f for f in os.listdir(os.path.join(city_input_path, "文本版本")) if f.endswith('.txt')]
        text_dir = os.path.join(city_input_path, "文本版本")
        txt_files = []

        if not os.path.exists(text_dir):
            print(f"⏩ 跳过: 目录不存在 - {text_dir}")
            continue
        elif not os.path.isdir(text_dir):
            print(f"⏩ 跳过: 不是有效目录 - {text_dir}")
            continue
        else:
            try:
                txt_files = [f for f in os.listdir(text_dir) if f.lower().endswith('.txt')]
                print(f"📂 找到 {len(txt_files)} 个文本文件: {text_dir}")
            except Exception as e:
                print(f"❌ 读取目录失败: {text_dir} - {str(e)}")
                #errolog_file = os.path.join(city_output_path, "..", "error_log.txt")
                errolog_file = "/home/JingpengQin/travel_guide/data/process_data/输出结果/旅游攻略Markdown/error_log.txt"
                with open(errolog_file, 'a') as f:
                    f.write(f"{city_folder} 读取目录失败: {text_dir} - {str(e)}\n")
                continue
                #txt_files = []
                
        api = AIChatAPI()

        # 使用线程池处理文件
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for txt_file in txt_files:
                futures.append(
                    executor.submit(
                        process_txt_file,
                        txt_file,
                        city_input_path,
                        city_output_path,
                        base_prompt,
                        api  # 传递API实例以保持会话历史
                    )
                )
            
            # 等待所有任务完成
            # for future in as_completed(futures):
            #     future.result()  # 这里可以获取返回值或处理异常
            success_count = 0
            skip_count = 0
            fail_count = 0
            
            for future in as_completed(futures):
                result = future.result()
                if result == "skipped":
                    skip_count += 1
                elif result is True:
                    success_count += 1
                else:
                    fail_count += 1

            print(f"\n处理完成！成功: {success_count}, 跳过: {skip_count}, 失败: {fail_count}")

    print("\n所有城市处理完成!")

def strip_think(content: str) -> str:
    clean_str = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    return clean_str.strip()

# 使用示例
if __name__ == "__main__":
    input_directory = "/home/JingpengQin/travel_guide/process_data/输出结果/旅游攻略文本"
    #output_directory = "/home/JingpengQin/travel_guide/process_data/输出结果/旅游攻略Markdown"
    output_directory = "/home/JingpengQin/travel_guide/process_data/输出结果/超长旅游攻略Markdown"
    # 确保输出目录存在
    os.makedirs(output_directory, exist_ok=True)
    print(f"输入目录: {input_directory}")
    print(f"输出目录: {output_directory}")
    # 调用转换函数
    txt_guide_to_md_guide(input_directory, output_directory, max_workers=20)
# txt_guide_to_md_guide("输入目录", "输出目录", max_workers=5)