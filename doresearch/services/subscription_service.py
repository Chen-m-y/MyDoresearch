"""
新订阅管理系统服务层
处理外部微服务调用、参数验证、同步调度等
"""
import json
import requests
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from jsonschema import validate, ValidationError
import threading
import time

from models.subscription_models import (
    SubscriptionTemplateManager, 
    UserSubscriptionManager, 
    SyncHistoryManager
)
from models.database import Database
from config import DATABASE_PATH


class ExternalServiceClient:
    """外部微服务客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def health_check(self) -> Dict:
        """检查外部服务健康状态"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_supported_sources(self) -> Dict:
        """获取支持的数据源列表"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/sources",
                timeout=self.timeout
            )
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def fetch_papers(self, source: str, source_params: Dict) -> Dict:
        """从外部服务获取论文数据"""
        try:
            payload = {
                'source': source,
                'source_params': source_params
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/fetch",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return {'success': True, 'data': result}
        except requests.exceptions.Timeout:
            return {'success': False, 'error': '请求超时'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'网络请求失败: {str(e)}'}
        except json.JSONDecodeError:
            return {'success': False, 'error': 'JSON解析失败'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class ParameterValidator:
    """参数验证器"""
    
    @staticmethod
    def validate_parameters(params: Dict, schema: Dict) -> Dict:
        """根据JSON Schema验证参数"""
        try:
            validate(instance=params, schema=schema)
            return {'valid': True}
        except ValidationError as e:
            return {'valid': False, 'error': e.message}
        except Exception as e:
            return {'valid': False, 'error': str(e)}


class PaperProcessor:
    """论文数据处理器"""
    
    def __init__(self, db_path: str):
        self.db = Database(db_path)
    
    def get_connection(self):
        """获取数据库连接"""
        return self.db.get_connection()
    
    def process_papers(self, papers: List[Dict], subscription_id: int, 
                      feed_name: str) -> Dict:
        """处理并存储论文数据"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            new_papers = 0
            total_papers = len(papers)
            
            for paper_data in papers:
                if not paper_data.get('title'):
                    continue
                
                # 生成论文哈希用于去重
                paper_hash = self._generate_paper_hash(paper_data)
                
                # 检查论文是否已存在
                c.execute('SELECT id FROM papers WHERE hash = ?', (paper_hash,))
                if c.fetchone():
                    continue
                
                # 标准化论文数据
                standardized_paper = self._standardize_paper_data(
                    paper_data, subscription_id, feed_name
                )
                
                # 插入论文
                c.execute('''INSERT INTO papers
                             (subscription_id, title, abstract, authors, journal, published_date,
                              url, pdf_url, doi, status, status_changed_at, hash, external_id, 
                              ieee_article_number, keywords, citations, metadata)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (
                              standardized_paper['subscription_id'],
                              standardized_paper['title'],
                              standardized_paper['abstract'],
                              standardized_paper['authors'],
                              standardized_paper['journal'],
                              standardized_paper['published_date'],
                              standardized_paper['url'],
                              standardized_paper['pdf_url'],
                              standardized_paper['doi'],
                              standardized_paper['status'],
                              standardized_paper['status_changed_at'],
                              standardized_paper['hash'],
                              standardized_paper['external_id'],
                              standardized_paper['ieee_article_number'],
                              standardized_paper['keywords'],
                              standardized_paper['citations'],
                              standardized_paper['metadata']
                          ))
                new_papers += 1
            
            conn.commit()
            return {
                'success': True,
                'total_papers': total_papers,
                'new_papers': new_papers
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def _generate_paper_hash(self, paper_data: Dict) -> str:
        """生成论文哈希"""
        hash_content = (
            paper_data.get('title', '') +
            paper_data.get('url', '') +
            paper_data.get('doi', '') +
            str(paper_data.get('source_specific', {}).get('ieee_number', ''))
        )
        return hashlib.md5(hash_content.encode()).hexdigest()
    
    def _standardize_paper_data(self, paper_data: Dict, subscription_id: int, 
                               feed_name: str) -> Dict:
        """标准化论文数据格式"""
        current_time = datetime.now().isoformat()
        
        # 处理作者信息
        authors = paper_data.get('authors', [])
        if isinstance(authors, list):
            authors_str = ', '.join(authors)
        else:
            authors_str = str(authors) if authors else ''
        
        # 处理关键词
        keywords = paper_data.get('keywords', [])
        keywords_str = json.dumps(keywords) if keywords else None
        
        # 处理引用数
        citations = paper_data.get('citations', 0)
        if not isinstance(citations, int):
            citations = 0
        
        # 处理元数据
        metadata = {
            'source_specific': paper_data.get('source_specific', {}),
            'metadata': paper_data.get('metadata', {}),
            'feed_name': feed_name
        }
        
        return {
            'subscription_id': subscription_id,
            'title': paper_data.get('title', '').strip(),
            'abstract': paper_data.get('abstract', '').strip(),
            'authors': authors_str,
            'journal': paper_data.get('journal', ''),
            'published_date': self._parse_date(paper_data.get('published_date')),
            'url': paper_data.get('url', ''),
            'pdf_url': paper_data.get('pdf_url', ''),
            'doi': paper_data.get('doi', ''),
            'status': 'unread',
            'status_changed_at': current_time,
            'hash': self._generate_paper_hash(paper_data),
            'external_id': str(paper_data.get('id', '')),
            'ieee_article_number': paper_data.get('source_specific', {}).get('ieee_number'),
            'keywords': keywords_str,
            'citations': citations,
            'metadata': json.dumps(metadata)
        }
    
    def _parse_date(self, date_str: Any) -> Optional[str]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        try:
            # 尝试解析ISO格式日期
            if isinstance(date_str, str):
                # 移除时区信息简化处理
                date_str = date_str.replace('Z', '').split('+')[0].split('T')[0]
                datetime.strptime(date_str, '%Y-%m-%d')
                return date_str
            return str(date_str)
        except:
            return None


class SubscriptionSyncService:
    """订阅同步服务"""
    
    def __init__(self, db_path: str = DATABASE_PATH, 
                 external_service_url: str = "http://localhost:8000"):
        self.db_path = db_path
        self.user_subscription_manager = UserSubscriptionManager(db_path)
        self.sync_history_manager = SyncHistoryManager(db_path)
        self.paper_processor = PaperProcessor(db_path)
        self.external_client = ExternalServiceClient(external_service_url)
        
        self._running = False
        self._sync_thread = None
    
    def start(self):
        """启动同步服务"""
        if self._running:
            return
        
        self._running = True
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()
        print("✅ 订阅同步服务已启动")
    
    def stop(self):
        """停止同步服务"""
        self._running = False
        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5)
        print("⏹️ 订阅同步服务已停止")
    
    def _sync_loop(self):
        """同步循环"""
        while self._running:
            try:
                self._process_pending_syncs()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                print(f"❌ 同步循环异常: {e}")
                time.sleep(60)
    
    def _process_pending_syncs(self):
        """处理待同步的订阅"""
        subscriptions = self.user_subscription_manager.get_subscriptions_for_sync(10)
        
        for subscription in subscriptions:
            try:
                self._sync_subscription(subscription)
            except Exception as e:
                print(f"❌ 订阅 {subscription['id']} 同步失败: {e}")
                self._handle_sync_error(subscription['id'], str(e))
    
    def _sync_subscription(self, subscription: Dict):
        """同步单个订阅"""
        subscription_id = subscription['id']
        
        # 创建同步记录
        sync_id = self.sync_history_manager.create_sync_record(subscription_id)
        
        try:
            # 调用外部服务获取论文
            result = self.external_client.fetch_papers(
                subscription['source_type'], 
                subscription['source_params']
            )
            
            if not result['success']:
                raise Exception(result['error'])
            
            service_data = result['data']
            papers = service_data.get('data', {}).get('papers', [])
            
            # 处理论文数据
            process_result = self.paper_processor.process_papers(
                papers, subscription_id, subscription['name']
            )
            
            if not process_result['success']:
                raise Exception(process_result['error'])
            
            # 更新同步记录为成功
            self.sync_history_manager.update_sync_record(
                sync_id, 'success',
                papers_found=process_result['total_papers'],
                papers_new=process_result['new_papers'],
                service_response=json.dumps(service_data)
            )
            
            # 更新订阅的同步状态
            next_sync = self._calculate_next_sync_time(subscription)
            self.user_subscription_manager.update_sync_status(
                subscription_id,
                last_sync_at=datetime.now().isoformat(),
                next_sync_at=next_sync.isoformat(),
                error_message=None,
                status='active'
            )
            
            print(f"✅ 订阅 {subscription_id} 同步成功: "
                  f"发现 {process_result['total_papers']} 篇，"
                  f"新增 {process_result['new_papers']} 篇")
            
        except Exception as e:
            # 更新同步记录为失败
            self.sync_history_manager.update_sync_record(
                sync_id, 'error', error_details=str(e)
            )
            
            # 更新订阅状态为错误
            self.user_subscription_manager.update_sync_status(
                subscription_id,
                error_message=str(e),
                status='error'
            )
            
            print(f"❌ 订阅 {subscription_id} 同步失败: {e}")
    
    def _calculate_next_sync_time(self, subscription: Dict) -> datetime:
        """计算下次同步时间"""
        sync_frequency = subscription.get('sync_frequency', 86400)  # 默认24小时
        
        # 对于会议类型，可以设置更长的同步间隔
        if subscription['source_type'] == 'dblp':
            # 会议论文通常不会频繁更新，可以设置为一周同步一次
            sync_frequency = max(sync_frequency, 604800)  # 至少7天
        
        return datetime.now() + timedelta(seconds=sync_frequency)
    
    def _handle_sync_error(self, subscription_id: int, error_message: str):
        """处理同步错误"""
        # 可以实现错误重试逻辑
        # 这里简单地设置错误状态
        self.user_subscription_manager.update_sync_status(
            subscription_id,
            error_message=error_message,
            status='error'
        )
    
    def manual_sync_subscription(self, subscription_id: int, user_id: Optional[int] = None) -> Dict:
        """手动同步指定订阅"""
        try:
            # 获取订阅信息
            subscription = self.user_subscription_manager.get_subscription(subscription_id, user_id)
            if not subscription:
                return {'success': False, 'error': '订阅不存在或无权限'}
            
            if subscription['status'] != 'active':
                return {'success': False, 'error': '订阅未激活'}
            
            # 执行同步
            self._sync_subscription(subscription)
            return {'success': True, 'message': '同步已完成'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class NewSubscriptionService:
    """新订阅管理服务 - 统一服务接口"""
    
    def __init__(self, db_path: str = DATABASE_PATH, 
                 external_service_url: str = "http://localhost:8000"):
        self.template_manager = SubscriptionTemplateManager(db_path)
        self.subscription_manager = UserSubscriptionManager(db_path)
        self.sync_history_manager = SyncHistoryManager(db_path)
        self.sync_service = SubscriptionSyncService(db_path, external_service_url)
        self.external_client = ExternalServiceClient(external_service_url)
        self.validator = ParameterValidator()
    
    def start(self):
        """启动服务"""
        self.sync_service.start()
    
    def stop(self):
        """停止服务"""
        self.sync_service.stop()
    
    # 模板管理方法
    def get_templates(self) -> List[Dict]:
        """获取所有可用的订阅模板"""
        return self.template_manager.get_all_templates()
    
    def get_template(self, template_id: int) -> Optional[Dict]:
        """获取单个模板详情"""
        return self.template_manager.get_template(template_id)
    
    def create_template(self, **kwargs) -> Dict:
        """创建订阅模板（管理员功能）"""
        return self.template_manager.create_template(**kwargs)
    
    def update_template(self, template_id: int, **kwargs) -> Dict:
        """更新订阅模板（管理员功能）"""
        return self.template_manager.update_template(template_id, **kwargs)
    
    def delete_template(self, template_id: int) -> Dict:
        """删除订阅模板（管理员功能）"""
        return self.template_manager.delete_template(template_id)
    
    # 用户订阅管理方法
    def create_subscription(self, user_id: int, template_id: int, 
                          name: str, source_params: Dict) -> Dict:
        """创建用户订阅"""
        # 获取模板信息
        template = self.template_manager.get_template(template_id)
        if not template:
            return {'success': False, 'error': '订阅模板不存在'}
        
        # 验证参数
        validation_result = self.validator.validate_parameters(
            source_params, template['parameter_schema']
        )
        if not validation_result['valid']:
            return {
                'success': False, 
                'error': f'参数验证失败: {validation_result["error"]}'
            }
        
        # 创建订阅
        return self.subscription_manager.create_subscription(
            user_id, template_id, name, source_params
        )
    
    def get_user_subscriptions(self, user_id: int) -> List[Dict]:
        """获取用户的所有订阅"""
        return self.subscription_manager.get_user_subscriptions(user_id)
    
    def get_subscription(self, subscription_id: int, user_id: Optional[int] = None) -> Optional[Dict]:
        """获取单个订阅详情"""
        return self.subscription_manager.get_subscription(subscription_id, user_id)
    
    def update_subscription(self, subscription_id: int, user_id: int, **kwargs) -> Dict:
        """更新用户订阅"""
        return self.subscription_manager.update_subscription(subscription_id, user_id, **kwargs)
    
    def delete_subscription(self, subscription_id: int, user_id: int) -> Dict:
        """删除用户订阅"""
        return self.subscription_manager.delete_subscription(subscription_id, user_id)
    
    def manual_sync(self, subscription_id: int, user_id: Optional[int] = None) -> Dict:
        """手动同步订阅"""
        return self.sync_service.manual_sync_subscription(subscription_id, user_id)
    
    def get_sync_history(self, subscription_id: int, limit: int = 20) -> List[Dict]:
        """获取订阅的同步历史"""
        return self.sync_history_manager.get_subscription_history(subscription_id, limit)
    
    # 系统管理方法
    def check_external_service(self) -> Dict:
        """检查外部服务状态"""
        return self.external_client.health_check()
    
    def get_supported_sources(self) -> Dict:
        """获取支持的数据源"""
        return self.external_client.get_supported_sources()