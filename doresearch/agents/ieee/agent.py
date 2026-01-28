"""
IEEE Agent主类
"""
import uuid
import time
import threading
from typing import Dict, Any

from .config import AgentConfig, ConnectionConfig
from .connection_manager import ConnectionManager
from .task_processor import TaskProcessor
from .types import TaskData, AgentStatus


class IEEEAgent:
    """基于SSE的IEEE下载Agent"""
    
    def __init__(self, server_url: str = "http://localhost:5000", agent_id: str = None):
        # 生成Agent ID
        if agent_id is None:
            agent_id = f"ieee-agent-{uuid.uuid4().hex[:8]}"
        
        # 创建配置
        self.config = AgentConfig(
            server_url=server_url.rstrip('/'),
            agent_id=agent_id
        )
        
        # 初始化组件
        self.connection_manager = ConnectionManager(self.config)
        self.task_processor = TaskProcessor()
        
        # 设置事件处理器 
        self.connection_manager.set_event_handler(self.handle_event)
        
        # 状态管理
        self.status = AgentStatus.OFFLINE
        self.running = False
        
        print(f"🤖 IEEE Agent初始化完成: {self.config.agent_id}")
        print(f"🔧 重连配置: 最大重试{self.config.connection.max_retries}次, 基础延迟{self.config.connection.base_retry_delay}秒")
    
    def start(self):
        """启动Agent"""
        if self.running:
            print("⚠️ Agent已经在运行中")
            return
        
        print(f"🚀 启动Agent: {self.config.name}")
        self.running = True
        self.status = AgentStatus.CONNECTING
        
        # 在新线程中启动连接循环
        connection_thread = threading.Thread(
            target=self.connection_manager.start_connection_loop,
            daemon=True
        )
        connection_thread.start()
        
        print("✅ Agent启动完成")
        
        # 主线程保持运行
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号")
            self.stop()
    
    def handle_event(self, data: Dict[str, Any]):
        """处理SSE事件"""
        try:
            event_type = data.get('type')
            
            if event_type == 'ping':
                # 心跳事件，无需处理
                pass
            elif event_type == 'task':
                # 任务事件
                self._handle_task_event(data)
            elif event_type == 'status':
                # 状态查询事件
                self._handle_status_event(data)
            else:
                print(f"⚠️ 收到未知事件类型: {event_type}")
                
        except Exception as e:
            print(f"❌ 处理事件异常: {e}")
    
    def _handle_task_event(self, data: Dict[str, Any]):
        """处理任务事件"""
        try:
            task_id = data.get('task_id')
            task_type = data.get('task_type')
            task_data = data.get('task_data', {})
            
            if not task_id or not task_type:
                print("⚠️ 任务事件缺少必要参数")
                return
            
            print(f"📋 收到任务: {task_id} (类型: {task_type})")
            
            # 创建任务数据
            task = TaskData(
                task_id=task_id,
                task_type=task_type,
                data=task_data
            )
            
            # 在新线程中处理任务
            task_thread = threading.Thread(
                target=self._process_task_async,
                args=(task,),
                daemon=True
            )
            task_thread.start()
            
        except Exception as e:
            print(f"❌ 处理任务事件异常: {e}")
    
    def _process_task_async(self, task: TaskData):
        """异步处理任务"""
        try:
            # 处理任务
            result = self.task_processor.process_task(task)
            
            # 提交结果
            self.connection_manager.submit_result(
                result.task_id,
                result.result or {'error': result.error},
                result.success
            )
            
        except Exception as e:
            print(f"❌ 异步任务处理异常: {e}")
            # 提交错误结果
            self.connection_manager.submit_result(
                task.task_id,
                {'error': str(e)},
                False
            )
    
    def _handle_status_event(self, data: Dict[str, Any]):
        """处理状态查询事件"""
        try:
            # 获取状态信息
            status_info = self.get_status_info()
            
            # 这里可以向服务器报告状态
            print(f"📊 状态查询: {status_info}")
            
        except Exception as e:
            print(f"❌ 处理状态事件异常: {e}")
    
    def get_status_info(self) -> Dict[str, Any]:
        """获取状态信息"""
        connection_status = self.connection_manager.get_status_info()
        
        return {
            'agent_id': self.config.agent_id,
            'name': self.config.name,
            'capabilities': self.config.capabilities,
            'status': self.status.value,
            'running': self.running,
            'supported_tasks': self.task_processor.get_supported_task_types(),
            **connection_status
        }
    
    def stop(self):
        """停止Agent"""
        print("🛑 正在停止Agent...")
        self.running = False
        self.status = AgentStatus.OFFLINE
        
        # 停止连接管理器
        self.connection_manager.stop()
        
        print("✅ Agent已停止")