import re
import os

def extract_book_info(text):
    """
    升级版：提取书籍信息并格式化为参考文献标准格式
    增强了对无格式纯文本的识别容错率
    """
    # 扩大检索范围到前5000字，通常能覆盖扉页和版权页(CIP数据)
    head_text = text[:5000]
    
    # ---------------- 1. 提取书名 (Title) ----------------
    # 策略A：找明确的标识符
    title_match = re.search(r'(?:书名|题名|书 名|Title)[\s:：]+([^\n]+)', head_text)
    if title_match:
        title_str = title_match.group(1).strip()
    else:
        # 策略B：取文本第一行非空字符作为书名（绝大部分TXT的规律）
        lines = [line.strip() for line in head_text.split('\n') if line.strip()]
        title_str = lines[0] if lines else "[未知书名]"
        # 过滤掉可能存在的特殊符号如 # * = 【】等
        title_str = re.sub(r'^[#\*=【】\s]+', '', title_str)

    # ---------------- 2. 提取作者 (Author) ----------------
    # 策略A：找标识符
    author_match = re.search(r'(?:作者|作 者|编者|主编|著|编著)[\s:：]+([^\n]+)', head_text)
    if not author_match:
        # 策略B：找以“著”、“编著”结尾的行（例如：“郑浩峻 著”）
        author_match = re.search(r'^([^\n]+?)\s*(?:著|编著|主编)$', head_text, re.MULTILINE)
    
    author_str = author_match.group(1).strip() if author_match else "[未知作者]"
    author_str = re.sub(r'[:：\s]', '', author_str) # 清除多余标点和空格

    # ---------------- 3. 提取出版社 (Publisher) ----------------
    # 匹配任何以“出版社”、“出版公司”、“书局”结尾的词组
    pub_match = re.search(r'([^\n,，:：\s]+?(?:出版社|出版公司|书局))', head_text)
    publisher_str = pub_match.group(1).strip() if pub_match else "[未知出版社]"

    # ---------------- 4. 提取出版年 (Publication Year) ----------------
    # 匹配 19XX 或 20XX 年
    year_match = re.search(r'(19\d{2}|20\d{2})\s*年', head_text)
    if not year_match:
        # 匹配 2011-05 或 2011.05 这种格式
        year_match = re.search(r'(19\d{2}|20\d{2})[-./年]', head_text)
    pub_year_str = year_match.group(1) if year_match else "[未知年份]"

    # ---------------- 5. 提取出版地 (Publication Place) ----------------
    # 图书在版编目(CIP)数据中通常是 “城市：出版社” 的格式
    pub_place_str = "[未知出版地]"
    if publisher_str != "[未知出版社]":
        # 动态构建正则，寻找紧挨在出版社前面的城市名（通常为2-4个中文字符）
        place_pattern = rf'([\u4e00-\u9fa5]{{2,4}})[\s:：]+{re.escape(publisher_str)}'
        place_match = re.search(place_pattern, head_text)
        if place_match:
            pub_place_str = place_match.group(1).strip()

    # ---------------- 组合输出格式 ----------------
    book = f"【{author_str}. {title_str}[M]. {pub_place_str}: {publisher_str}, {pub_year_str}.】"
    return book

def search_in_txt(filepath, keyword):
    """
    任务2 & 3：检索关键字的页码(loca)和文段(para)
    """
    if not os.path.exists(filepath):
        print(f"错误：找不到文件 '{filepath}'")
        return None, [], []
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except UnicodeDecodeError:
        # 兼容不同的中文编码
        with open(filepath, 'r', encoding='gbk') as f:
            text = f.read()

    # 1. 获取书籍信息
    book = extract_book_info(text)
    
    # 初始化变量（由于关键字可能出现多次，loca和para使用列表存储）
    loca = []  
    para = []  
    
    # 2. 利用正则按页码分割文本
    # 模式解析：非贪婪匹配任意字符 (.*?)，直到遇到 ≦ 数字 ≧
    # re.DOTALL 允许 . 匹配换行符
    page_pattern = re.compile(r'(.*?)≦\s*(\d+)\s*≧', re.DOTALL)
    
    last_idx = 0
    for match in page_pattern.finditer(text):
        page_text = match.group(1)  # 当前页的文本内容
        page_num = match.group(2)   # 当前页码
        
        # 如果当前页包含关键字
        if keyword in page_text:
            # 将当前页按换行符拆分成段落
            paragraphs = page_text.split('\n')
            for p in paragraphs:
                if keyword in p:
                    # 去除段落两端的空白字符并存储
                    loca.append(page_num)
                    para.append(p.strip())
                    
        last_idx = match.end()
        
    # 3. 处理文件末尾可能没有页码标记的剩余文本
    remaining_text = text[last_idx:]
    if keyword in remaining_text:
        paragraphs = remaining_text.split('\n')
        for p in paragraphs:
            if keyword in p:
                loca.append("尾部无页码区域")
                para.append(p.strip())
                
    return book, loca, para

# ================= 测试与输出部分 =================
if __name__ == "__main__":
    # 配置您的文件路径和关键字（请确保当前目录下有一个 test.txt 文件）
    file_path = input("请输入文件名，确保TXT格式文件在当前文件夹下")+'.txt' 
    search_keyword = input("请输入关键词/句")
    
    # 执行检索
    book_info, loca_list, para_list = search_in_txt(file_path, search_keyword)
    
    # 按照要求输出结果
    if book_info:
        print("="*50)
        print("1、书籍信息：")
        print(book_info)
        print("="*50)
        
        print(f"关键字/句子：【{search_keyword}】")
        print(f"共检索到 {len(loca_list)} 处匹配：\n")
        
        for i in range(len(loca_list)):
            print(f"【匹配项 {i+1}】")
            print(f"2、页码 (loca): ≦ {loca_list[i]} ≧")
            print(f"3、文段 (para): {para_list[i]}\n")
            print("-" * 30)
