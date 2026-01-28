"""
异步推荐计算处理器
负责后台AI推荐计算、缓存管理和增量更新
"""
import json
import hashlib
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models.database import Database
from services.ai_based_recommender import AIBasedRecommender
from config import DATABASE_PATH


class AsyncRecommendationProcessor:
    """异步推荐计算处理器"""
    
    def __init__(self):
        self.db = Database(DATABASE_PATH)
        self.ai_recommender = AIBasedRecommender()
        self.is_running = False
        self.processing_thread = None
        
        # 配置参数
        self.CACHE_EXPIRY_HOURS = 24  # 缓存24小时过期
        self.MAX_RETRIES = 3  # 最大重试次数
        self.PROCESS_INTERVAL = 60  # 任务处理间隔（秒）
        
    def start_background_processor(self):
        """启动后台处理线程"""
        if not self.is_running:
            self.is_running = True
            self.processing_thread = threading.Thread(target=self._process_loop, daemon=True)
            self.processing_thread.start()
            print("✅ 异步推荐处理器已启动")
    
    def stop_background_processor(self):
        """停止后台处理"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        print("⚠️ 异步推荐处理器已停止")
    
    def _process_loop(self):
        """后台处理循环"""
        while self.is_running:
            try:
                # 处理待执行的任务
                self._process_pending_jobs()
                
                # 清理过期缓存
                self._cleanup_expired_cache()
                
                # 检查用户兴趣变化，触发增量更新
                self._check_interest_changes()
                
                # 等待下一次处理
                time.sleep(self.PROCESS_INTERVAL)
                
            except Exception as e:
                print(f"❌ 后台处理异常: {e}")
                time.sleep(self.PROCESS_INTERVAL)
    
    def _process_pending_jobs(self):
        """处理待执行的推荐任务"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # 获取待处理任务（按优先级排序）
            c.execute('''
                SELECT id, job_type, reference_data, priority
                FROM recommendation_jobs
                WHERE job_status = 'pending'
                ORDER BY priority DESC, created_at ASC
                LIMIT 5
            ''')
            
            jobs = c.fetchall()
            
            for job in jobs:
                job_id, job_type, reference_data, priority = job
                
                try:
                    # 标记任务为执行中
                    c.execute('''
                        UPDATE recommendation_jobs 
                        SET job_status = 'running', started_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (job_id,))
                    conn.commit()
                    
                    print(f"🔄 开始处理推荐任务 {job_id}: {job_type}")
                    
                    # 根据任务类型执行相应处理
                    if job_type == 'full_recompute':
                        self._process_full_recompute(job_id)
                    elif job_type == 'incremental':
                        self._process_incremental_update(job_id, reference_data)
                    elif job_type == 'similar':
                        self._process_similar_recommendations(job_id, reference_data)
                    
                    # 标记任务完成
                    c.execute('''
                        UPDATE recommendation_jobs 
                        SET job_status = 'completed', completed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (job_id,))
                    conn.commit()
                    
                    print(f"✅ 推荐任务 {job_id} 处理完成")
                    
                except Exception as e:
                    # 标记任务失败
                    c.execute('''
                        UPDATE recommendation_jobs 
                        SET job_status = 'failed', 
                            completed_at = CURRENT_TIMESTAMP,
                            error_message = ?
                        WHERE id = ?
                    ''', (str(e), job_id))
                    conn.commit()
                    print(f"❌ 推荐任务 {job_id} 处理失败: {e}")
                    
        except Exception as e:
            print(f"❌ 处理推荐任务失败: {e}")
        finally:
            conn.close()
    
    def _process_full_recompute(self, job_id: int):
        """处理全量重计算任务"""
        try:
            # 清除旧的个性化推荐缓存
            self._clear_cache('personalized')
            
            # 重新计算个性化推荐
            recommendations = self.ai_recommender.get_personalized_recommendations(limit=50)
            
            if recommendations:
                # 缓存新的推荐结果
                cache_key = 'personalized_50'
                self._cache_recommendations(cache_key, recommendations, 'personalized')
                
                # 创建不同limit的缓存版本
                for limit in [5, 10, 20]:
                    limited_recs = recommendations[:limit]
                    limited_key = f'personalized_{limit}'
                    self._cache_recommendations(limited_key, limited_recs, 'personalized')
                
                print(f"✅ 全量重计算完成，缓存了 {len(recommendations)} 个推荐")
            else:
                print("⚠️ 全量重计算未生成推荐结果")
                
        except Exception as e:
            print(f"❌ 全量重计算失败: {e}")
            raise
    
    def _process_incremental_update(self, job_id: int, reference_data: str):
        """处理增量更新任务"""
        try:
            # 解析参考数据
            data = json.loads(reference_data) if reference_data else {}
            trigger_reason = data.get('trigger_reason', 'unknown')
            
            print(f"🔄 增量更新触发原因: {trigger_reason}")
            
            # 检查是否需要更新
            if self._should_perform_incremental_update():
                # 执行增量更新（实际上还是全量计算，但可以优化）
                self._process_full_recompute(job_id)
            else:
                print("⚠️ 跳过增量更新，兴趣数据无显著变化")
                
        except Exception as e:
            print(f"❌ 增量更新失败: {e}")
            raise
    
    def _process_similar_recommendations(self, job_id: int, reference_data: str):
        """处理相似论文推荐任务"""
        try:
            data = json.loads(reference_data) if reference_data else {}
            paper_id = data.get('paper_id')
            limit = data.get('limit', 5)
            
            if not paper_id:
                raise ValueError("缺少paper_id参数")
            
            # 计算相似论文
            similar_papers = self.ai_recommender.find_similar_papers(paper_id, limit=limit)
            
            if similar_papers:
                # 缓存相似论文推荐
                cache_key = f'similar_{paper_id}_{limit}'
                self._cache_recommendations(cache_key, similar_papers, 'similar', paper_id)
                
                print(f"✅ 论文 {paper_id} 的相似推荐计算完成，缓存了 {len(similar_papers)} 个结果")
            else:
                print(f"⚠️ 论文 {paper_id} 未找到相似推荐")
                
        except Exception as e:
            print(f"❌ 相似推荐计算失败: {e}")
            raise
    
    def _cache_recommendations(self, cache_key: str, recommendations: List[Dict], 
                              rec_type: str, reference_paper_id: Optional[int] = None):
        """缓存推荐结果"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # 清除旧缓存
            c.execute('DELETE FROM recommendation_cache WHERE cache_key = ?', (cache_key,))
            
            # 计算过期时间
            expires_at = datetime.now() + timedelta(hours=self.CACHE_EXPIRY_HOURS)
            
            # 插入新缓存
            for i, rec in enumerate(recommendations):
                c.execute('''
                    INSERT INTO recommendation_cache 
                    (cache_key, paper_id, recommendation_type, reference_paper_id,
                     recommendation_score, ai_reason, rank_position, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cache_key,
                    rec['id'],
                    rec_type,
                    reference_paper_id,
                    rec.get('recommendation_score', 0.0),
                    rec.get('ai_reason', ''),
                    i + 1,
                    expires_at
                ))
            
            conn.commit()
            print(f"📦 缓存 {cache_key}: {len(recommendations)} 条推荐")
            
        except Exception as e:
            print(f"❌ 缓存推荐结果失败: {e}")
            raise
        finally:
            conn.close()
    
    def _clear_cache(self, recommendation_type: str):
        """清除指定类型的缓存"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('''
                DELETE FROM recommendation_cache 
                WHERE recommendation_type = ?
            ''', (recommendation_type,))
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ 清除缓存失败: {e}")
        finally:
            conn.close()
    
    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('''
                DELETE FROM recommendation_cache 
                WHERE expires_at < CURRENT_TIMESTAMP
            ''')
            
            deleted_count = c.rowcount
            conn.commit()
            
            if deleted_count > 0:
                print(f"🧹 清理了 {deleted_count} 条过期缓存")
                
        except Exception as e:
            print(f"❌ 清理过期缓存失败: {e}")
        finally:
            conn.close()
    
    def _check_interest_changes(self):
        """检查用户兴趣变化，触发增量更新"""
        try:
            # 获取当前用户兴趣数据
            current_interests = self._get_current_interests_hash()
            
            # 获取最近的快照
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT snapshot_hash, liked_papers_count
                FROM user_interest_snapshots
                WHERE is_current = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            ''')
            
            last_snapshot = c.fetchone()
            
            # 如果兴趣发生变化，触发增量更新
            if not last_snapshot or last_snapshot['snapshot_hash'] != current_interests['hash']:
                
                # 更新快照
                self._update_interest_snapshot(current_interests)
                
                # 如果有显著变化，创建增量更新任务
                if self._is_significant_change(last_snapshot, current_interests):
                    self._create_incremental_job('interest_change')
                    print("🔄 检测到用户兴趣显著变化，触发增量更新")
                    
        except Exception as e:
            print(f"❌ 检查兴趣变化失败: {e}")
        finally:
            conn.close()
    
    def _get_current_interests_hash(self) -> Dict:
        """获取当前用户兴趣的哈希值"""
        try:
            liked_papers = self.ai_recommender._get_user_liked_papers()
            
            # 创建兴趣数据快照
            interests_data = {
                'liked_papers_count': len(liked_papers),
                'liked_papers_ids': sorted([p['id'] for p in liked_papers]),
                'timestamp': datetime.now().isoformat()
            }
            
            # 计算哈希值
            data_str = json.dumps(interests_data, sort_keys=True)
            hash_value = hashlib.md5(data_str.encode()).hexdigest()
            
            return {
                'hash': hash_value,
                'data': interests_data,
                'liked_papers_count': len(liked_papers)
            }
            
        except Exception as e:
            print(f"❌ 获取兴趣哈希失败: {e}")
            return {'hash': '', 'data': {}, 'liked_papers_count': 0}
    
    def _update_interest_snapshot(self, current_interests: Dict):
        """更新用户兴趣快照"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # 将旧快照标记为非当前
            c.execute('UPDATE user_interest_snapshots SET is_current = FALSE')
            
            # 插入新快照
            c.execute('''
                INSERT INTO user_interest_snapshots
                (snapshot_hash, liked_papers_count, snapshot_data)
                VALUES (?, ?, ?)
            ''', (
                current_interests['hash'], 
                current_interests['liked_papers_count'],
                json.dumps(current_interests['data'])
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ 更新兴趣快照失败: {e}")
        finally:
            conn.close()
    
    def _is_significant_change(self, last_snapshot: Optional[Dict], current_interests: Dict) -> bool:
        """判断是否为显著的兴趣变化"""
        if not last_snapshot:
            return True  # 首次运行
        
        last_count =last_snapshot.get('liked_papers_count', 0)
        current_count = current_interests['liked_papers_count']
        
        # 如果喜爱论文数量变化超过20%或增加了3篇以上，认为是显著变化
        if current_count == 0:
            return False
        
        change_ratio = abs(current_count - last_count) / max(current_count, 1)
        change_absolute = abs(current_count - last_count)
        
        return change_ratio > 0.2 or change_absolute >= 3
    
    def _should_perform_incremental_update(self) -> bool:
        """判断是否应该执行增量更新"""
        # 这里可以添加更复杂的逻辑，比如检查缓存是否过旧等
        return True
    
    def _create_incremental_job(self, trigger_reason: str):
        """创建增量更新任务"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            reference_data = json.dumps({
                'trigger_reason': trigger_reason,
                'created_by': 'interest_monitor'
            })
            
            c.execute('''
                INSERT INTO recommendation_jobs
                (job_type, priority, reference_data)
                VALUES ('incremental', 8, ?)
            ''', (reference_data,))
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ 创建增量更新任务失败: {e}")
        finally:
            conn.close()
    
    # 公开方法：手动触发任务
    
    def create_full_recompute_job(self, priority: int = 7):
        """手动创建全量重计算任务"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO recommendation_jobs
                (job_type, priority)
                VALUES ('full_recompute', ?)
            ''', (priority,))
            
            conn.commit()
            print("✅ 全量重计算任务已创建")
            
        except Exception as e:
            print(f"❌ 创建全量重计算任务失败: {e}")
        finally:
            conn.close()
    
    def create_similar_job(self, paper_id: int, limit: int = 5, priority: int = 5):
        """手动创建相似推荐任务"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            reference_data = json.dumps({
                'paper_id': paper_id,
                'limit': limit
            })
            
            c.execute('''
                INSERT INTO recommendation_jobs
                (job_type, priority, reference_data)
                VALUES ('similar', ?, ?)
            ''', (priority, reference_data))
            
            conn.commit()
            print(f"✅ 论文 {paper_id} 的相似推荐任务已创建")
            
        except Exception as e:
            print(f"❌ 创建相似推荐任务失败: {e}")
        finally:
            conn.close()
    
    def get_job_status(self) -> Dict:
        """获取任务处理状态"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT job_status, COUNT(*) as count
                FROM recommendation_jobs
                GROUP BY job_status
            ''')
            
            status_counts = dict(c.fetchall())
            
            c.execute('''
                SELECT COUNT(*) as cache_count,
                       MIN(expires_at) as earliest_expiry
                FROM recommendation_cache
                WHERE expires_at > CURRENT_TIMESTAMP
            ''')
            
            cache_info = c.fetchone()
            
            return {
                'processor_running': self.is_running,
                'job_counts': status_counts,
                'cache_count': cache_info['cache_count'] if cache_info else 0,
                'earliest_cache_expiry': cache_info['earliest_expiry'] if cache_info else None
            }
            
        except Exception as e:
            print(f"❌ 获取任务状态失败: {e}")
            return {}
        finally:
            conn.close()


# 全局处理器实例
recommendation_processor = AsyncRecommendationProcessor()