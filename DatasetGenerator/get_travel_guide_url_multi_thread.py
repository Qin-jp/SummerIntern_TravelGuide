from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urljoin
import threading
from queue import Queue


# 设置请求头模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://vacations.ctrip.com/'
}

def get_product_links(base_url, max_pages=3):
    """
    从产品列表页面获取具体产品详情页的链接
    :param base_url: 产品列表页面的URL
    :param max_pages: 最大爬取页数
    :return: 产品详情页面的URL列表
    """
    product_links = []
    
    for page in range(1, max_pages + 1):
        # 构造分页URL（携程的分页参数是pagenum）
        page_url = base_url + "&p=1"
        page_url = page_url.replace('p=1', f'p={page}')
        #page_url = f"{base_url.split('?')[0]}?pagenum={page}&{base_url.split('?')[1]}"
        
        try:
            print(f"正在爬取第{page}页: {page_url}")
            response = requests.get(page_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 方法1：直接从HTML中解析产品链接（适用于静态页面）
            items = soup.find_all('div', class_='product-item')
            for item in items:
                link_tag = item.find('a', href=re.compile(r'/tour/detail/p\d+s\d+'))
                if link_tag and 'href' in link_tag.attrs:
                    product_url = urljoin('https://vacations.ctrip.com/', link_tag['href'])
                    product_links.append(product_url)
            
            # 方法2：从JSON数据中提取（适用于动态加载）
            script_tags = soup.find_all('script')
            pattern = re.compile(r'"ONLINE":"(https://vacations\.ctrip\.com/tour/detail/p\d+s\d+)"')
            for script in script_tags:
                if script.string:
                    matches = pattern.findall(script.string)
                    product_links.extend(matches)
            
            # 去重
            product_links = list(set(product_links))
            
            print(f"当前已找到{len(product_links)}个产品链接")
            
            # 随机延迟，避免请求过于频繁
            time.sleep(random.uniform(2, 5))
            
        except Exception as e:
            print(f"爬取第{page}页时出错: {str(e)}")
            continue
    
    return product_links

def save_urls_to_txt(url_list, filename):
    """
    将URL列表保存到文本文件（每行一个URL）
    :param url_list: URL列表，例如 ["https://example.com/1", "https://example.com/2"]
    :param filename: 要保存的文件名（如 "urls.txt"）
    """
    if not url_list:
        print("没有URL需要保存")
        return
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for url in url_list:
                f.write(url + '\n')  # 每行写入一个URL
        print(f"✅ 成功保存 {len(url_list)} 个URL到 {filename}")
    except Exception as e:
        print(f"❌ 保存文件时出错: {str(e)}")


if __name__ == "__main__":  
    #一共16个城市
    china_cities = [
    ["北京市", ["北京市"]],
    ["天津市", ["天津市"]],
    ["上海市", ["上海市"]],
    ["重庆市", ["重庆市"]],
    ["河北省", [
        "石家庄市", "唐山市", "秦皇岛市", "邯郸市", "邢台市", 
        "保定市", "张家口市", "承德市", "沧州市", "廊坊市", "衡水市"
    ]],
    ["山西省", [
        "太原市", "大同市", "阳泉市", "长治市", "晋城市",
        "朔州市", "晋中市", "运城市", "忻州市", "临汾市", "吕梁市"
    ]],
    ["内蒙古自治区", [
        "呼和浩特市", "包头市", "乌海市", "赤峰市", "通辽市",
        "鄂尔多斯市", "呼伦贝尔市", "巴彦淖尔市", "乌兰察布市",
        "兴安盟", "锡林郭勒盟", "阿拉善盟"
    ]],
    ["辽宁省", [
        "沈阳市", "大连市", "鞍山市", "抚顺市", "本溪市",
        "丹东市", "锦州市", "营口市", "阜新市", "辽阳市",
        "盘锦市", "铁岭市", "朝阳市", "葫芦岛市"
    ]],
    ["吉林省", [
        "长春市", "吉林市", "四平市", "辽源市", "通化市",
        "白山市", "松原市", "白城市", "延边朝鲜族自治州"
    ]],
    ["黑龙江省", [
        "哈尔滨市", "齐齐哈尔市", "鸡西市", "鹤岗市", "双鸭山市",
        "大庆市", "伊春市", "佳木斯市", "七台河市", "牡丹江市",
        "黑河市", "绥化市", "大兴安岭地区"
    ]],
    ["江苏省", [
        "南京市", "无锡市", "徐州市", "常州市", "苏州市",
        "南通市", "连云港市", "淮安市", "盐城市", "扬州市",
        "镇江市", "泰州市", "宿迁市"
    ]],
    ["浙江省", [
        "杭州市", "宁波市", "温州市", "嘉兴市", "湖州市",
        "绍兴市", "金华市", "衢州市", "舟山市", "台州市",
        "丽水市"
    ]],
    ["安徽省", [
        "合肥市", "芜湖市", "蚌埠市", "淮南市", "马鞍山市",
        "淮北市", "铜陵市", "安庆市", "黄山市", "滁州市",
        "阜阳市", "宿州市", "六安市", "亳州市", "池州市",
        "宣城市"
    ]],
    ["福建省", [
        "福州市", "厦门市", "莆田市", "三明市", "泉州市",
        "漳州市", "南平市", "龙岩市", "宁德市"
    ]],
    ["江西省", [
        "南昌市", "景德镇市", "萍乡市", "九江市", "新余市",
        "鹰潭市", "赣州市", "吉安市", "宜春市", "抚州市",
        "上饶市"
    ]],
    ["山东省", [
        "济南市", "青岛市", "淄博市", "枣庄市", "东营市",
        "烟台市", "潍坊市", "济宁市", "泰安市", "威海市",
        "日照市", "临沂市", "德州市", "聊城市", "滨州市",
        "菏泽市"
    ]],
    ["河南省", [
        "郑州市", "开封市", "洛阳市", "平顶山市", "安阳市",
        "鹤壁市", "新乡市", "焦作市", "濮阳市", "许昌市",
        "漯河市", "三门峡市", "南阳市", "商丘市", "信阳市",
        "周口市", "驻马店市", "济源市"
    ]],
    ["湖北省", [
        "武汉市", "黄石市", "十堰市", "宜昌市", "襄阳市",
        "鄂州市", "荆门市", "孝感市", "荆州市", "黄冈市",
        "咸宁市", "随州市", "恩施土家族苗族自治州", "仙桃市",
        "潜江市", "天门市", "神农架林区"
    ]],
    ["湖南省", [
        "长沙市", "株洲市", "湘潭市", "衡阳市", "邵阳市",
        "岳阳市", "常德市", "张家界市", "益阳市", "郴州市",
        "永州市", "怀化市", "娄底市", "湘西土家族苗族自治州"
    ]],
    ["广东省", [
        "广州市", "韶关市", "深圳市", "珠海市", "汕头市",
        "佛山市", "江门市", "湛江市", "茂名市", "肇庆市",
        "惠州市", "梅州市", "汕尾市", "河源市", "阳江市",
        "清远市", "东莞市", "中山市", "潮州市", "揭阳市",
        "云浮市"
    ]],
    ["广西壮族自治区", [
        "南宁市", "柳州市", "桂林市", "梧州市", "北海市",
        "防城港市", "钦州市", "贵港市", "玉林市", "百色市",
        "贺州市", "河池市", "来宾市", "崇左市"
    ]],
    ["海南省", [
        "海口市", "三亚市", "三沙市", "儋州市", 
        "五指山市", "琼海市", "文昌市", "万宁市", "东方市",
        "定安县", "屯昌县", "澄迈县", "临高县", "白沙黎族自治县",
        "昌江黎族自治县", "乐东黎族自治县", "陵水黎族自治县",
        "保亭黎族苗族自治县", "琼中黎族苗族自治县"
    ]],
    ["四川省", [
        "成都市", "自贡市", "攀枝花市", "泸州市", "德阳市",
        "绵阳市", "广元市", "遂宁市", "内江市", "乐山市",
        "南充市", "眉山市", "宜宾市", "广安市", "达州市",
        "雅安市", "巴中市", "资阳市", "阿坝藏族羌族自治州",
        "甘孜藏族自治州", "凉山彝族自治州"
    ]],
    ["贵州省", [
        "贵阳市", "六盘水市", "遵义市", "安顺市", "毕节市",
        "铜仁市", "黔西南布依族苗族自治州", "黔东南苗族侗族自治州",
        "黔南布依族苗族自治州"
    ]],
    ["云南省", [
        "昆明市", "曲靖市", "玉溪市", "保山市", "昭通市",
        "丽江市", "普洱市", "临沧市", "楚雄彝族自治州",
        "红河哈尼族彝族自治州", "文山壮族苗族自治州", "西双版纳傣族自治州",
        "大理白族自治州", "德宏傣族景颇族自治州", "怒江傈僳族自治州",
        "迪庆藏族自治州"
    ]],
    ["西藏自治区", [
        "拉萨市", "日喀则市", "昌都市", "林芝市", "山南市",
        "那曲市", "阿里地区"
    ]],
    ["陕西省", [
        "西安市", "铜川市", "宝鸡市", "咸阳市", "渭南市",
        "延安市", "汉中市", "榆林市", "安康市", "商洛市"
    ]],
    ["甘肃省", [
        "兰州市", "嘉峪关市", "金昌市", "白银市", "天水市",
        "武威市", "张掖市", "平凉市", "酒泉市", "庆阳市",
        "定西市", "陇南市", "临夏回族自治州", "甘南藏族自治州"
    ]],
    ["青海省", [
        "西宁市", "海东市", "海北藏族自治州", "黄南藏族自治州",
        "海南藏族自治州", "果洛藏族自治州", "玉树藏族自治州",
        "海西蒙古族藏族自治州"
    ]],
    ["宁夏回族自治区", [
        "银川市", "石嘴山市", "吴忠市", "固原市", "中卫市"
    ]],
    ["新疆维吾尔自治区", [
        "乌鲁木齐市", "克拉玛依市", "吐鲁番市", "哈密市",
        "昌吉回族自治州", "博尔塔拉蒙古自治州", "巴音郭楞蒙古自治州",
        "阿克苏地区", "克孜勒苏柯尔克孜自治州", "喀什地区",
        "和田地区", "伊犁哈萨克自治州", "塔城地区", "阿勒泰地区",
        "石河子市", "阿拉尔市", "图木舒克市", "五家渠市",
        "北屯市", "铁门关市", "双河市", "可克达拉市", "昆玉市"
    ]],
    ["香港特别行政区", ["香港特别行政区"]],
    ["澳门特别行政区", ["澳门特别行政区"]],
    ["台湾省", [
        "台北市", "新北市", "桃园市", "台中市", "台南市", 
        "高雄市", "基隆市", "新竹市", "嘉义市", "新竹县",
        "苗栗县", "彰化县", "南投县", "云林县", "嘉义县",
        "屏东县", "宜兰县", "花莲县", "台东县", "澎湖县",
        "金门县", "连江县"
    ]]
]





    # cities = ['北京', '上海', '广州', '深圳', '成都', '重庆', '杭州', '南京', '武汉', '西安', '青岛', '厦门', '三亚', '丽江', '大理', '张家界'] 
    base_url = "https://vacations.ctrip.com/list/whole/sc2.html"

    # 线程安全的集合存储所有URL
    all_url = set()
    lock = threading.Lock()

# 创建队列存储省份数据
    province_queue = Queue()

# 将省份数据放入队列（每两个省份一组）
    for i in range(0, len(china_cities), 2):
        provinces = china_cities[i:i+2]
        province_queue.put(provinces)

    def process_provinces(provinces):
        for province, cities in provinces:
            print(f"线程 {threading.current_thread().name} 正在处理省份: {province}")
            for city in cities:
                encoded_city = quote(city)
                params = {
                "sv": encoded_city,
                "st": encoded_city,
                "from": "do",
                "startcity": 2
                }
                url = f"{base_url}?{'&'.join(f'{k}={v}' for k,v in params.items())}"
                product_urls = get_product_links(url, max_pages=3)
            
            # 线程安全地更新集合
                with lock:
                    all_url.update(product_urls)
            
                save_urls_to_txt(product_urls, f"/home/JingpengQin/travel_guide/process_data/旅游攻略url/{city}旅游攻略.txt")

    def worker():
        while not province_queue.empty():
            provinces = province_queue.get()
            try:
                process_provinces(provinces)
            finally:
                province_queue.task_done()

# 创建并启动线程
    threads = []
    for i in range(17):  # 5个线程
        t = threading.Thread(target=worker, name=f"Thread-{i+1}")
        t.start()
        threads.append(t)

# 等待所有任务完成
    province_queue.join()

# 等待所有线程结束
    for t in threads:
        t.join()

    print("所有省份处理完成！")

    with open('/home/JingpengQin/travel_guide/process_data/旅游攻略url/AAA所有城市旅游攻略.txt', 'w', encoding='utf-8') as f:
        for url in all_url:
            f.write(url + '\n')
    print(f"所有城市的旅游攻略链接已保存，共 {len(all_url)} 个链接。")
    print("程序执行完毕！")
