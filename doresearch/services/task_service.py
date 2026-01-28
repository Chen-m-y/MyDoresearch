"""
任务服务 - 处理IEEE论文下载任务
与SSE系统集成 - 使用统一的SSE管理器
"""
import os
import time
import base64
import threading
from typing import Dict, Optional

# 使用统一的SSE管理器
from services.sse_manager import sse_manager


class TaskService:
    """任务服务类"""

    def __init__(self, pdf_dir: str = "data/pdfs"):
        self.pdf_dir = pdf_dir
        self.running = False

        # 确保目录存在
        os.makedirs(pdf_dir, exist_ok=True)

        print("✅ 任务服务已初始化")

    def start(self):
        """启动任务服务"""
        if not self.running:
            self.running = True
            print("📋 任务服务已启动")

    def stop(self):
        """停止任务服务"""
        self.running = False
        print("📋 任务服务已停止")

    def download_ieee_paper(self, article_number: str, timeout: int = 300) -> Dict:
        """下载IEEE论文"""
        if not article_number:
            return {'success': False, 'error': '缺少文章编号'}

        print(f"📥 开始下载IEEE论文: {article_number}")

        # 检查是否有可用的下载Agent
        agents = sse_manager.get_active_agents()
        ieee_agents = [a for a in agents if 'ieee_download' in a['capabilities']]

        if not ieee_agents:
            return {
                'success': False,
                'error': '没有可用的IEEE下载Agent，请启动ieee_agent.py'
            }

        print(f"🔍 找到 {len(ieee_agents)} 个可用的IEEE下载Agent")

        # 提交下载任务
        task_id = sse_manager.submit_task(
            'ieee_download',
            {'article_number': article_number},
            'ieee_download'
        )

        if not task_id:
            return {'success': False, 'error': '任务提交失败'}

        print(f"📋 下载任务已提交: {task_id}")

        # 等待下载结果
        result = sse_manager.get_task_result(task_id, timeout)

        if not result:
            return {'success': False, 'error': '下载超时'}

        if not result.get('success'):
            error_msg = result.get('result', {}).get('error', '下载失败')
            return {'success': False, 'error': error_msg}

        # 解码PDF内容
        pdf_base64 = result.get('result', {}).get('pdf_content')
        if not pdf_base64:
            return {'success': False, 'error': '没有收到PDF内容'}

        try:
            pdf_data = base64.b64decode(pdf_base64)
            pdf_path = self._save_pdf(article_number, pdf_data)

            print(f"✅ PDF下载成功: {len(pdf_data) / 1024 / 1024:.2f}MB")

            return {
                'success': True,
                'pdf_path': pdf_path,
                'file_size': len(pdf_data),
                'article_number': article_number
            }

        except Exception as e:
            return {'success': False, 'error': f'PDF保存失败: {str(e)}'}

    def _save_pdf(self, article_number: str, pdf_data: bytes) -> str:
        """保存PDF文件"""
        filename = f"ieee_{article_number}_{int(time.time())}.pdf"
        pdf_path = os.path.join(self.pdf_dir, filename)

        with open(pdf_path, 'wb') as f:
            f.write(pdf_data)

        print(f"💾 PDF已保存: {pdf_path}")
        return pdf_path

    def get_agent_status(self) -> Dict:
        """获取Agent状态"""
        return sse_manager.get_status()

    def create_download_task(self, paper_id: int, article_number: str) -> Dict:
        """创建下载任务（异步）"""
        def download_async():
            try:
                result = self.download_ieee_paper(article_number)

                if result['success']:
                    # 这里可以更新数据库，记录下载成功
                    print(f"✅ 论文 {paper_id} 下载完成: {result['pdf_path']}")
                    # TODO: 更新数据库中的pdf_path字段
                else:
                    print(f"❌ 论文 {paper_id} 下载失败: {result['error']}")
                    # TODO: 更新数据库中的错误信息

            except Exception as e:
                print(f"❌ 异步下载任务异常: {e}")

        # 在后台线程中执行下载
        thread = threading.Thread(target=download_async, daemon=True)
        thread.start()

        return {
            'success': True,
            'message': f'下载任务已启动，论文ID: {paper_id}',
            'paper_id': paper_id,
            'article_number': article_number
        }

    def test_download(self, article_number: str, timeout: int = 60) -> Dict:
        """测试下载功能（用于API测试）"""
        try:
            result = self.download_ieee_paper(article_number, timeout)

            if result['success']:
                # 不返回完整PDF内容，只返回基本信息
                return {
                    'success': True,
                    'task_id': f"test_{int(time.time())}",
                    'article_number': article_number,
                    'file_size_mb': round(result['file_size'] / 1024 / 1024, 2),
                    'message': '下载测试成功'
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'article_number': article_number
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'article_number': article_number
            }


# 全局任务服务实例
task_service = TaskService()