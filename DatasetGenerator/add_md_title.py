import os
import re

def add_titles_to_md(root_dir):
    assert os.path.isdir(root_dir) is True  # 确保路径存在
    for dirpath, _, filenames in os.walk(root_dir):
        print(f"正在处理目录: {dirpath}")
        if dirpath.endswith("旅游攻略"):
            # 提取城市名（如 "鹤壁市"）
            city = os.path.basename(dirpath).replace("旅游攻略", "")
            
            for filename in filenames:
                if filename.endswith(".md"):
                    filepath = os.path.join(dirpath, filename)
                    
                    # 提取天数（如 "3日游"）
                    match = re.search(r"(\d+)日游", filename)
                    if not match:
                        continue
                    days = match.group(0)
                    
                    # 构造标题
                    title = f"# {city}{days}旅游攻略"
                    
                    # 检查是否已有标题
                    with open(filepath, "r+", encoding="utf-8") as f:
                        content = f.read()
                        if not content.startswith("# "):
                            # 在开头插入标题
                            f.seek(0, 0)
                            f.write(title + "\n\n" + content)
                            print(f"已添加标题: {filepath} → {title}")
                        else:
                            print(f"文件已有标题，跳过: {filepath}")

# 用法：传入你的旅游攻略目录
# add_titles_to_md("/home/JingpengQin/travel_guide/test_code_in_small_scale/旅游攻略Markdown")

add_titles_to_md("/home/JingpengQin/travel_guide/process_data/输出结果/旅游攻略Markdown")