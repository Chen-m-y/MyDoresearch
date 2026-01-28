"""
SSE任务管理器 - 全局单例
处理Agent注册、任务分发和结果收集
统一替换所有其他SSE实现
"""
import sqlite3
import json
import uuid
import time
import threading
import os
from typing import Dict, List, Optional, Any
from datetime import datetime


class SSETaskManager:
    """SSE任务管理器 - 单例模式"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: str = "data/sse_tasks.db"):
        # 防止重复初始化
        if hasattr(self, '_initialized'):
            return

        self.db_path = db_path
        self.init_db()

        # Agent管理
        self.active_agents: Dict[str, Dict] = {}

        # 任务队列
        self.pending_tasks: Dict[str, List[Dict]] = {}

        # 任务结果缓存
        self.task_results: Dict[str, Dict] = {}

        # 线程锁
        self.lock = threading.Lock()

        # 启动清理线程
        self._start_cleanup_thread()

        self._initialized = True
        print("✅ SSE任务管理器已初始化")

    def init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 任务表
        c.execute('''CREATE TABLE IF NOT EXISTS sse_tasks
                     (
                         id TEXT PRIMARY KEY,
                         agent_id TEXT,
                         task_type TEXT,
                         task_data TEXT,
                         status TEXT DEFAULT 'pending',
                         result TEXT,
                         created_at REAL,
                         assigned_at REAL,
                         completed_at REAL
                     )''')

        # Agent表
        c.execute('''CREATE TABLE IF NOT EXISTS sse_agents
                     (
                         agent_id TEXT PRIMARY KEY,
                         name TEXT,
                         capabilities TEXT,
                         last_seen REAL,
                         status TEXT DEFAULT 'active'
                     )''')

        conn.commit()
        conn.close()

    def register_agent(self, agent_id: str, name: str, capabilities: List[str]) -> bool:
        """注册Agent"""
        with self.lock:
            self.active_agents[agent_id] = {
                'name': name,
                'capabilities': capabilities,
                'last_seen': time.time(),
                'registered_at': time.time()
            }

        # 保存到数据库
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO sse_agents 
                     (agent_id, name, capabilities, last_seen, status) 
                     VALUES (?, ?, ?, ?, ?)''',
                  (agent_id, name, json.dumps(capabilities), time.time(), 'active'))
        conn.commit()
        conn.close()

        print(f"✅ Agent注册成功: {name} ({agent_id})")
        return True

    def update_heartbeat(self, agent_id: str) -> bool:
        """更新Agent心跳"""
        with self.lock:
            if agent_id in self.active_agents:
                self.active_agents[agent_id]['last_seen'] = time.time()
                return True
        return False
    
    def remove_agent(self, agent_id: str) -> bool:
        """手动移除Agent（当连接断开时）"""
        with self.lock:
            if agent_id in self.active_agents:
                del self.active_agents[agent_id]
                
                # 清理相关的待处理任务
                if agent_id in self.pending_tasks:
                    del self.pending_tasks[agent_id]
                
                print(f"🧹 Agent已断线并清理: {agent_id}")
                return True
        return False

    # 兼容旧接口
    def update_agent_heartbeat(self, agent_id: str) -> bool:
        """更新Agent心跳 - 兼容旧接口"""
        return self.update_heartbeat(agent_id)

    def submit_task(self, task_type: str, task_data: Dict, capability_required: str = None) -> Optional[str]:
        """提交任务"""
        # 选择Agent
        agent_id = self._find_available_agent(capability_required)
        if not agent_id:
            print(f"❌ 没有可用的Agent处理任务: {task_type}")
            return None

        task_id = str(uuid.uuid4())

        # 保存到数据库
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO sse_tasks
                     (id, agent_id, task_type, task_data, created_at)
                     VALUES (?, ?, ?, ?, ?)''',
                  (task_id, agent_id, task_type, json.dumps(task_data), time.time()))
        conn.commit()
        conn.close()

        # 添加到待发送队列
        with self.lock:
            if agent_id not in self.pending_tasks:
                self.pending_tasks[agent_id] = []

            self.pending_tasks[agent_id].append({
                'task_id': task_id,
                'task_type': task_type,
                'task_data': task_data,
                'created_at': time.time()
            })

        print(f"📋 任务已提交: {task_id} -> {agent_id} ({task_type})")
        return task_id

    def get_pending_tasks(self, agent_id: str) -> List[Dict]:
        """获取Agent的待处理任务"""
        with self.lock:
            if agent_id in self.pending_tasks:
                tasks = self.pending_tasks[agent_id].copy()
                self.pending_tasks[agent_id] = []
                return tasks
        return []

    def submit_result(self, task_id: str, result: Any, success: bool = True) -> bool:
        """提交任务结果"""
        status = "completed" if success else "failed"

        # 保存结果到内存
        with self.lock:
            self.task_results[task_id] = {
                'success': success,
                'result': result,
                'completed_at': time.time()
            }

        # 保存到数据库
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''UPDATE sse_tasks
                     SET status = ?, result = ?, completed_at = ?
                     WHERE id = ?''',
                  (status, json.dumps(result), time.time(), task_id))
        conn.commit()
        conn.close()

        print(f"✅ 任务结果已提交: {task_id}")
        return True

    # 兼容旧接口
    def update_task_result(self, task_id: str, result: Any, success: bool = True) -> bool:
        """更新任务结果 - 兼容旧接口"""
        return self.submit_result(task_id, result, success)

    def get_task_result(self, task_id: str, timeout: int = 300) -> Optional[Dict]:
        """等待并获取任务结果"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self.lock:
                if task_id in self.task_results:
                    result = self.task_results.pop(task_id)
                    return result
            time.sleep(1)

        print(f"⏰ 任务超时: {task_id}")
        return None

    def get_active_agents(self) -> List[Dict]:
        """获取活跃的Agent列表"""
        with self.lock:
            current_time = time.time()
            active = []

            for agent_id, agent_data in self.active_agents.items():
                # 使用较短的心跳超时时间（2分钟）来快速检测掉线
                if current_time - agent_data['last_seen'] <= 120:
                    active.append({
                        'agent_id': agent_id,
                        'name': agent_data['name'],
                        'capabilities': agent_data['capabilities'],
                        'last_seen': agent_data['last_seen'],
                        'last_seen_ago': current_time - agent_data['last_seen']
                    })

            return active

    def _find_available_agent(self, capability_required: str = None) -> Optional[str]:
        """找到可用的Agent"""
        with self.lock:
            current_time = time.time()

            for agent_id, agent_data in self.active_agents.items():
                # 检查是否在线
                if current_time - agent_data['last_seen'] > 300:
                    continue

                # 检查能力
                if capability_required:
                    if capability_required not in agent_data['capabilities']:
                        continue

                return agent_id

        return None

    # 兼容旧接口
    def find_available_agent(self, capability_required: str = None) -> Optional[str]:
        """找到可用的Agent - 兼容旧接口"""
        return self._find_available_agent(capability_required)

    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup_expired():
            while True:
                try:
                    current_time = time.time()
                    expired_agents = []

                    with self.lock:
                        for agent_id, agent_data in list(self.active_agents.items()):
                            # 清理3分钟没有心跳的Agent（更快检测掉线）
                            if current_time - agent_data['last_seen'] > 180:
                                expired_agents.append(agent_id)
                                del self.active_agents[agent_id]

                                # 清理相关的待处理任务
                                if agent_id in self.pending_tasks:
                                    del self.pending_tasks[agent_id]

                    if expired_agents:
                        print(f"🧹 清理过期Agent: {expired_agents}")

                    # 清理1小时前的任务结果
                    with self.lock:
                        expired_results = []
                        for task_id, result_data in list(self.task_results.items()):
                            if current_time - result_data['completed_at'] > 3600:
                                expired_results.append(task_id)
                                del self.task_results[task_id]

                        if expired_results:
                            print(f"🧹 清理过期任务结果: {len(expired_results)}个")

                except Exception as e:
                    print(f"❌ 清理线程异常: {e}")

                time.sleep(30)  # 每30秒清理一次，更快检测掉线

        thread = threading.Thread(target=cleanup_expired, daemon=True)
        thread.start()

    def get_status(self) -> Dict:
        """获取系统状态"""
        agents = self.get_active_agents()
        ieee_agents = [a for a in agents if 'ieee_download' in a['capabilities']]

        with self.lock:
            pending_count = sum(len(tasks) for tasks in self.pending_tasks.values())
            result_count = len(self.task_results)

        return {
            'total_agents': len(agents),
            'ieee_agents': len(ieee_agents),
            'pending_tasks': pending_count,
            'cached_results': result_count,
            'agents': agents
        }


# 全局单例实例 - 统一入口
sse_manager = SSETaskManager()

# 兼容旧的导入方式
sse_task_manager = sse_manager