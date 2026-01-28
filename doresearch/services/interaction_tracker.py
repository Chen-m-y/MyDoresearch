"""
智能交互追踪服务 - 推荐系统的核心数据收集模块
基于用户行为智能评估对论文的兴趣度
"""
import sqlite3
import time
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from models.database import Database
from config import DATABASE_PATH


class InteractionTracker:
    """智能交互追踪服务"""
    
    # 交互类型常量
    INTERACTION_TYPES = {
        'VIEW_START': 'view_start',        # 开始查看论文
        'VIEW_END': 'view_end',           # 结束查看论文
        'SCROLL': 'scroll',               # 滚动浏览
        'CLICK_PDF': 'click_pdf',         # 点击PDF链接
        'CLICK_URL': 'click_url',         # 点击论文URL
        'BOOKMARK': 'bookmark',           # 加入稍后阅读
        'UNBOOKMARK': 'unbookmark',       # 移除稍后阅读
        'EXPLICIT_LIKE': 'explicit_like', # 明确表示喜欢
        'EXPLICIT_DISLIKE': 'explicit_dislike',  # 明确表示不喜欢
        'SEARCH_CLICK': 'search_click',   # 从搜索结果点击进入
    }
    
    # 兴趣强度权重配置（只保留明确行为）
    INTEREST_WEIGHTS = {
        'EXPLICIT_LIKE': 100,      # 明确喜欢
        'EXPLICIT_DISLIKE': -100,  # 明确不喜欢
        'BOOKMARK': 80,            # 收藏
        'UNBOOKMARK': -80,         # 取消收藏
        'CLICK_PDF': 60,           # 点击PDF
        'CLICK_URL': 40,           # 点击原文链接
        # 其他行为不再计入评分
        'VIEW_START': 0,
        'VIEW_END': 0,
        'SCROLL': 0,
        'SEARCH_CLICK': 0,
    }
    
    def __init__(self):
        self.db = Database(DATABASE_PATH)
    
    def track_interaction(self, paper_id: int, interaction_type: str, 
                         duration_seconds: int = 0, scroll_depth_percent: int = 0,
                         click_count: int = 0, session_id: str = None,
                         user_agent: str = None, metadata: dict = None) -> bool:
        """
        记录用户与论文的交互行为
        
        Args:
            paper_id: 论文ID
            interaction_type: 交互类型
            duration_seconds: 持续时间（秒）
            scroll_depth_percent: 滚动深度百分比 (0-100)
            click_count: 点击次数
            session_id: 会话ID
            user_agent: 用户代理
            metadata: 额外元数据
        """
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # 插入交互记录
            c.execute('''INSERT INTO paper_interactions 
                        (paper_id, interaction_type, duration_seconds, scroll_depth_percent,
                         click_count, session_id, user_agent, created_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (paper_id, interaction_type, duration_seconds, scroll_depth_percent,
                      click_count, session_id, user_agent, datetime.now()))
            
            conn.commit()
            
            # 异步更新兴趣评分
            self._update_interest_score(paper_id)
            
            return True
            
        except Exception as e:
            print(f"❌ 记录交互失败: {e}")
            return False
        finally:
            conn.close()
    
    def track_paper_view(self, paper_id: int, duration_seconds: int, 
                        scroll_depth_percent: int, session_id: str = None) -> Dict:
        """
        记录论文查看行为并智能评估兴趣度
        
        Returns:
            包含兴趣评估结果的字典
        """
        # 记录查看交互
        self.track_interaction(
            paper_id=paper_id,
            interaction_type=self.INTERACTION_TYPES['VIEW_END'],
            duration_seconds=duration_seconds,
            scroll_depth_percent=scroll_depth_percent,
            session_id=session_id
        )
        
        # 分析兴趣信号
        interest_signals = self._analyze_interest_signals(paper_id, duration_seconds, scroll_depth_percent)
        
        return {
            'paper_id': paper_id,
            'duration_seconds': duration_seconds,
            'scroll_depth_percent': scroll_depth_percent,
            'interest_level': interest_signals['level'],
            'interest_score': interest_signals['score'],
            'signals': interest_signals['signals']
        }
    
    def _analyze_interest_signals(self, paper_id: int, duration: int, scroll_depth: int) -> Dict:
        """分析用户行为的兴趣信号（简化版：不依赖时间因素）"""
        # 这个函数保留但不作为主要推荐依据，只用于提供反馈
        signals = ['此次交互已记录']
        
        # 简化版本：不再基于时间和滚动进行复杂判断
        level = 'recorded'  # 只表示已记录
        final_score = 0     # 不再生成自动评分
        
        return {
            'level': level,
            'score': final_score, 
            'signals': signals,
            'duration': duration,
            'scroll_depth': scroll_depth,
            'analysis_method': 'explicit_only'
        }
    
    def _update_interest_score(self, paper_id: int):
        """更新论文的综合兴趣评分"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # 获取该论文的所有交互记录
            c.execute('''SELECT interaction_type, duration_seconds, scroll_depth_percent, 
                               click_count, created_at 
                        FROM paper_interactions 
                        WHERE paper_id = ? 
                        ORDER BY created_at DESC''', (paper_id,))
            
            interactions = c.fetchall()
            
            if not interactions:
                return
            
            # 计算综合评分
            total_score = 0
            total_view_time = 0
            max_scroll = 0
            interaction_count = len(interactions)
            bookmark_count = 0
            
            # 只关注明确的兴趣标记，完全忽略时间和滚动数据
            for interaction in interactions:
                itype = interaction['interaction_type']
                duration = interaction['duration_seconds'] or 0
                scroll = interaction['scroll_depth_percent'] or 0
                
                # 只计算明确的行为权重
                if itype == self.INTERACTION_TYPES['EXPLICIT_LIKE']:
                    total_score += 100  # 明确喜欢 = 直接高分
                elif itype == self.INTERACTION_TYPES['EXPLICIT_DISLIKE']:
                    total_score -= 100  # 明确不喜欢 = 直接低分
                elif itype == self.INTERACTION_TYPES['BOOKMARK']:
                    total_score += 80   # 收藏 = 高兴趣
                    bookmark_count += 1
                elif itype == self.INTERACTION_TYPES['UNBOOKMARK']:
                    total_score -= 80   # 取消收藏 = 降低兴趣
                    bookmark_count = max(0, bookmark_count - 1)
                elif itype == self.INTERACTION_TYPES['CLICK_PDF']:
                    total_score += 60   # 点击PDF = 中高兴趣
                elif itype == self.INTERACTION_TYPES['CLICK_URL']:
                    total_score += 40   # 点击原文链接 = 中等兴趣
                
                # 统计数据（不影响评分）
                total_view_time += duration
                if scroll > max_scroll:
                    max_scroll = scroll
            
            # 最终评分 (0-100)
            final_score = max(0, min(100, total_score))
            
            # 检查是否在稍后阅读列表中
            c.execute('SELECT COUNT(*) as count FROM read_later WHERE paper_id = ?', (paper_id,))
            in_read_later = c.fetchone()['count'] > 0
            
            # 计算明确兴趣标记
            explicit_interest = 0
            if in_read_later:
                explicit_interest = 1
                
            # 检查是否有明确的喜欢/不喜欢标记
            explicit_like_count = sum(1 for interaction in interactions 
                                    if interaction['interaction_type'] == self.INTERACTION_TYPES['EXPLICIT_LIKE'])
            explicit_dislike_count = sum(1 for interaction in interactions 
                                       if interaction['interaction_type'] == self.INTERACTION_TYPES['EXPLICIT_DISLIKE'])
            
            if explicit_like_count > explicit_dislike_count:
                explicit_interest = 1
            elif explicit_dislike_count > explicit_like_count:
                explicit_interest = -1
            
            # 更新或插入兴趣评分记录
            c.execute('''INSERT OR REPLACE INTO paper_interest_scores 
                        (paper_id, interest_score, interaction_count, total_view_time,
                         max_scroll_depth, last_interaction_at, bookmark_count, explicit_interest,
                         calculated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (paper_id, final_score, interaction_count, total_view_time,
                      max_scroll, datetime.now(), bookmark_count, explicit_interest, datetime.now()))
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ 更新兴趣评分失败: {e}")
        finally:
            conn.close()
    
    def get_paper_interest_score(self, paper_id: int) -> Optional[Dict]:
        """获取论文的兴趣评分详情"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('''SELECT * FROM paper_interest_scores WHERE paper_id = ?''', (paper_id,))
            result = c.fetchone()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            print(f"❌ 获取兴趣评分失败: {e}")
            return None
        finally:
            conn.close()
    
    def get_high_interest_papers(self, min_score: int = 60, limit: int = 50) -> List[Dict]:
        """获取高兴趣度的论文列表"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('''SELECT p.*, pis.interest_score, pis.total_view_time, pis.explicit_interest
                        FROM papers p
                        JOIN paper_interest_scores pis ON p.id = pis.paper_id
                        WHERE pis.interest_score >= ?
                        ORDER BY pis.interest_score DESC, pis.last_interaction_at DESC
                        LIMIT ?''', (min_score, limit))
            
            return [dict(row) for row in c.fetchall()]
            
        except Exception as e:
            print(f"❌ 获取高兴趣论文失败: {e}")
            return []
        finally:
            conn.close()
    
    def analyze_user_patterns(self) -> Dict:
        """分析用户的整体兴趣模式"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # 分析关键词模式
            c.execute('''
                SELECT p.title, p.abstract, pis.interest_score 
                FROM papers p
                JOIN paper_interest_scores pis ON p.id = pis.paper_id
                WHERE pis.interest_score > 50
                ORDER BY pis.interest_score DESC
                LIMIT 100
            ''')
            
            high_interest_papers = c.fetchall()
            
            # 提取关键词（简单实现）
            keyword_scores = {}
            
            for paper in high_interest_papers:
                title = paper['title'] or ''
                abstract = paper['abstract'] or ''
                score = paper['interest_score']
                
                # 简单的关键词提取（可以改进为更复杂的NLP算法）
                text = (title + ' ' + abstract).lower()
                words = re.findall(r'\b\w+\b', text)
                
                for word in words:
                    if len(word) > 3:  # 只考虑长度>3的词
                        if word not in keyword_scores:
                            keyword_scores[word] = []
                        keyword_scores[word].append(score)
            
            # 计算关键词的平均兴趣度
            keyword_patterns = {}
            for word, scores in keyword_scores.items():
                if len(scores) >= 2:  # 至少出现2次
                    avg_score = sum(scores) / len(scores)
                    keyword_patterns[word] = {
                        'average_score': avg_score,
                        'occurrence_count': len(scores),
                        'strength': min(1.0, avg_score / 100.0)
                    }
            
            # 按强度排序
            sorted_patterns = sorted(keyword_patterns.items(), 
                                   key=lambda x: x[1]['strength'], reverse=True)
            
            return {
                'keyword_patterns': dict(sorted_patterns[:20]),  # 前20个关键词
                'total_analyzed_papers': len(high_interest_papers),
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ 分析用户模式失败: {e}")
            return {}
        finally:
            conn.close()
    
    def get_interaction_stats(self, days: int = 30) -> Dict:
        """获取交互统计信息"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            since_date = datetime.now() - timedelta(days=days)
            
            # 总体统计
            c.execute('''SELECT 
                            COUNT(*) as total_interactions,
                            COUNT(DISTINCT paper_id) as unique_papers,
                            AVG(duration_seconds) as avg_duration,
                            AVG(scroll_depth_percent) as avg_scroll_depth
                        FROM paper_interactions 
                        WHERE created_at >= ?''', (since_date,))
            
            stats = dict(c.fetchone())
            
            # 按交互类型统计
            c.execute('''SELECT interaction_type, COUNT(*) as count
                        FROM paper_interactions 
                        WHERE created_at >= ?
                        GROUP BY interaction_type
                        ORDER BY count DESC''', (since_date,))
            
            stats['interaction_types'] = {row['interaction_type']: row['count'] 
                                        for row in c.fetchall()}
            
            # 兴趣度分布
            c.execute('''SELECT 
                            CASE 
                                WHEN interest_score >= 80 THEN 'very_high'
                                WHEN interest_score >= 60 THEN 'high'  
                                WHEN interest_score >= 40 THEN 'medium'
                                WHEN interest_score >= 20 THEN 'low'
                                ELSE 'very_low'
                            END as interest_level,
                            COUNT(*) as count
                        FROM paper_interest_scores
                        GROUP BY interest_level''')
            
            stats['interest_distribution'] = {row['interest_level']: row['count'] 
                                            for row in c.fetchall()}
            
            return stats
            
        except Exception as e:
            print(f"❌ 获取交互统计失败: {e}")
            return {}
        finally:
            conn.close()