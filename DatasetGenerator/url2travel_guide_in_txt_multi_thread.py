import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import json
from dotenv import load_dotenv
import os
from typing import List, Dict
import time
import shutil
import re
import threading
from queue import Queue
from selenium.common.exceptions import TimeoutException

# def extract_dynamic_itinerary(url, output_file, timeout=15, proxy=None):
#     """
#     增强版动态内容提取函数（带代理支持和异常重试机制）
#     :param url: 目标URL
#     :param output_file: 输出文件路径
#     :param timeout: 超时时间（秒）
#     :param proxy: 代理设置，格式为 "ip:port" 或 "username:password@ip:port"
#     :return: 是否成功
#     """
#     chrome_options = Options()
    
#     # 基础无头模式配置
#     chrome_options.add_argument("--headless=new")  # 使用新版Headless模式
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
    
#     # 反反爬关键配置
#     chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#     chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     chrome_options.add_experimental_option("useAutomationExtension", False)
    
#     # 完整User-Agent设置
#     chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
#     # 其他优化参数
#     chrome_options.add_argument("--start-maximized")
#     chrome_options.add_argument("--window-size=1920,1080")
#     chrome_options.add_argument("--disable-infobars")
#     chrome_options.add_argument("--disable-extensions")
#     chrome_options.add_argument("--disable-notifications")
#     chrome_options.add_argument("--disable-popup-blocking")
    
#     # 隐藏WebDriver特征
#     chrome_options.add_argument("--disable-web-security")
#     chrome_options.add_argument("--allow-running-insecure-content")
    
#     # 代理设置
#     if proxy:
#         if "@" in proxy:  # 有认证的代理 user:pass@ip:port
#             auth, host_port = proxy.split("@")
#             proxy = f"{host_port}"  # Chrome代理插件只需要host:port
#             chrome_options.add_extension(_create_proxy_auth_extension(auth))
#         else:  # 无认证代理 ip:port
#             host_port = proxy
            
#         # 设置代理
#         chrome_options.add_argument(f'--proxy-server={host_port}')
#         print(f"使用代理: {proxy}")
    
#     driver = None
#     try:
#         driver = webdriver.Chrome(options=chrome_options)
        
#         # 设置页面加载超时
#         driver.set_page_load_timeout(timeout)
        
#         # 访问目标URL
#         driver.get(url)
        
#         # 智能等待（先等页面基本加载完成）
#         WebDriverWait(driver, timeout).until(
#             lambda d: d.execute_script("return document.readyState") == "complete"
#         )
        
#         # 显式等待目标div（最长等待timeout秒）
#         itinerary_div = WebDriverWait(driver, timeout).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "div.daily_itinerary_con"))
#         )
        
#         content = itinerary_div.get_attribute('outerHTML')
        
#         # 确保目录存在
#         os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
#         with open(output_file, 'w', encoding='utf-8') as f:
#             f.write(content)
        
#         print(f"✅ 成功保存: {output_file}")
#         return True
        
#     except TimeoutException:
#         print(f"❌ 页面加载超时 {url} (超时时间: {timeout}秒)")
#         return False
#     except Exception as e:
#         print(f"❌ 提取失败 {url}: {str(e)}")
#         return False
#     finally:
#         if driver:
#             driver.quit()


def extract_dynamic_itinerary(url, output_file, timeout=15, proxy=None):
    """
    增强版动态内容提取函数（带异常重试机制）
    :param url: 目标URL
    :param output_file: 输出文件路径
    :param timeout: 超时时间（秒）
    :return: 是否成功
    """
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    chrome_options = Options()
    
    # 基础无头模式配置
    chrome_options.add_argument("--headless=new")  # 使用新版Headless模式
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 反反爬关键配置
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # 完整User-Agent设置（建议从真实浏览器复制）
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    # 其他优化参数
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    
    # 隐藏WebDriver特征（重要！）
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # 智能等待（先等页面基本加载完成）
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # 显式等待目标div（最长等待timeout秒）
        itinerary_div = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.daily_itinerary_con"))
        )
        
        content = itinerary_div.get_attribute('outerHTML')
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 成功保存: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ 提取失败 {url}: {str(e)}")
        return False
    finally:
        if driver:
            driver.quit()

