"""
任务处理器模块
"""
import os
import base64
import tempfile
import time
from typing import Dict, Any, Optional

from ieee_downloader import IEEEDownloader
from .types import TaskData, TaskResult


class TaskProcessor:
    """任务处理器"""
    
    def __init__(self):
        self.downloader = IEEEDownloader()
    
    def process_task(self, task_data: TaskData) -> TaskResult:
        """处理任务"""
        start_time = time.time()
        
        try:
            print(f"🔄 开始处理任务: {task_data.task_id}")
            
            if task_data.task_type == 'ieee_download':
                result = self._download_ieee_paper(task_data.data)
                success = result.get('success', False)
            else:
                result = {'error': f'未知任务类型: {task_data.task_type}'}
                success = False
            
            processing_time = time.time() - start_time
            
            return TaskResult(
                task_id=task_data.task_id,
                success=success,
                result=result,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ 任务处理失败: {e}")
            
            return TaskResult(
                task_id=task_data.task_id,
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    def _download_ieee_paper(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """下载IEEE论文"""
        article_number = task_data.get('article_number')
        if not article_number:
            return {'success': False, 'error': '缺少article_number参数'}
        
        print(f"📥 开始下载IEEE论文: {article_number}")
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            try:
                success = self.downloader.download_pdf(article_number, temp_filename)
                
                if success and os.path.exists(temp_filename):
                    with open(temp_filename, 'rb') as f:
                        pdf_content = f.read()
                    
                    if len(pdf_content) > 0:
                        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                        file_size = len(pdf_content)
                        
                        print(f"✅ 下载成功: {file_size / 1024 / 1024:.2f}MB")
                        
                        return {
                            'success': True,
                            'pdf_content': pdf_base64,
                            'file_size': file_size,
                            'article_number': article_number
                        }
                    else:
                        return {'success': False, 'error': '下载的文件为空'}
                else:
                    return {'success': False, 'error': 'PDF下载失败，可能需要订阅或付费访问'}
            
            finally:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
        
        except Exception as e:
            return {'success': False, 'error': f'下载异常: {str(e)}'}
    
    def get_supported_task_types(self) -> list:
        """获取支持的任务类型"""
        return ['ieee_download']