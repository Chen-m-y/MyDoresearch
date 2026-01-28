#!/usr/bin/env python3
"""
IEEE PDF完整下载器
修复临时文件冲突问题
"""

import requests
import re
import time
import os
import sys
import argparse
import tempfile
import uuid
from urllib.parse import urljoin, unquote
import html


class IEEEDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://ieeexplore.ieee.org"

        # 设置请求头模拟真实浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive',
        })

    def extract_pdf_urls(self, article_number):
        """提取所有可能的PDF URL"""
        urls = []

        # 访问stamp页面获取PDF链接
        stamp_url = f"{self.base_url}/stamp/stamp.jsp?tp=&arnumber={article_number}"

        try:
            print("正在分析PDF页面...")
            response = self.session.get(stamp_url, timeout=30)
            if response.status_code != 200:
                print(f"无法访问stamp页面: HTTP {response.status_code}")
                return urls

            content = response.text

            # 方法1: 查找embed标签中的original-url
            embed_pattern = r'original-url="([^"]*stampPDF/getPDF\.jsp[^"]*)"'
            matches = re.findall(embed_pattern, content)
            for match in matches:
                # 解码HTML实体
                url = html.unescape(match)
                if url not in urls:
                    urls.append(url)
                    print(f"找到URL (embed): {url}")

            # 方法2: 查找直接的PDF文件URL (ielx格式)
            pdf_patterns = [
                r'https://ieeexplore\.ieee\.org/ielx[^"]*\.pdf[^"]*',
                r'/ielx[^"]*\.pdf[^"]*',
                r'"(https://ieeexplore\.ieee\.org/ielx[^"]*\.pdf[^"]*)"',
                r'"(/ielx[^"]*\.pdf[^"]*)"'
            ]

            for pattern in pdf_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    url = match
                    if url.startswith('/'):
                        url = f"{self.base_url}{url}"
                    if url not in urls:
                        urls.append(url)
                        print(f"找到URL (直接): {url}")

            # 方法3: 查找iframe src
            iframe_patterns = [
                r'<iframe[^>]*src="([^"]*ielx[^"]*\.pdf[^"]*)"',
                r'<iframe[^>]*src="([^"]*stampPDF[^"]*)"'
            ]

            for pattern in iframe_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    url = html.unescape(match)
                    if url.startswith('/'):
                        url = f"{self.base_url}{url}"
                    if url not in urls:
                        urls.append(url)
                        print(f"找到URL (iframe): {url}")

            # 方法4: 构造标准的getPDF URL
            standard_urls = [
                f"{self.base_url}/stampPDF/getPDF.jsp?tp=&arnumber={article_number}",
                f"{self.base_url}/stampPDF/getPDF.jsp?tp=&arnumber={article_number}&ref=",
            ]

            for url in standard_urls:
                if url not in urls:
                    urls.append(url)
                    print(f"添加标准URL: {url}")

        except Exception as e:
            print(f"分析PDF页面时出错: {e}")

        return urls

    def download_from_url(self, url, output_path, article_number):
        """从指定URL下载PDF"""
        try:
            # 设置正确的请求头
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Priority': 'u=0, i',
                'Referer': f'https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={article_number}',
                'Sec-Ch-Ua': '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'iframe',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Upgrade-Insecure-Requests': '1',
            }

            print(f"尝试从URL下载: {url}")
            response = self.session.get(url, headers=headers, timeout=60, stream=True)

            if response.status_code == 200:
                # 检查Content-Type
                content_type = response.headers.get('Content-Type', '').lower()

                # 生成唯一的临时文件名，避免冲突
                temp_file_id = uuid.uuid4().hex[:8]
                temp_file = output_path + f".tmp_{temp_file_id}"

                try:
                    with open(temp_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    # 验证下载的文件是否是PDF
                    if self._is_valid_pdf(temp_file):
                        # 如果目标文件已存在，先删除
                        if os.path.exists(output_path):
                            try:
                                os.remove(output_path)
                            except OSError as e:
                                print(f"警告: 无法删除现有文件 {output_path}: {e}")

                        # 重命名临时文件
                        try:
                            os.rename(temp_file, output_path)
                            file_size = os.path.getsize(output_path)
                            print(f"✅ PDF下载成功: {output_path}")
                            print(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
                            return True
                        except OSError as e:
                            print(f"❌ 文件重命名失败: {e}")
                            # 尝试复制文件内容
                            try:
                                with open(temp_file, 'rb') as src, open(output_path, 'wb') as dst:
                                    dst.write(src.read())
                                os.remove(temp_file)
                                file_size = os.path.getsize(output_path)
                                print(f"✅ PDF下载成功（通过复制）: {output_path}")
                                print(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
                                return True
                            except Exception as copy_e:
                                print(f"❌ 文件复制也失败: {copy_e}")
                                return False
                    else:
                        # 检查是否是HTML错误页面
                        with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content_preview = f.read(1000)

                        if 'html' in content_preview.lower():
                            print(f"❌ 收到HTML页面而不是PDF")
                            # 尝试从HTML中提取更多信息
                            if 'access denied' in content_preview.lower() or 'unauthorized' in content_preview.lower():
                                print("   可能需要订阅或付费访问")
                            elif 'not found' in content_preview.lower():
                                print("   PDF文件未找到")
                        else:
                            print(f"❌ 下载的文件不是有效的PDF")

                        return False

                finally:
                    # 清理临时文件
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except OSError:
                            pass

            elif response.status_code == 403:
                print(f"❌ 访问被拒绝 (403)")
                return False
            elif response.status_code == 404:
                print(f"❌ 资源未找到 (404)")
                return False
            else:
                print(f"❌ HTTP错误 {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ 下载出错: {e}")
            return False

    def download_pdf(self, article_number, output_path=None):
        """下载PDF文件的主函数"""
        if output_path is None:
            output_path = f"ieee_paper_{article_number}.pdf"

        print(f"正在下载论文 {article_number}...")

        # 步骤1: 访问文档页面建立会话
        doc_url = f"{self.base_url}/document/{article_number}/"
        print(f"步骤1: 访问文档页面...")

        try:
            doc_response = self.session.get(doc_url, timeout=30)
            if doc_response.status_code != 200:
                print(f"❌ 无法访问文档页面: HTTP {doc_response.status_code}")
                return False

            # 更新referer
            self.session.headers.update({'Referer': doc_url})

        except Exception as e:
            print(f"❌ 访问文档页面出错: {e}")
            return False

        # 步骤2: 提取所有可能的PDF URL
        pdf_urls = self.extract_pdf_urls(article_number)

        if not pdf_urls:
            print("❌ 未找到任何PDF下载链接")
            return False

        print(f"步骤3: 尝试下载PDF (找到 {len(pdf_urls)} 个候选URL)...")

        # 步骤3: 尝试每个URL直到成功
        for i, url in enumerate(pdf_urls, 1):
            print(f"\n尝试 {i}/{len(pdf_urls)}: ")
            if self.download_from_url(url, output_path, article_number):
                return True

            # 在尝试下一个URL前稍等
            if i < len(pdf_urls):
                time.sleep(2)

        print(f"\n❌ 所有下载方法都失败了")
        print("可能的原因:")
        print("1. 该论文需要订阅或付费访问")
        print("2. 您的IP地址没有机构访问权限")
        print("3. IEEE网站的访问控制策略")
        print("4. 论文编号不存在")

        return False

    def _is_valid_pdf(self, file_path):
        """检查文件是否是有效的PDF"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                return header == b'%PDF'
        except:
            return False

    def get_paper_info(self, article_number):
        """获取论文基本信息"""
        url = f"{self.base_url}/document/{article_number}/"
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                content = response.text

                # 提取标题
                title_match = re.search(r'<title>([^<]+)</title>', content)
                title = title_match.group(1) if title_match else "未知标题"

                # 清理标题
                title = title.replace(' | IEEE Journals & Magazine | IEEE Xplore', '')
                title = title.replace(' | IEEE Conference Publication | IEEE Xplore', '')

                return {
                    'article_number': article_number,
                    'title': title.strip(),
                    'status': 'found',
                    'url': url
                }
            else:
                return {
                    'article_number': article_number,
                    'status': 'not_found',
                    'error': f'HTTP {response.status_code}'
                }
        except Exception as e:
            return {
                'article_number': article_number,
                'status': 'error',
                'error': str(e)
            }

    def batch_download(self, article_numbers, output_dir="downloads"):
        """批量下载多篇论文"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        results = []

        for i, article_number in enumerate(article_numbers, 1):
            print(f"\n{'=' * 60}")
            print(f"下载进度: {i}/{len(article_numbers)}")
            print(f"{'=' * 60}")

            # 获取论文信息
            info = self.get_paper_info(article_number)
            if info['status'] == 'found':
                print(f"标题: {info['title']}")

            # 生成安全的文件名
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', info.get('title', 'unknown'))[:100]
            output_path = os.path.join(output_dir, f"{article_number}_{safe_title}.pdf")

            success = self.download_pdf(article_number, output_path)
            results.append({
                'article_number': article_number,
                'title': info.get('title', 'unknown'),
                'success': success,
                'output_path': output_path if success else None
            })

            # 避免请求过于频繁
            if i < len(article_numbers):
                time.sleep(3)

        # 输出批量下载结果
        print(f"\n{'=' * 60}")
        print(f"批量下载完成")
        print(f"{'=' * 60}")
        successful = sum(1 for r in results if r['success'])
        print(f"成功下载: {successful}/{len(article_numbers)}")

        for result in results:
            status = "✅" if result['success'] else "❌"
            print(
                f"{status} {result['article_number']}: {result['title'][:50]}{'...' if len(result['title']) > 50 else ''}")

        return results


def main():
    parser = argparse.ArgumentParser(description='IEEE PDF下载器')
    parser.add_argument('article_numbers', nargs='+', help='IEEE文章编号')
    parser.add_argument('-o', '--output', help='输出文件路径 (仅单个文件时有效)')
    parser.add_argument('-d', '--output-dir', default='downloads', help='批量下载的输出目录')
    parser.add_argument('--info', action='store_true', help='仅获取论文信息，不下载')

    args = parser.parse_args()

    downloader = IEEEDownloader()

    if args.info:
        # 仅获取论文信息
        for article_number in args.article_numbers:
            info = downloader.get_paper_info(article_number)
            print(f"文章编号: {info['article_number']}")
            print(f"状态: {info['status']}")
            if 'title' in info:
                print(f"标题: {info['title']}")
            if 'error' in info:
                print(f"错误: {info['error']}")
            print("-" * 50)

    elif len(args.article_numbers) == 1:
        # 单个文件下载
        article_number = args.article_numbers[0]
        output_path = args.output or f"ieee_paper_{article_number}.pdf"
        downloader.download_pdf(article_number, output_path)
    else:
        # 批量下载
        downloader.batch_download(args.article_numbers, args.output_dir)


if __name__ == "__main__":
    main()