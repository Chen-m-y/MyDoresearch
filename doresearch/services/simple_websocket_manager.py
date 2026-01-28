"""
简化的WebSocket管理器
集成到现有的task_processor.py中
"""
import asyncio
import json
import uuid
import threading
import websockets
from datetime import datetime
from typing import Dict, Optional
import time


class SimpleWebSocketManager:
    """简化的WebSocket管理器"""

    def __init__(self):
        self.connected_agents = {}  # agent_id -> websocket
        self.agent_info = {}  # agent_id -> agent_info
        self.task_results = {}  # task_id -> result
        self.server = None
        self.running = False

    async def handle_agent(self, websocket, path):
        """处理Agent连接"""
        agent_id = None
        try:
            # 等待注册消息
            message = await websocket.recv()
            data = json.loads(message)

            if data.get('type') == 'register':
                agent_info = data.get('agent_info', {})
                agent_id = agent_info.get('agent_id')

                if agent_id:
                    self.connected_agents[agent_id] = websocket
                    self.agent_info[agent_id] = agent_info

                    await websocket.send(json.dumps({
                        'type': 'registered',
                        'message': '注册成功'
                    }))

                    print(f"🤖 Agent已连接: {agent_info.get('name')} ({agent_id})")

                    # 监听消息
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self.handle_agent_message(agent_id, data)
                        except:
                            pass

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"❌ Agent连接错误: {e}")
        finally:
            if agent_id and agent_id in self.connected_agents:
                del self.connected_agents[agent_id]
                del self.agent_info[agent_id]
                print(f"🤖 Agent已断开: {agent_id}")

    async def handle_agent_message(self, agent_id: str, data: Dict):
        """处理Agent消息"""
        msg_type = data.get('type')

        if msg_type == 'task_result':
            task_id = data.get('task_id')
            self.task_results[task_id] = data
            print(f"📋 收到任务结果: {task_id}")
        elif msg_type == 'heartbeat':
            # 心跳响应
            await self.send_to_agent(agent_id, {'type': 'heartbeat_ack'})

    async def send_to_agent(self, agent_id: str, message: Dict):
        """发送消息给Agent"""
        if agent_id in self.connected_agents:
            try:
                websocket = self.connected_agents[agent_id]
                await websocket.send(json.dumps(message))
                return True
            except:
                # 连接断开，清理
                if agent_id in self.connected_agents:
                    del self.connected_agents[agent_id]
                if agent_id in self.agent_info:
                    del self.agent_info[agent_id]
        return False

    async def assign_task(self, task_data: Dict, capability: str = None) -> Optional[str]:
        """分配任务给Agent"""
        # 查找合适的Agent
        target_agent = None
        for agent_id, info in self.agent_info.items():
            if agent_id in self.connected_agents:
                if not capability or capability in info.get('capabilities', []):
                    target_agent = agent_id
                    break

        if not target_agent:
            return None

        task_id = str(uuid.uuid4())
        task_message = {
            'type': 'task',
            'task_id': task_id,
            'task_data': task_data
        }

        success = await self.send_to_agent(target_agent, task_message)
        return task_id if success else None

    def get_task_result(self, task_id: str, timeout: int = 300) -> Optional[Dict]:
        """等待任务结果"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if task_id in self.task_results:
                result = self.task_results.pop(task_id)
                return result
            time.sleep(0.5)
        return None

    def get_available_agents(self, capability: str = None) -> list:
        """获取可用Agent"""
        agents = []
        for agent_id, info in self.agent_info.items():
            if agent_id in self.connected_agents:
                if not capability or capability in info.get('capabilities', []):
                    agents.append(info)
        return agents

    def start_server(self, host='0.0.0.0', port=8765):
        """启动WebSocket服务器"""
        if self.running:
            return

        def run_server():
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 在新的事件循环中启动服务器
                self.server = loop.run_until_complete(
                    websockets.serve(self.handle_agent, host, port)
                )
                self.running = True

                print(f"🌐 WebSocket服务器已启动: ws://{host}:{port}")

                # 运行事件循环
                loop.run_forever()

            except Exception as e:
                print(f"❌ WebSocket服务器启动失败: {e}")
            finally:
                self.running = False
                loop.close()

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        return thread


# 全局WebSocket管理器实例
websocket_manager = SimpleWebSocketManager()