def batch_extract_itineraries(input_file, output_dir, proxy=None):
    """
    批量处理URL文件中的每个链接
    :param input_file: 包含URL的文本文件（每行一个URL）
    :param output_dir: 输出目录路径
    """
    # 读取URL列表
    with open(input_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"📋 共发现 {len(urls)} 个待处理URL")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    success_count = 0
    for i, url in enumerate(urls, 1):
        print(f"\n🔍 正在处理 ({i}/{len(urls)}): {url}")
        
        # 生成唯一文件名（使用URL中的产品ID）
        product_id = url.split('/')[-1].split('?')[0].replace('p', '')[:10]
        output_file = os.path.join(output_dir, f"攻略_{product_id}.html")
        
        if os.path.exists(output_file):
            print(f"⏩ 已存在文件: {output_file}，跳过")
            success_count += 1
            continue

        # 执行提取
        if extract_dynamic_itinerary(url, output_file, proxy=proxy):
            success_count += 1
        
        # 礼貌延迟（避免被封）
        time.sleep(1)
    
    print(f"\n🎉 处理完成！成功 {success_count}/{len(urls)} 个")

def render_html_to_text(html_file, output_dir=None, wait_time=3):
    """
    将HTML文件渲染后转换为可读文本
    :param html_file: HTML文件路径
    :param output_dir: 输出目录（默认同HTML目录）
    :param wait_time: 渲染等待时间（秒）
    :return: 生成的文本文件路径
    """
    


    try:
        # 准备输出路径
        if not output_dir:
            output_dir = os.path.dirname(html_file)
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文本文件名
        base_name = os.path.splitext(os.path.basename(html_file))[0]
        txt_file = os.path.join(output_dir, f"{base_name}.txt")
        
        if os.path.exists(txt_file):
            print(f"⏩ 已存在文本文件: {txt_file}，跳过")
            return txt_file
        
        # 配置浏览器
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=chrome_options)
        # 构建本地文件URL
        abs_path = os.path.abspath(html_file)
        file_url = f"file://{abs_path}"
        
        # 加载本地HTML文件
        driver.get(file_url)
        time.sleep(wait_time)  # 等待渲染完成

        # 获取渲染后的文本
        visible_text = driver.find_element(By.TAG_NAME, "body").text
        


        # 保存文本
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(visible_text)
        
        print(f"✅ 文本已保存: {txt_file}")
        return txt_file

    except Exception as e:
        print(f"❌ 转换失败: {str(e)}")
        return None
    finally:
        driver.quit()

def batch_html_to_text(input_dir, output_dir=None, method='selenium'):
    """
    批量转换HTML为文本
    :param input_dir: 包含HTML的目录
    :param output_dir: 输出目录（默认创建text_output子目录）
    :param method: 'selenium' 或 'bs4'
    """
    if not output_dir:
        output_dir = os.path.join(input_dir, 'text_output')
    os.makedirs(output_dir, exist_ok=True)
    
    success = 0
    for file in os.listdir(input_dir):
        if file.endswith('.html'):
            html_path = os.path.join(input_dir, file)
            print(f"\n处理: {file}")
            
            if method == 'selenium':
                result = render_html_to_text(html_path, output_dir)
            
            if result:
                success += 1
    
    print(f"\n🎉 转换完成！成功 {success}/{len(os.listdir(input_dir))} 个文件")
    print(f"文本文件保存在: {os.path.abspath(output_dir)}")

# def process_city_urls_multi_thread(input_dir, output_base_dir):
#     """
#     多线程处理函数：读取城市URL文件，爬取攻略并转换为文本
#     :param input_dir: 包含城市URL文件的目录
#     :param output_base_dir: 输出根目录
#     """
#     # 创建输出目录结构
#     final_output_dir = os.path.join(output_base_dir, "旅游攻略文本")
#     os.makedirs(final_output_dir, exist_ok=True)
    
#     # 获取所有城市文件
#     city_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    
#     # 创建任务队列（每5个城市一组）
#     task_queue = Queue()
#     for i in range(0, len(city_files), 5):
#         task_queue.put(city_files[i:i+5])
    
#     # 线程锁（用于打印输出）
#     print_lock = threading.Lock()
    
#     def worker():
#         while not task_queue.empty():
#             try:
#                 files_batch = task_queue.get()
#                 for city_file in files_batch:
#                     # 提取城市名（从文件名）
#                     city_name = os.path.splitext(city_file)[0]
#                     city_url_file = os.path.join(input_dir, city_file)
                    
#                     # 为每个城市创建单独目录
#                     city_output_dir = os.path.join(final_output_dir, city_name)
#                     os.makedirs(city_output_dir, exist_ok=True)
                    
#                     with print_lock:
#                         print(f"\n{'='*40}")
#                         print(f"线程 {threading.current_thread().name} 正在处理城市: {city_name}")
                    
