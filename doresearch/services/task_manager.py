"""
任务管理服务
"""
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from models.database import Database
from models.task_models import Task, TaskStep, TaskStatus, TaskType
from config import DATABASE_PATH


class TaskManager:
    def __init__(self):
        self.db = Database(DATABASE_PATH)

    def create_analysis_task(self, paper_id: int, priority: int = 5) -> Dict:
        """创建深度分析任务"""
        task_id = str(uuid.uuid4())
        conn = self.db.get_connection()
        try:
            c = conn.cursor()

            # 检查是否已有进行中的任务
            c.execute('''SELECT COUNT(*) as count
                         FROM tasks
                         WHERE paper_id = ? AND status IN (?, ?, ?, ?)''',
                      (paper_id, TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value,
                       TaskStatus.DOWNLOADING.value, TaskStatus.ANALYZING.value))

            result = c.fetchone()
            if result['count'] > 0:
                return {'success': False, 'error': '该论文已有进行中的分析任务'}

            # 创建任务
            c.execute('''INSERT INTO tasks
                             (id, paper_id, task_type, status, priority, metadata)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (task_id, paper_id, TaskType.DEEP_ANALYSIS.value, TaskStatus.PENDING.value,
                       priority, json.dumps({})))

            # 创建任务步骤
            steps = [
                'download_pdf',
                'analyze_with_deepseek',
                'save_results'
            ]
            for step in steps:
                c.execute('''INSERT INTO task_steps (task_id, step_name, status)
                             VALUES (?, ?, ?)''',
                          (task_id, step, TaskStatus.PENDING.value))

            conn.commit()
            return {
                'success': True, 
                'task_id': task_id, 
                'task_type': TaskType.DEEP_ANALYSIS.value,
                'paper_id': paper_id,
                'message': '深度分析任务创建成功'
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'task_id': None}
        finally:
            conn.close()

    def create_pdf_download_task(self, paper_id: int, article_number: str, priority: int = 5) -> Dict:
        """创建仅PDF下载任务"""
        task_id = str(uuid.uuid4())
        conn = self.db.get_connection()
        try:
            c = conn.cursor()

            # 检查是否已有进行中的PDF下载任务
            c.execute('''SELECT COUNT(*) as count
                         FROM tasks
                         WHERE paper_id = ? AND task_type IN (?, ?) AND status IN (?, ?)''',
                      (paper_id, TaskType.PDF_DOWNLOAD_ONLY.value, TaskType.PDF_DOWNLOAD.value,
                       TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value))

            result = c.fetchone()
            if result['count'] > 0:
                return {'success': False, 'error': '该论文已有进行中的PDF下载任务', 'task_id': None}

            # 创建任务
            metadata = {
                'article_number': article_number,
                'download_method': 'agent',
                'task_description': '仅下载PDF文件'
            }
            
            c.execute('''INSERT INTO tasks
                             (id, paper_id, task_type, status, priority, metadata)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (task_id, paper_id, TaskType.PDF_DOWNLOAD_ONLY.value, TaskStatus.PENDING.value,
                       priority, json.dumps(metadata)))

            # 创建任务步骤
            c.execute('''INSERT INTO task_steps (task_id, step_name, status)
                         VALUES (?, ?, ?)''',
                      (task_id, 'download_pdf', TaskStatus.PENDING.value))

            conn.commit()
            return {
                'success': True, 
                'task_id': task_id, 
                'task_type': TaskType.PDF_DOWNLOAD_ONLY.value,
                'paper_id': paper_id,
                'message': 'PDF下载任务创建成功'
            }

        except Exception as e:
            return {'success': False, 'error': str(e), 'task_id': None}
        finally:
            conn.close()

    def create_full_analysis_task(self, paper_id: int, priority: int = 5) -> Dict:
        """创建完整分析任务（下载PDF + AI分析）"""
        task_id = str(uuid.uuid4())
        conn = self.db.get_connection()
        try:
            c = conn.cursor()

            # 检查是否已有进行中的分析任务
            c.execute('''SELECT COUNT(*) as count
                         FROM tasks
                         WHERE paper_id = ? AND task_type IN (?, ?) AND status IN (?, ?, ?, ?)''',
                      (paper_id, TaskType.FULL_ANALYSIS.value, TaskType.DEEP_ANALYSIS.value,
                       TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value,
                       TaskStatus.DOWNLOADING.value, TaskStatus.ANALYZING.value))

            result = c.fetchone()
            if result['count'] > 0:
                return {'success': False, 'error': '该论文已有进行中的分析任务', 'task_id': None}

            # 创建任务
            metadata = {
                'task_description': '完整分析（下载PDF + AI深度分析）',
                'includes_download': True,
                'includes_analysis': True
            }
            
            c.execute('''INSERT INTO tasks
                             (id, paper_id, task_type, status, priority, metadata)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (task_id, paper_id, TaskType.FULL_ANALYSIS.value, TaskStatus.PENDING.value,
                       priority, json.dumps(metadata)))

            # 创建任务步骤
            steps = [
                ('download_pdf', '下载PDF文件'),
                ('analyze_with_ai', '使用AI进行深度分析'),
                ('save_results', '保存分析结果')
            ]
            
            for step_name, step_desc in steps:
                c.execute('''INSERT INTO task_steps (task_id, step_name, status, result)
                             VALUES (?, ?, ?, ?)''',
                          (task_id, step_name, TaskStatus.PENDING.value, step_desc))

            conn.commit()
            return {
                'success': True, 
                'task_id': task_id, 
                'task_type': TaskType.FULL_ANALYSIS.value,
                'paper_id': paper_id,
                'message': '完整分析任务创建成功'
            }

        except Exception as e:
            return {'success': False, 'error': str(e), 'task_id': None}
        finally:
            conn.close()

    def get_pending_tasks(self) -> List[Dict]:
        """获取待处理任务"""
        conn = self.db.get_connection()
        try:
            c = conn.cursor()
            c.execute('''SELECT t.*, p.title, p.ieee_article_number, p.doi, p.url
                         FROM tasks t
                                  JOIN papers p ON t.paper_id = p.id
                         WHERE t.status = ?
                         ORDER BY t.priority DESC, t.created_at ASC''',
                      (TaskStatus.PENDING.value,))
            return [dict(row) for row in c.fetchall()]
        finally:
            conn.close()

    def update_task_status(self, task_id: str, status: str, error_message: str = None,
                           progress: int = None, result: str = None) -> Dict:
        """更新任务状态"""
        conn = self.db.get_connection()
        try:
            c = conn.cursor()

            update_fields = ['status = ?']
            params = [status]

            if error_message:
                update_fields.append('error_message = ?')
                params.append(error_message)

            if progress is not None:
                update_fields.append('progress = ?')
                params.append(progress)

            if result:
                update_fields.append('result = ?')
                params.append(result)

            if status == TaskStatus.IN_PROGRESS.value:
                update_fields.append('started_at = ?')
                params.append(datetime.now().isoformat())
            elif status == TaskStatus.COMPLETED.value:
                update_fields.append('completed_at = ?')
                params.append(datetime.now().isoformat())

            params.append(task_id)

            c.execute(f'UPDATE tasks SET {", ".join(update_fields)} WHERE id = ?', params)
            conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def update_task_step(self, task_id: str, step_name: str, status: str,
                         error_message: str = None, result: str = None) -> Dict:
        """更新任务步骤状态"""
        conn = self.db.get_connection()
        try:
            c = conn.cursor()

            update_fields = ['status = ?']
            params = [status]

            if error_message:
                update_fields.append('error_message = ?')
                params.append(error_message)

            if result:
                update_fields.append('result = ?')
                params.append(result)

            if status == TaskStatus.IN_PROGRESS.value:
                update_fields.append('started_at = ?')
                params.append(datetime.now().isoformat())
            elif status == TaskStatus.COMPLETED.value:
                update_fields.append('completed_at = ?')
                params.append(datetime.now().isoformat())

            params.extend([task_id, step_name])

            c.execute(f'''UPDATE task_steps 
                         SET {", ".join(update_fields)} 
                         WHERE task_id = ? AND step_name = ?''', params)
            conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_all_tasks(self, status: str = None, limit: int = 100, task_type: str = None, include_steps: bool = True) -> List[Dict]:
        """获取所有任务"""
        conn = self.db.get_connection()
        try:
            c = conn.cursor()

            # 构建WHERE条件
            conditions = []
            params = []
            
            if status:
                conditions.append('t.status = ?')
                params.append(status)
            
            if task_type:
                conditions.append('t.task_type = ?')
                params.append(task_type)
            
            where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
            
            query = f'''SELECT t.*, p.title, p.ieee_article_number
                        FROM tasks t
                                 JOIN papers p ON t.paper_id = p.id
                        {where_clause}
                        ORDER BY t.created_at DESC LIMIT ?'''
            
            params.append(limit)
            c.execute(query, params)

            tasks = []
            for row in c.fetchall():
                task = dict(row)
                
                # 解析元数据
                if task.get('metadata'):
                    try:
                        import json
                        task['metadata'] = json.loads(task['metadata'])
                    except (json.JSONDecodeError, TypeError):
                        task['metadata'] = {}
                else:
                    task['metadata'] = {}
                
                # 添加任务类型描述
                task['task_type_desc'] = self._get_task_type_description(task['task_type'])
                
                # 添加任务类型图标（用于UI显示）
                task['task_type_icon'] = self._get_task_type_icon(task['task_type'])
                
                # 根据include_steps参数决定是否添加步骤信息
                if include_steps:
                    task['steps'] = self.get_task_steps(task['id'])
                else:
                    task['steps_count'] = len(self.get_task_steps(task['id']))
                
                tasks.append(task)
            
            return tasks
        finally:
            conn.close()
    
    def _get_task_type_description(self, task_type: str) -> str:
        """获取任务类型描述"""
        descriptions = {
            'pdf_download_only': '仅下载PDF',
            'full_analysis': '完整分析（下载+AI分析）',
            'deep_analysis': '深度分析',
            'pdf_download': 'PDF下载',
            'translation': '翻译任务'
        }
        return descriptions.get(task_type, task_type)
    
    def _get_task_type_icon(self, task_type: str) -> str:
        """获取任务类型图标"""
        icons = {
            'pdf_download_only': '📥',
            'full_analysis': '🔍',
            'deep_analysis': '🧠',
            'pdf_download': '📄',
            'translation': '🌐'
        }
        return icons.get(task_type, '📋')

    def get_task_steps(self, task_id: str) -> List[Dict]:
        """获取任务步骤"""
        conn = self.db.get_connection()
        try:
            c = conn.cursor()
            c.execute('SELECT * FROM task_steps WHERE task_id = ? ORDER BY id', (task_id,))
            return [dict(row) for row in c.fetchall()]
        finally:
            conn.close()

    def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """根据ID获取任务"""
        conn = self.db.get_connection()
        try:
            c = conn.cursor()
            c.execute('''SELECT t.*, p.title, p.ieee_article_number, p.analysis_result
                         FROM tasks t
                                  JOIN papers p ON t.paper_id = p.id
                         WHERE t.id = ?''', (task_id,))
            task = c.fetchone()

            if task:
                task_dict = dict(task)
                
                # 解析元数据
                if task_dict.get('metadata'):
                    try:
                        import json
                        task_dict['metadata'] = json.loads(task_dict['metadata'])
                    except (json.JSONDecodeError, TypeError):
                        task_dict['metadata'] = {}
                else:
                    task_dict['metadata'] = {}
                
                # 添加任务类型描述和图标
                task_dict['task_type_desc'] = self._get_task_type_description(task_dict['task_type'])
                task_dict['task_type_icon'] = self._get_task_type_icon(task_dict['task_type'])
                
                # 获取任务步骤
                task_dict['steps'] = self.get_task_steps(task_id)
                
                return task_dict

            return None
        finally:
            conn.close()

    def cancel_task(self, task_id: str) -> Dict:
        """取消任务"""
        return self.update_task_status(task_id, TaskStatus.CANCELLED.value)
