## 代码运行环境：
python版本：3.11.13 <br>
安装下列包：BeautifulSoup、requests、python-dotenv、selenium<br>
参考安装命令：
>pip install beautifulsoup4 requests python-dotenv selenium<br>

注:使用Selenium时需要对应浏览器驱动，推荐使用webdriver-manager自动管理驱动版本，没有安装驱动可以使用命令 pip install webdriver-manager 安装
## 代码使用方法
1、运行get_travel_guide_url_multi_thread.py,获取旅游攻略网页的url，结果存放在“process_data/旅游攻略url”中。

2、之后运行url2travel_guide_in_txt_multi_thread.py,通过url获取网页中旅游攻略的内容并且最终转换为txt文件，结果存放在“process_data/输出结果/旅游攻略文本”中，其中同时包含了txt文件和html文件。

3、之后运行txt2md_in_multi_thread.py,将txt攻略通过大模型转换为符合要求的md文件，结果存放在“process_data/输出结果/旅游攻略Markdown”中。

4、之后运行add_md_title.py,给每个攻略加上标题。

5、之后运行y2x_multi_thread.py,生成最终的json格式的约束条件和对应的自然语言问题，结果存放在“final_data”中。

（Todo）6、之后运行“划分程序”，将城市随机划分为8:1:1的不同的数据集，包含（x0，y4），用于后面的Env-LLM和Planner-LLM使用。

注：代码使用绝对路径，可能需要修改为本地的绝对路径后才能运行。