#                     # 第一步：爬取HTML攻略
#                     html_dir = os.path.join(city_output_dir, "HTML版本")
#                     batch_extract_itineraries(city_url_file, html_dir)
                    
#                     # 第二步：转换为文本
#                     batch_html_to_text(html_dir, os.path.join(city_output_dir, "文本版本"))
                    
#                     with print_lock:
#                         print(f"城市 {city_name} 处理完成！")
#             finally:
#                 task_queue.task_done()
    
#     # 创建并启动线程（根据CPU核心数调整线程数量）
#     num_threads = min(1, (len(city_files) + 4) // 5)  # 最多8个线程
#     threads = []
#     for i in range(num_threads):
#         t = threading.Thread(target=worker, name=f"CityWorker-{i+1}")
#         t.start()
#         threads.append(t)
    
#     # 等待所有任务完成
#     task_queue.join()
    
#     # 等待所有线程结束
#     for t in threads:
#         t.join()
    
#     print("所有城市处理完成！")

def process_city_urls_multi_thread(input_dir, output_base_dir, proxy_list):
    """
    多线程处理函数：读取城市URL文件，爬取攻略并转换为文本
    每个线程使用独立的代理IP
    
    :param input_dir: 包含城市URL文件的目录
    :param output_base_dir: 输出根目录
    :param proxy_list: 可用的代理IP列表，格式如 ["123.141.18.8:5031", "123.30.154.171:7777"]
    """
    # 创建输出目录结构
    final_output_dir = os.path.join(output_base_dir, "旅游攻略文本")
    os.makedirs(final_output_dir, exist_ok=True)
    
    # 获取所有城市文件
    city_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    
    # 创建任务队列（每5个城市一组）
    task_queue = Queue()
    for i in range(0, len(city_files), 5):
        task_queue.put(city_files[i:i+5])
    
    # 线程锁（用于打印输出和代理IP管理）
    print_lock = threading.Lock()
    proxy_lock = threading.Lock()
    
    # 代理IP状态字典
    proxy_status = {proxy: {"available": True, "last_used": 0} for proxy in proxy_list}
    
    def get_proxy_for_thread():
        """为线程获取一个可用的代理IP"""
        with proxy_lock:
            # 优先选择最近未使用的可用代理
            available_proxies = [p for p, status in proxy_status.items() if status["available"]]
            if not available_proxies:
                return None
            
            # 按最后使用时间排序，选择最久未使用的
            available_proxies.sort(key=lambda p: proxy_status[p]["last_used"])
            selected_proxy = available_proxies[0]
            proxy_status[selected_proxy]["last_used"] = time.time()
            return selected_proxy
    
    def mark_proxy_status(proxy, is_available):
        """更新代理IP状态"""
        with proxy_lock:
            if proxy in proxy_status:
                proxy_status[proxy]["available"] = is_available
                if not is_available:
                    print(f"标记代理 {proxy} 为不可用")
    
    def worker():
        """工作线程函数"""
        # 为当前线程获取代理
        proxy = get_proxy_for_thread()
        if not proxy:
            with print_lock:
                print(f"线程 {threading.current_thread().name} 启动失败: 无可用代理")
            return
            
        proxy_dict = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
        
        with print_lock:
            print(f"线程 {threading.current_thread().name} 启动，使用代理: {proxy}")
        
        while not task_queue.empty():
            try:
                files_batch = task_queue.get()
                for city_file in files_batch:
                    # 提取城市名（从文件名）
                    city_name = os.path.splitext(city_file)[0]
                    city_url_file = os.path.join(input_dir, city_file)
                    
                    # 为每个城市创建单独目录
                    city_output_dir = os.path.join(final_output_dir, city_name)
                    os.makedirs(city_output_dir, exist_ok=True)
                    
                    with print_lock:
                        print(f"\n{'='*40}")
                        print(f"线程 {threading.current_thread().name} (代理: {proxy}) 正在处理城市: {city_name}")
                    
                    try:
                        # 第一步：爬取HTML攻略（传入代理）
                        html_dir = os.path.join(city_output_dir, "HTML版本")
                        batch_extract_itineraries(city_url_file, html_dir, proxy=proxy_dict["https"])
                        
                        # 第二步：转换为文本
                        batch_html_to_text(html_dir, os.path.join(city_output_dir, "文本版本"))
                        
                        with print_lock:
                            print(f"城市 {city_name} 处理完成！")
                    except Exception as e:
                        with print_lock:
                            print(f"处理城市 {city_name} 时出错: {str(e)}")
                        # 标记代理可能有问题
                        # mark_proxy_status(proxy, False)
                        # 获取新代理
                        new_proxy = get_proxy_for_thread()
                        if new_proxy:
                            proxy = new_proxy
                            proxy_dict = {
                                "http": f"http://{proxy}",
                                "https": f"http://{proxy}"
                            }
                            with print_lock:
                                print(f"线程 {threading.current_thread().name} 切换为新代理: {proxy}")
                        else:
                            with print_lock:
                                print(f"线程 {threading.current_thread().name} 无可用代理，终止任务")
                            return
            finally:
                task_queue.task_done()
    
    # 创建并启动线程（根据CPU核心数和代理数量调整线程数量）
    num_threads = min(len(proxy_list), (len(city_files) + 4) // 5, 2)  # 最多8个线程或代理数量
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, name=f"CityWorker-{i+1}")
        t.start()
        threads.append(t)
    
    # 等待所有任务完成
    task_queue.join()
    
    # 等待所有线程结束
    for t in threads:
        t.join()
    
    print("所有城市处理完成！")



