"""
推荐缓存管理服务
提供快速的缓存推荐查询，避免实时AI调用
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models.database import Database
from services.ai_based_recommender import AIBasedRecommender
from services.async_recommendation_processor import recommendation_processor
from config import DATABASE_PATH


class RecommendationCacheManager:
    """推荐缓存管理器"""
    
    def __init__(self):
        self.db = Database(DATABASE_PATH)
        self.ai_recommender = AIBasedRecommender()  # 作为回退方案
        
        # 缓存策略配置
        self.CACHE_HIT_THRESHOLD = 0.8  # 缓存命中率阈值
        self.FALLBACK_ENABLED = True  # 是否启用回退到实时计算
        self.PRECOMPUTE_TRIGGER_THRESHOLD = 2  # 连续缓存未命中次数触发预计算
        
        self._cache_miss_count = 0
    
    def get_personalized_recommendations(self, limit: int = 10) -> Dict:
        """
        获取个性化推荐（优先从缓存）
        返回格式与原AI推荐系统兼容
        """
        try:
            # 1. 尝试从缓存获取
            cached_recommendations = self._get_cached_personalized(limit)
            
            if cached_recommendations:
                self._cache_miss_count = 0  # 重置未命中计数
                return {
                    'recommendations': cached_recommendations,
                    'count': len(cached_recommendations),
                    'limit': limit,
                    'source': 'cache',
                    'generated_at': datetime.now().isoformat()
                }
            
            # 2. 缓存未命中，记录并处理
            self._cache_miss_count += 1
            print(f"⚠️ 个性化推荐缓存未命中 (连续{self._cache_miss_count}次)")
            
            # 3. 触发后台预计算
            if self._cache_miss_count >= self.PRECOMPUTE_TRIGGER_THRESHOLD:
                self._trigger_background_computation()
                self._cache_miss_count = 0
            
            # 4. 回退到实时计算（如果启用）
            if self.FALLBACK_ENABLED:
                print("🔄 回退到实时AI计算...")
                fallback_recommendations = self.ai_recommender.get_personalized_recommendations(limit)
                
                return {
                    'recommendations': fallback_recommendations,
                    'count': len(fallback_recommendations),
                    'limit': limit,
                    'source': 'fallback_realtime',
                    'generated_at': datetime.now().isoformat(),
                    'warning': '推荐结果来自实时计算，可能响应较慢'
                }
            else:
                # 返回空结果
                return {
                    'recommendations': [],
                    'count': 0,
                    'limit': limit,
                    'source': 'empty',
                    'generated_at': datetime.now().isoformat(),
                    'message': '推荐数据正在后台计算中，请稍后再试'
                }
                
        except Exception as e:
            print(f"❌ 获取个性化推荐失败: {e}")
            return {
                'recommendations': [],
                'count': 0,
                'limit': limit,
                'source': 'error',
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def get_similar_recommendations(self, paper_id: int, limit: int = 5) -> Dict:
        """
        获取相似论文推荐（优先从缓存）
        """
        try:
            # 1. 尝试从缓存获取
            cached_similar = self._get_cached_similar(paper_id, limit)
            
            if cached_similar:
                return {
                    'target_paper_id': paper_id,
                    'similar_papers': cached_similar,
                    'count': len(cached_similar),
                    'limit': limit,
                    'source': 'cache'
                }
            
            # 2. 缓存未命中，触发后台计算
            print(f"⚠️ 论文 {paper_id} 相似推荐缓存未命中")
            self._trigger_similar_computation(paper_id, limit)
            
            # 3. 回退到实时计算
            if self.FALLBACK_ENABLED:
                print("🔄 回退到实时相似度计算...")
                fallback_similar = self.ai_recommender.find_similar_papers(paper_id, limit)
                
                return {
                    'target_paper_id': paper_id,
                    'similar_papers': fallback_similar,
                    'count': len(fallback_similar),
                    'limit': limit,
                    'source': 'fallback_realtime',
                    'warning': '相似推荐来自实时计算，可能响应较慢'
                }
            else:
                return {
                    'target_paper_id': paper_id,
                    'similar_papers': [],
                    'count': 0,
                    'limit': limit,
                    'source': 'empty',
                    'message': '相似推荐正在后台计算中，请稍后再试'
                }
                
        except Exception as e:
            print(f"❌ 获取相似推荐失败: {e}")
            return {
                'target_paper_id': paper_id,
                'similar_papers': [],
                'count': 0,
                'limit': limit,
                'source': 'error',
                'error': str(e)
            }
    
    def get_recommendation_explanation(self, paper_id: int) -> Dict:
        """
        获取推荐解释（优先从缓存）
        """
        try:
            # 1. 尝试从缓存获取解释
            cached_explanation = self._get_cached_explanation(paper_id)
            
            if cached_explanation:
                return {
                    'paper_id': paper_id,
                    'paper_title': cached_explanation.get('paper_title', ''),
                    'explanation': cached_explanation.get('ai_reason', ''),
                    'analysis_method': 'AI语义分析（缓存）',
                    'source': 'cache'
                }
            
            # 2. 缓存未命中，回退到实时AI解释
            if self.FALLBACK_ENABLED:
                print(f"⚠️ 论文 {paper_id} 推荐解释缓存未命中，回退到实时计算")
                fallback_explanation = self.ai_recommender.explain_recommendation(paper_id)
                
                # 添加源标识
                fallback_explanation['source'] = 'fallback_realtime'
                fallback_explanation['warning'] = '解释来自实时AI分析，可能响应较慢'
                
                return fallback_explanation
            else:
                return {
                    'paper_id': paper_id,
                    'explanation': '推荐解释正在后台生成中，请稍后再试',
                    'source': 'empty'
                }
                
        except Exception as e:
            print(f"❌ 获取推荐解释失败: {e}")
            return {
                'paper_id': paper_id,
                'error': str(e),
                'source': 'error'
            }
    
    def _get_cached_personalized(self, limit: int) -> List[Dict]:
        """从缓存获取个性化推荐"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # 查找最匹配的缓存（优先精确匹配，然后是更大的limit）
            cache_keys = [f'personalized_{limit}']
            if limit <= 50:
                cache_keys.extend([f'personalized_{l}' for l in [50, 20, 10] if l > limit])
            
            for cache_key in cache_keys:
                c.execute('''
                    SELECT p.id, p.title, p.abstract, p.authors, p.journal, p.published_date, p.url,
                           rc.recommendation_score, rc.ai_reason, rc.rank_position
                    FROM recommendation_cache rc
                    JOIN papers p ON rc.paper_id = p.id
                    WHERE rc.cache_key = ?
                    AND rc.expires_at > CURRENT_TIMESTAMP
                    AND rc.recommendation_type = 'personalized'
                    ORDER BY rc.rank_position ASC
                    LIMIT ?
                ''', (cache_key, limit))
                
                results = c.fetchall()
                
                if results:
                    recommendations = []
                    for row in results:
                        rec = dict(row)
                        # 重新映射字段名以保持兼容性
                        rec['recommendation_score'] = row['recommendation_score']
                        rec['ai_reason'] = row['ai_reason']
                        recommendations.append(rec)
                    
                    print(f"✅ 从缓存 {cache_key} 获取了 {len(recommendations)} 个个性化推荐")
                    return recommendations
            
            return []
            
        except Exception as e:
            print(f"❌ 获取缓存个性化推荐失败: {e}")
            return []
        finally:
            conn.close()
    
    def _get_cached_similar(self, paper_id: int, limit: int) -> List[Dict]:
        """从缓存获取相似推荐"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            cache_key = f'similar_{paper_id}_{limit}'
            
            c.execute('''
                SELECT p.id, p.title, p.abstract, p.authors, p.journal, p.published_date, p.url,
                       rc.recommendation_score as similarity_score, rc.ai_reason as similarity_reason
                FROM recommendation_cache rc
                JOIN papers p ON rc.paper_id = p.id
                WHERE rc.cache_key = ?
                AND rc.expires_at > CURRENT_TIMESTAMP
                AND rc.recommendation_type = 'similar'
                ORDER BY rc.rank_position ASC
            ''', (cache_key,))
            
            results = c.fetchall()
            
            if results:
                similar_papers = []
                for row in results:
                    paper = dict(row)
                    # 重新映射字段名以保持兼容性
                    paper['similarity_score'] = row['similarity_score']
                    paper['similarity_reason'] = row['similarity_reason']
                    similar_papers.append(paper)
                
                print(f"✅ 从缓存获取了论文 {paper_id} 的 {len(similar_papers)} 个相似推荐")
                return similar_papers
            
            return []
            
        except Exception as e:
            print(f"❌ 获取缓存相似推荐失败: {e}")
            return []
        finally:
            conn.close()
    
    def _get_cached_explanation(self, paper_id: int) -> Optional[Dict]:
        """从缓存获取推荐解释"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # 查找该论文在个性化推荐缓存中的解释
            c.execute('''
                SELECT p.title as paper_title, rc.ai_reason
                FROM recommendation_cache rc
                JOIN papers p ON rc.paper_id = p.id
                WHERE rc.paper_id = ?
                AND rc.expires_at > CURRENT_TIMESTAMP
                AND rc.recommendation_type = 'personalized'
                AND rc.ai_reason IS NOT NULL
                AND LENGTH(rc.ai_reason) > 10
                LIMIT 1
            ''', (paper_id,))
            
            result = c.fetchone()
            
            if result:
                return dict(result)
            
            return None
            
        except Exception as e:
            print(f"❌ 获取缓存解释失败: {e}")
            return None
        finally:
            conn.close()
    
    def _trigger_background_computation(self):
        """触发后台个性化推荐计算"""
        try:
            recommendation_processor.create_full_recompute_job(priority=9)
            print("🚀 已触发后台个性化推荐计算")
        except Exception as e:
            print(f"❌ 触发后台计算失败: {e}")
    
    def _trigger_similar_computation(self, paper_id: int, limit: int):
        """触发后台相似推荐计算"""
        try:
            recommendation_processor.create_similar_job(paper_id, limit, priority=6)
            print(f"🚀已触发论文 {paper_id} 的后台相似推荐计算")
        except Exception as e:
            print(f"❌ 触发相似推荐计算失败: {e}")
    
    def get_cache_status(self) -> Dict:
        """获取缓存状态信息"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # 获取缓存统计
            c.execute('''
                SELECT recommendation_type, 
                       COUNT(*) as count,
                       COUNT(DISTINCT cache_key) as unique_keys,
                       MIN(expires_at) as earliest_expiry,
                       MAX(created_at) as latest_creation
                FROM recommendation_cache
                WHERE expires_at > CURRENT_TIMESTAMP
                GROUP BY recommendation_type
            ''')
            
            cache_stats = {}
            for row in c.fetchall():
                cache_stats[row['recommendation_type']] = dict(row)
            
            # 获取任务状态
            job_status = recommendation_processor.get_job_status()
            
            return {
                'cache_statistics': cache_stats,
                'job_status': job_status,
                'fallback_enabled': self.FALLBACK_ENABLED,
                'consecutive_misses': self._cache_miss_count,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ 获取缓存状态失败: {e}")
            return {
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
        finally:
            conn.close()
    
    def warm_up_cache(self):
        """预热缓存 - 手动触发推荐计算"""
        try:
            print("🔥 开始缓存预热...")
            
            # 创建全量重计算任务
            recommendation_processor.create_full_recompute_job(priority=10)
            
            # 为最近查看的论文创建相似推荐任务
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT DISTINCT pi.paper_id
                FROM paper_interactions pi
                WHERE pi.created_at > datetime('now', '-7 days')
                AND pi.interaction_type IN ('click_pdf', 'bookmark', 'explicit_like')
                LIMIT 10
            ''')
            
            recent_papers = c.fetchall()
            
            for paper in recent_papers:
                recommendation_processor.create_similar_job(paper['paper_id'], 5, priority=7)
            
            print(f"✅ 缓存预热完成，创建了 {1 + len(recent_papers)} 个后台任务")
            
        except Exception as e:
            print(f"❌ 缓存预热失败: {e}")
        finally:
            conn.close()
    
    def clear_expired_cache(self):
        """清理过期缓存（手动触发）"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('DELETE FROM recommendation_cache WHERE expires_at < CURRENT_TIMESTAMP')
            deleted_count = c.rowcount
            conn.commit()
            
            print(f"🧹 手动清理了 {deleted_count} 条过期缓存")
            return deleted_count
            
        except Exception as e:
            print(f"❌ 清理过期缓存失败: {e}")
            return 0
        finally:
            conn.close()
    
    def force_refresh_cache(self):
        """强制刷新所有缓存"""
        try:
            print("🔄 强制刷新缓存...")
            
            # 清空所有缓存
            conn = self.db.get_connection()
            c = conn.cursor()
            c.execute('DELETE FROM recommendation_cache')
            conn.commit()
            
            # 触发重新计算
            self.warm_up_cache()
            
            print("✅ 缓存强制刷新完成")
            
        except Exception as e:
            print(f"❌ 强制刷新缓存失败: {e}")
        finally:
            conn.close()


# 全局缓存管理器实例
cache_manager = RecommendationCacheManager()