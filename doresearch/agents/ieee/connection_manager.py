"""
连接管理器模块
"""
import requests
import time
import threading
from typing import Optional, Callable

from .config import AgentConfig, ConnectionConfig
from .types import AgentStatus


class ConnectionManager:
    """连接管理器"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.session = requests.Session()
        self.running = False
        self.connected = False
        self.connection_start_time: Optional[float] = None
        self.last_connection_error: Optional[str] = None
        self.total_reconnections = 0
        self.last_heartbeat = time.time()
        
        # 事件处理器
        self.event_handler: Optional[Callable] = None
        
        # 健康检查线程
        self.health_check_thread: Optional[threading.Thread] = None
        
        # 主动心跳线程
        self.heartbeat_thread: Optional[threading.Thread] = None
    
    def set_event_handler(self, handler: Callable):
        """设置事件处理器"""
        self.event_handler = handler
    
    def register(self) -> bool:
        """注册到服务器"""
        try:
            print(f"📝 正在注册到服务器: {self.config.server_url}")
            
            response = self.session.post(
                f"{self.config.server_url}/api/agent/register",
                json={
                    'agent_id': self.config.agent_id,
                    'name': self.config.name,
                    'capabilities': self.config.capabilities
                },
                timeout=self.config.connection.request_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Agent注册成功: {self.config.name}")
                    return True
                else:
                    print(f"❌ Agent注册失败: {result.get('error')}")
                    return False
            else:
                print(f"❌ Agent注册失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 注册异常: {e}")
            return False
    
    def start_connection_loop(self):
        """启动连接循环"""
        self.running = True
        
        # 启动健康检查线程
        self._start_health_check()
        
        # 启动主动心跳线程
        self._start_heartbeat_sender()
        
        # 开始连接循环
        self._connection_loop()
    
    def _start_health_check(self):
        """启动健康检查线程"""
        def health_check():
            while self.running:
                try:
                    current_time = time.time()
                    
                    # 检查心跳超时
                    if (self.connected and 
                        current_time - self.last_heartbeat > self.config.connection.heartbeat_timeout):
                        print(f"💔 心跳超时 ({self.config.connection.heartbeat_timeout}秒)，断开连接")
                        self.connected = False
                    
                    time.sleep(self.config.connection.health_check_interval)
                    
                except Exception as e:
                    print(f"❌ 健康检查异常: {e}")
                    
        self.health_check_thread = threading.Thread(target=health_check, daemon=True)
        self.health_check_thread.start()
        print("💗 健康检查线程已启动")
    
    def _start_heartbeat_sender(self):
        """启动主动心跳发送线程"""
        def send_heartbeat():
            while self.running:
                try:
                    # 只有在已注册时才发送心跳
                    if self.connected:
                        success = self._send_heartbeat()
                        # 减少日志频率 - 只在失败时或每5次成功时记录一次
                        if not success:
                            print(f"💔 心跳发送失败")
                        elif hasattr(self, '_heartbeat_count'):
                            self._heartbeat_count += 1
                            if self._heartbeat_count % 5 == 0:  # 每5次记录一次
                                print(f"💓 心跳正常 (已发送{self._heartbeat_count}次)")
                        else:
                            self._heartbeat_count = 1
                    
                    # 等待心跳间隔
                    for i in range(self.config.connection.heartbeat_interval):
                        if not self.running:
                            break
                        time.sleep(1)
                    
                except Exception as e:
                    print(f"❌ 心跳发送异常: {e}")
                    
        self.heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
        self.heartbeat_thread.start()
        print("💓 主动心跳线程已启动")
    
    def _send_heartbeat(self) -> bool:
        """发送主动心跳"""
        try:
            response = self.session.post(
                f"{self.config.server_url}/api/agents/{self.config.agent_id}/heartbeat",
                timeout=self.config.connection.request_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
            else:
                print(f"❌ 心跳请求失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 发送心跳异常: {e}")
            return False
    
    def _connection_loop(self):
        """连接循环 - 主要的重连逻辑"""
        retry_count = 0
        
        while self.running and retry_count < self.config.connection.max_retries:
            try:
                # 尝试注册
                if self._attempt_registration():
                    # 注册成功，尝试连接SSE
                    if self._attempt_sse_connection():
                        # 连接成功，重置重试计数
                        retry_count = 0
                        self.total_reconnections += 1 if self.total_reconnections > 0 else 0
                        continue
                
                # 连接失败，准备重试
                retry_count += 1
                
                if retry_count >= self.config.connection.max_retries:
                    print(f"❌ 达到最大重试次数 ({self.config.connection.max_retries})，停止重连")
                    break
                
                # 计算重试延迟
                if self.config.connection.exponential_backoff:
                    delay = min(
                        self.config.connection.base_retry_delay * (2 ** (retry_count - 1)),
                        self.config.connection.max_retry_delay
                    )
                else:
                    delay = self.config.connection.base_retry_delay
                
                print(f"⏰ 第{retry_count}/{self.config.connection.max_retries}次重连失败，{delay}秒后重试...")
                
                # 分段等待，允许中途停止
                for i in range(int(delay)):
                    if not self.running:
                        return
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\n🛑 收到停止信号")
                break
            except Exception as e:
                print(f"❌ 连接循环异常: {e}")
                retry_count += 1
        
        print("🔌 连接循环结束")
    
    def _attempt_registration(self) -> bool:
        """尝试注册到服务器"""
        try:
            return self.register()
        except Exception as e:
            print(f"❌ 注册尝试失败: {e}")
            self.last_connection_error = str(e)
            return False
    
    def _attempt_sse_connection(self) -> bool:
        """尝试建立SSE连接"""
        try:
            print(f"🔌 尝试建立SSE连接...")
            sse_url = f"{self.config.server_url}/api/agent/{self.config.agent_id}/events"
            
            response = self.session.get(
                sse_url,
                stream=True,
                timeout=(10, None),  # 连接超时10秒，读取无超时
                headers={
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive'
                }
            )
            
            if response.status_code == 200:
                print("✅ SSE连接建立成功")
                self.connected = True
                self.connection_start_time = time.time()
                self.last_heartbeat = time.time()
                self.last_connection_error = None
                
                # 处理SSE流
                return self._handle_sse_stream(response)
            else:
                print(f"❌ SSE连接失败: HTTP {response.status_code}")
                if response.text:
                    print(f"   响应内容: {response.text[:200]}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ SSE连接错误: {e}")
            self.last_connection_error = "连接错误"
            return False
        except requests.exceptions.Timeout as e:
            print(f"❌ SSE连接超时: {e}")
            self.last_connection_error = "连接超时"
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ SSE请求异常: {e}")
            self.last_connection_error = str(e)
            return False
        except Exception as e:
            print(f"❌ SSE连接未预期异常: {e}")
            self.last_connection_error = str(e)
            return False
        finally:
            self.connected = False
    
    def _handle_sse_stream(self, response) -> bool:
        """处理SSE数据流"""
        try:
            for line in response.iter_lines():
                if not self.running:
                    print("🛑 收到停止信号，断开SSE连接")
                    break
                
                if line:
                    line = line.decode('utf-8')
                    
                    # 处理心跳
                    if line.startswith('data: ping'):
                        self.last_heartbeat = time.time()
                        continue
                    
                    # 处理实际事件
                    if line.startswith('data: '):
                        try:
                            import json
                            data = json.loads(line[6:])  # 去掉 'data: ' 前缀
                            
                            # 更新心跳时间
                            self.last_heartbeat = time.time()
                            
                            # 调用事件处理器
                            if self.event_handler:
                                self.event_handler(data)
                                
                        except json.JSONDecodeError:
                            print(f"⚠️ 无法解析SSE数据: {line}")
                        except Exception as e:
                            print(f"❌ 处理SSE事件异常: {e}")
            
            return False  # SSE流结束
            
        except Exception as e:
            print(f"❌ SSE流处理异常: {e}")
            return False
    
    def submit_result(self, task_id: str, result: dict, success: bool):
        """提交任务结果"""
        try:
            response = self.session.post(
                f"{self.config.server_url}/api/agent/task-result",
                json={
                    'task_id': task_id,
                    'success': success,
                    'result': result
                },
                timeout=self.config.connection.request_timeout
            )
            
            if response.status_code == 200:
                result_data = response.json()
                if result_data.get('success'):
                    print(f"✅ 任务结果提交成功: {task_id}")
                    return True
                else:
                    print(f"❌ 任务结果提交失败: {result_data.get('error')}")
                    return False
            else:
                print(f"❌ 提交结果HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 提交结果异常: {e}")
            return False
    
    def get_status_info(self) -> dict:
        """获取状态信息"""
        uptime = time.time() - self.connection_start_time if self.connection_start_time else 0
        
        return {
            'agent_id': self.config.agent_id,
            'connected': self.connected,
            'running': self.running,
            'uptime': uptime,
            'total_reconnections': self.total_reconnections,
            'last_heartbeat': self.last_heartbeat,
            'last_error': self.last_connection_error
        }
    
    def stop(self):
        """停止连接"""
        print("🛑 正在停止连接管理器...")
        self.running = False
        self.connected = False
        
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=1)
        
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=1)
        
        self.session.close()
        print("✅ 连接管理器已停止")