load_dotenv()

API_URL = os.getenv("API_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = os.getenv("API_KEY")

class AIChatAPI:
    def __init__(self):
        self.conversation_history: List[Dict] = []
        
    def send_request(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 2048) -> Dict :
        """发送API请求并保存到历史记录"""
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
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
            return {}

def txt_guide_to_md_guide(input_root, output_root):
    with open("/home/JingpengQin/travel_guide/code/txt2Markdown_Prompt.txt", "r", encoding="utf-8") as f:
        base_prompt = f.read()

# 配置路径
    #input_root = "E:/清华学习/大三夏季实习/代码/爬虫获取旅游攻略/输出结果/整理后的攻略/文本版本"
    #output_root = "E:/清华学习/大三夏季实习/代码/爬虫获取旅游攻略/输出结果/整理后的攻略/精标后Markdown版本+对应文本版本/精标Markdown版本"

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
    
    # 遍历城市下的所有txt文件
        for txt_file in os.listdir(city_input_path):
            if not txt_file.endswith('.txt'):
                continue
            
        # 获取基础文件名（不含扩展名）
            base_filename = os.path.splitext(txt_file)[0]
        
        # 检查是否已存在同名文件（不考虑几日游标记）
            if is_file_processed(city_output_path, base_filename):
                print(f"⏩ 已存在相关文件: {base_filename}*.md")
                continue
            
            try:
            # 构造完整路径
                txt_path = os.path.join(city_input_path, txt_file)
            
            # 读取文本内容
                with open(txt_path, 'r', encoding='utf-8') as f:
                    txt_content = f.read()
            
            # 构造完整Prompt
                full_prompt = base_prompt + "\n\n" + txt_content
            
            # 调用Qwen API
                response = AIChatAPI().send_request(
                    messages=[{"role": "user", "content": full_prompt}],
                    temperature=0.7,
                    max_tokens=2048
                )
            
            # 生成带几日游标记的文件名
                md_filename = get_output_filename(txt_file, response.text)
                md_path = os.path.join(city_output_path, md_filename)
            
            # 保存Markdown文件
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
            
                print(f"✅ 转换成功: {txt_file} → {md_filename}")
            
            # 礼貌延迟（避免API限流）
                time.sleep(2)
            
            except Exception as e:
                print(f"❌ 处理失败 {txt_file}: {str(e)}")
            # 保存错误日志
                with open(os.path.join(output_root, "error_log.txt"), 'a') as f:
                    f.write(f"{city_folder}/{txt_file} 处理失败: {str(e)}\n")

    print("\n所有城市处理完成!")

# 使用示例
if __name__ == "__main__":
    # 配置路径
    URL_FILES_DIR = "/home/JingpengQin/travel_guide/process_data/旅游攻略url"  # 存放城市URL文本文件的目录
    OUTPUT_DIR = "/home/JingpengQin/travel_guide/process_data/输出结果"       # 输出根目录
    proxies = [
    # "85.215.64.49:8O",        # 注意：端口"BO"可能无效
    # "38.54.71.67:8O",         # 同上
    "193.151.141.17:8O8O",     # 端口格式异常
    "123.141.181.32:5031",      # 有效
    "123.30.154.171:7777",    # 有效
    "18.171.55.201:3128",     # 有效
    "51.81.245.3:17981",      # 有效(注意IP第三段812超过255)
    "156.38.112.11:8O",       # 端口无效
    "123.141.181.86:5031"      # 有效
]
    # 执行处理
    process_city_urls_multi_thread(URL_FILES_DIR, OUTPUT_DIR, proxies)
    print("\n所有城市处理完毕! 文本文件保存在: ", OUTPUT_DIR)