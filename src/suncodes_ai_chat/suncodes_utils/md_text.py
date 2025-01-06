"""
处理 MD 文档
"""
import markdown
from bs4 import BeautifulSoup

def markdown_to_text(markdown_string):
    """
    md 字符串 转为纯字符串
    :param markdown_string: md格式字符串
    :return:
    """
    if markdown_string is None or markdown_string.strip() == "":
        return ""
    # 将 Markdown 转换为 HTML
    md = markdown.Markdown(extensions=['tables', 'fenced_code'])
    html = md.convert(markdown_string)
    # 使用 BeautifulSoup 提取纯文本
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()
