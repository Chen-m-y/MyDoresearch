"""
Agent管理服务
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from models.database import Database
from models.agent_models import Agent, AgentStatus
from config import DATABASE_PATH, AGENT_HEARTBEAT_TIMEOUT


class AgentManager:
    def __init__(self):
        self.db = Database(DATABASE_PATH)

    def register_agent(self, agent_id: str, name: str, agent_type: str,
                       capabilities: List[str], endpoint: str, metadata: Dict = None) -> Dict:
        """注册Agent"""
        conn = self.db.get_connection()
        try:
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO agents 
                        (id, name, type, capabilities, endpoint, status, last_heartbeat, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (agent_id, name, agent_type, json.dumps(capabilities),
                       endpoint, AgentStatus.ONLINE.value, datetime.now().isoformat(),
                       json.dumps(metadata or {})))
            conn.commit()
            return {'success': True, 'message': 'Agent注册成功'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def update_agent_status(self, agent_id: str, status: str) -> Dict:
        """更新Agent状态"""
        conn = self.db.get_connection()
        try:
            c = conn.cursor()
            c.execute('UPDATE agents SET status = ?, last_heartbeat = ? WHERE id = ?',
                      (status, datetime.now().isoformat(), agent_id))
            conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_available_agents(self, capability: str = None) -> List[Dict]:
        """获取可用的Agent"""
        # 先检查Agent健康状态
        self.check_agent_health()
        
        conn = self.db.get_connection()
        try:
            c = conn.cursor()
            if capability:
                c.execute('''SELECT *
                             FROM agents
                             WHERE status = ?
                               AND capabilities LIKE ?''',
                          (AgentStatus.ONLINE.value, f'%{capability}%'))
            else:
                c.execute('SELECT * FROM agents WHERE status = ?',
                          (AgentStatus.ONLINE.value,))

            agents = []
            for row in c.fetchall():
                agent_dict = dict(row)
                agent_dict['capabilities'] = json.loads(agent_dict['capabilities'] or '[]')
                agent_dict['metadata'] = json.loads(agent_dict['metadata'] or '{}')
                agents.append(agent_dict)

            return agents
        finally:
            conn.close()

    def heartbeat(self, agent_id: str) -> Dict:
        """Agent心跳"""
        conn = self.db.get_connection()
        try:
            c = conn.cursor()
            c.execute('UPDATE agents SET last_heartbeat = ? WHERE id = ?',
                      (datetime.now().isoformat(), agent_id))
            conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def check_agent_health(self):
        """检查Agent健康状态"""
        conn = self.db.get_connection()
        try:
            c = conn.cursor()
            # 找出超时的Agent
            timeout_time = datetime.now() - timedelta(seconds=AGENT_HEARTBEAT_TIMEOUT)
            c.execute('''UPDATE agents
                         SET status = ?
                         WHERE status != ? AND last_heartbeat < ?''',
                      (AgentStatus.OFFLINE.value, AgentStatus.OFFLINE.value,
                       timeout_time.isoformat()))
            conn.commit()
        finally:
            conn.close()

    def get_all_agents(self) -> List[Dict]:
        """获取所有Agent"""
        # 先检查Agent健康状态，确保返回最新状态
        self.check_agent_health()
        
        conn = self.db.get_connection()
        try:
            c = conn.cursor()
            c.execute('SELECT * FROM agents ORDER BY created_at DESC')

            agents = []
            for row in c.fetchall():
                agent_dict = dict(row)
                agent_dict['capabilities'] = json.loads(agent_dict['capabilities'] or '[]')
                agent_dict['metadata'] = json.loads(agent_dict['metadata'] or '{}')
                agents.append(agent_dict)

            return agents
        finally:
            conn.close()