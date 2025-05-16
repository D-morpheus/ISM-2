#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime
import re

class SimpleSpider:
    """
    简单网页爬虫类：用于抓取网页标题和所有有效链接。
    """

    def __init__(self):
        """
        初始化参数，包括请求头、超时设置和最大重试次数。
        """
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            )
        }
        self.timeout = 10
        self.max_retries = 3

    def get_page(self, url):
        """
        发送 GET 请求获取网页内容，包含重试机制。
        参数:
            url (str): 要访问的网页地址。
        返回:
            str or None: HTML 内容或失败时返回 None。
        """
        for i in range(self.max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                response.encoding = 'utf-8'
                return response.text
            except Exception as e:
                print(f"[错误] 第 {i + 1} 次请求失败: {type(e).__name__} - {str(e)}")
                if i < self.max_retries - 1:
                    time.sleep(random.uniform(1, 3))
        return None

    def parse_page(self, html):
        """
        使用 BeautifulSoup 解析网页，提取标题和所有有效超链接。
        参数:
            html (str): 网页 HTML 内容。
        返回:
            list: 包含字典的结果列表，每项包括 title 和 url。
        """
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        results = []

        try:
            title = soup.title.string.strip() if soup.title and soup.title.string else "无标题"
            for link in soup.find_all('a'):
                href = link.get('href')
                text = link.get_text().strip()
                if href and href.startswith(('http://', 'https://')):
                    results.append({
                        'title': text or '无文本',
                        'url': href
                    })
            return results
        except Exception as e:
            print(f"[错误] 解析页面时出错: {type(e).__name__} - {str(e)}")
            return []

    def save_results(self, results, filename=None):
        """
        将抓取结果保存到文本文件中。
        参数:
            results (list): 要保存的数据列表。
            filename (str): 可选的输出文件名。
        返回:
            bool: 保存成功返回 True，失败返回 False。
        """
        if filename is None:
            filename = f"spider_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n")
                for item in results:
                    f.write(f"标题: {item['title']}\n")
                    f.write(f"链接: {item['url']}\n")
                    f.write("-" * 30 + "\n")
            print(f"[提示] 结果已保存到文件: {filename}")
            return True
        except Exception as e:
            print(f"[错误] 保存结果失败: {type(e).__name__} - {str(e)}")
            return False

    def __str__(self):
        return f"<SimpleSpider retries={self.max_retries}, timeout={self.timeout}s>"

def is_valid_url(url):
    """
    简单校验 URL 合法性。
    参数:
        url (str): 用户输入的 URL。
    返回:
        bool: 合法返回 True。
    """
    return url.startswith("http://") or url.startswith("https://")

def main():
    """
    主程序入口：控制流程与用户交互。
    """
    spider = SimpleSpider()

    print("请输入要爬取的网页地址：")
    url = input().strip()

    if not url:
        print("[错误] URL 不能为空。")
        return
    if not is_valid_url(url):
        print("[错误] 请输入合法的 HTTP 或 HTTPS 链接。")
        return

    print(f"[提示] 开始爬取: {url}")
    html = spider.get_page(url)

    if not html:
        print("[错误] 获取网页内容失败。")
        return

    results = spider.parse_page(html)

    if not results:
        print("[提示] 未提取到任何有效链接。")
        return

    print(f"[提示] 共找到 {len(results)} 个链接。")
    spider.save_results(results)

if __name__ == "__main__":
    main()
