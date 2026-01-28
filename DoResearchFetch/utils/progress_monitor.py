"""
进度监控和任务状态管理
支持实时任务进度查询和WebSocket推送
"""

import time
import uuid
import json
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待开始
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class TaskProgress:
    """任务进度数据结构"""
    task_id: str
    status: TaskStatus
    source: str
    total_items: int
    processed_items: int
    success_items: int
    failed_items: int
    start_time: float
    end_time: Optional[float] = None
    current_operation: str = ""
    error_message: str = ""
    results: Optional[Dict[str, Any]] = None
    
    @property
    def progress_percent(self) -> float:
        """进度百分比"""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100
    
    @property
    def elapsed_time(self) -> float:
        """已用时间（秒）"""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def estimated_remaining(self) -> float:
        """预估剩余时间（秒）"""
        if self.processed_items == 0:
            return 0.0
        
        rate = self.processed_items / self.elapsed_time
        remaining_items = self.total_items - self.processed_items
        
        if rate <= 0:
            return 0.0
        
        return remaining_items / rate
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['status'] = self.status.value
        data['progress_percent'] = round(self.progress_percent, 2)
        data['elapsed_time'] = round(self.elapsed_time, 2)
        data['estimated_remaining'] = round(self.estimated_remaining, 2)
        data['start_time_iso'] = datetime.fromtimestamp(self.start_time).isoformat()
        
        if self.end_time:
            data['end_time_iso'] = datetime.fromtimestamp(self.end_time).isoformat()
        
        return data


class ProgressManager:
    """进度管理器"""
    
    def __init__(self):
        self._tasks: Dict[str, TaskProgress] = {}
        self._lock = threading.RLock()
        self._max_history = 100  # 最多保留100个已完成任务
    
    def create_task(self, source: str, total_items: int, operation: str = "") -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())[:8]
        
        with self._lock:
            task = TaskProgress(
                task_id=task_id,
                status=TaskStatus.PENDING,
                source=source,
                total_items=total_items,
                processed_items=0,
                success_items=0,
                failed_items=0,
                start_time=time.time(),
                current_operation=operation
            )
            self._tasks[task_id] = task
        
        return task_id
    
    def start_task(self, task_id: str, operation: str = ""):
        """开始任务"""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = TaskStatus.RUNNING
                task.current_operation = operation
                task.start_time = time.time()
    
    def update_progress(self, task_id: str, processed: int = None, success: int = None, 
                       failed: int = None, operation: str = None):
        """更新任务进度"""
        with self._lock:
            if task_id not in self._tasks:
                return
            
            task = self._tasks[task_id]
            
            if processed is not None:
                task.processed_items = processed
            if success is not None:
                task.success_items = success
            if failed is not None:
                task.failed_items = failed
            if operation is not None:
                task.current_operation = operation
    
    def increment_progress(self, task_id: str, success: bool = True, operation: str = None):
        """递增任务进度"""
        with self._lock:
            if task_id not in self._tasks:
                return
            
            task = self._tasks[task_id]
            task.processed_items += 1
            
            if success:
                task.success_items += 1
            else:
                task.failed_items += 1
            
            if operation is not None:
                task.current_operation = operation
    
    def complete_task(self, task_id: str, results: Dict[str, Any] = None):
        """完成任务"""
        with self._lock:
            if task_id not in self._tasks:
                return
            
            task = self._tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.end_time = time.time()
            task.current_operation = "Completed"
            
            if results:
                task.results = results
            
            # 清理旧任务历史
            self._cleanup_old_tasks()
    
    def fail_task(self, task_id: str, error_message: str):
        """标记任务失败"""
        with self._lock:
            if task_id not in self._tasks:
                return
            
            task = self._tasks[task_id]
            task.status = TaskStatus.FAILED
            task.end_time = time.time()
            task.error_message = error_message
            task.current_operation = "Failed"
    
    def cancel_task(self, task_id: str):
        """取消任务"""
        with self._lock:
            if task_id not in self._tasks:
                return
            
            task = self._tasks[task_id]
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
                task.end_time = time.time()
                task.current_operation = "Cancelled"
    
    def get_task(self, task_id: str) -> Optional[TaskProgress]:
        """获取任务信息"""
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[TaskProgress]:
        """获取所有任务"""
        with self._lock:
            return list(self._tasks.values())
    
    def get_running_tasks(self) -> List[TaskProgress]:
        """获取正在运行的任务"""
        with self._lock:
            return [task for task in self._tasks.values() if task.status == TaskStatus.RUNNING]
    
    def get_task_stats(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        with self._lock:
            total = len(self._tasks)
            running = len([t for t in self._tasks.values() if t.status == TaskStatus.RUNNING])
            completed = len([t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED])
            failed = len([t for t in self._tasks.values() if t.status == TaskStatus.FAILED])
            
            return {
                'total_tasks': total,
                'running_tasks': running,
                'completed_tasks': completed,
                'failed_tasks': failed,
                'success_rate': round((completed / total * 100) if total > 0 else 0, 2)
            }
    
    def _cleanup_old_tasks(self):
        """清理旧的已完成任务"""
        completed_tasks = [
            (task_id, task) for task_id, task in self._tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        
        if len(completed_tasks) > self._max_history:
            # 按结束时间排序，保留最新的
            completed_tasks.sort(key=lambda x: x[1].end_time or 0)
            
            # 删除最旧的任务
            for task_id, _ in completed_tasks[:-self._max_history]:
                del self._tasks[task_id]


# 全局进度管理器实例
progress_manager = ProgressManager()


class ProgressTracker:
    """进度追踪器上下文管理器"""
    
    def __init__(self, source: str, total_items: int, operation: str = ""):
        self.source = source
        self.total_items = total_items
        self.operation = operation
        self.task_id: Optional[str] = None
    
    def __enter__(self):
        self.task_id = progress_manager.create_task(self.source, self.total_items, self.operation)
        progress_manager.start_task(self.task_id, self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # 发生异常，标记任务失败
            error_msg = f"{exc_type.__name__}: {exc_val}"
            progress_manager.fail_task(self.task_id, error_msg)
        else:
            # 正常完成
            progress_manager.complete_task(self.task_id)
    
    def update(self, processed: int = None, success: int = None, failed: int = None, operation: str = None):
        """更新进度"""
        if self.task_id:
            progress_manager.update_progress(self.task_id, processed, success, failed, operation)
    
    def increment(self, success: bool = True, operation: str = None):
        """递增进度"""
        if self.task_id:
            progress_manager.increment_progress(self.task_id, success, operation)
    
    def set_results(self, results: Dict[str, Any]):
        """设置结果数据"""
        if self.task_id:
            task = progress_manager.get_task(self.task_id)
            if task:
                task.results = results


# 工具函数
def create_progress_tracker(source: str, total_items: int, operation: str = "") -> ProgressTracker:
    """创建进度追踪器"""
    return ProgressTracker(source, total_items, operation)