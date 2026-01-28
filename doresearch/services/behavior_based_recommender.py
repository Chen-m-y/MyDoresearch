"""
基于行为的智能推荐服务  
根据用户的实际交互行为（而非简单的读/未读状态）进行个性化推荐
"""
import sqlite3
import re
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, Counter
from models.database import Database
from services.interaction_tracker import InteractionTracker
from config import DATABASE_PATH


class BehaviorBasedRecommender:
    """基于用户行为的智能推荐系统"""
    
    def __init__(self):
        self.db = Database(DATABASE_PATH) 
        self.interaction_tracker = InteractionTracker()
        
        # 推荐算法参数
        self.MIN_INTEREST_SCORE = 50  # 最低兴趣阈值
        self.SIMILARITY_THRESHOLD = 0.3  # 相似度阈值
        self.MAX_RECOMMENDATIONS = 20  # 最大推荐数量
        
    def get_personalized_recommendations(self, limit: int = 10) -> List[Dict]:
        """
        获取个性化推荐论文
        基于用户的历史兴趣行为进行推荐
        """
        try:
            # 1. 分析用户兴趣模式
            user_patterns = self._analyze_comprehensive_user_patterns()
            
            if not user_patterns['keywords']:
                return self._get_fallback_recommendations(limit)
            
            # 2. 基于兴趣模式找候选论文
            candidates = self._find_candidate_papers(user_patterns)
            
            # 3. 计算推荐分数
            scored_candidates = self._score_candidates(candidates, user_patterns)
            
            # 4. 过滤已交互的论文
            filtered_candidates = self._filter_interacted_papers(scored_candidates)
            
            # 5. 排序并返回结果
            final_recommendations = sorted(filtered_candidates, 
                                         key=lambda x: x['recommendation_score'], 
                                         reverse=True)[:limit]
            
            return final_recommendations
            
        except Exception as e:
            print(f"❌ 生成个性化推荐失败: {e}")
            return self._get_fallback_recommendations(limit)
    
    def _analyze_comprehensive_user_patterns(self) -> Dict:
        """分析用户兴趣模式（只基于明确标记为喜爱的文章）"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # 只获取明确标记为喜爱的论文（收藏或明确点赞）
            c.execute('''
                SELECT DISTINCT p.id, p.title, p.abstract, p.authors, p.journal
                FROM papers p
                WHERE p.id IN (
                    -- 明确点赞的论文
                    SELECT DISTINCT pi.paper_id 
                    FROM paper_interactions pi 
                    WHERE pi.interaction_type = 'explicit_like'
                    UNION
                    -- 收藏的论文
                    SELECT DISTINCT rl.paper_id 
                    FROM read_later rl
                    UNION  
                    -- 点击PDF的论文（表示想要深入阅读）
                    SELECT DISTINCT pi.paper_id 
                    FROM paper_interactions pi 
                    WHERE pi.interaction_type = 'click_pdf'
                )
                ORDER BY p.created_at DESC
                LIMIT 100
            ''')
            
            liked_papers = c.fetchall()
            
            if not liked_papers:
                return {'keywords': {}, 'authors': {}, 'journals': {}, 'total_papers': 0}
            
            # 基于喜爱文章的内容分析
            keyword_patterns = self._extract_content_keywords(liked_papers)
            author_patterns = self._extract_preferred_authors(liked_papers)
            journal_patterns = self._extract_preferred_journals(liked_papers)
            
            return {
                'keywords': keyword_patterns,
                'authors': author_patterns,
                'journals': journal_patterns,
                'total_papers': len(liked_papers)
            }
            
        except Exception as e:
            print(f"❌ 分析用户模式失败: {e}")
            return {'keywords': {}, 'authors': {}, 'journals': {}, 'total_papers': 0}
        finally:
            conn.close()
    
    def _extract_keyword_patterns(self, papers: List[Dict]) -> Dict[str, float]:
        """从高兴趣论文中提取关键词模式"""
        keyword_scores = defaultdict(list)
        
        for paper in papers:
            title = (paper['title'] or '').lower()
            abstract = (paper['abstract'] or '').lower()
            score = paper['interest_score'] if paper['interest_score'] > 0 else 60  # 稍后阅读默认60分
            
            # 合并标题和摘要进行关键词提取
            text = title + ' ' + abstract
            
            # 简单的关键词提取（后续可改进为更高级的NLP）
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text)  # 只要英文词，长度>=4
            
            # 对标题中的词给予更高权重
            title_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', title))
            
            for word in words:
                weight = 2.0 if word in title_words else 1.0
                keyword_scores[word].append(score * weight)
        
        # 计算关键词的加权平均分
        keyword_patterns = {}
        for word, scores in keyword_scores.items():
            if len(scores) >= 2:  # 至少出现2次
                avg_score = sum(scores) / len(scores)
                frequency = len(scores)
                # 综合考虑平均分和频率
                strength = min(1.0, (avg_score / 100.0) * (1 + math.log(frequency)))
                keyword_patterns[word] = strength
        
        # 返回前30个最强的关键词
        sorted_keywords = sorted(keyword_patterns.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_keywords[:30])
    
    def _extract_author_patterns(self, papers: List[Dict]) -> Dict[str, float]:
        """提取作者偏好模式"""
        author_scores = defaultdict(list)
        
        for paper in papers:
            authors = paper['authors'] or ''
            score = paper['interest_score'] if paper['interest_score'] > 0 else 60
            
            # 分割作者名（简单处理）
            author_list = [author.strip() for author in authors.split(',')]
            
            for author in author_list:
                if len(author) > 2:  # 过滤太短的名字
                    author_scores[author].append(score)
        
        # 计算作者兴趣强度
        author_patterns = {}
        for author, scores in author_scores.items():
            if len(scores) >= 2:  # 至少关注过该作者2篇论文
                avg_score = sum(scores) / len(scores)
                strength = min(1.0, avg_score / 100.0)
                author_patterns[author] = strength
        
        return author_patterns
    
    def _extract_journal_patterns(self, papers: List[Dict]) -> Dict[str, float]:
        """提取期刊偏好模式"""
        journal_scores = defaultdict(list)
        
        for paper in papers:
            journal = paper['journal'] or ''
            score = paper['interest_score'] if paper['interest_score'] > 0 else 60
            
            if journal:
                journal_scores[journal].append(score)
        
        # 计算期刊兴趣强度
        journal_patterns = {}
        for journal, scores in journal_scores.items():
            if len(scores) >= 1:  # 期刊只需要1篇即可
                avg_score = sum(scores) / len(scores)
                strength = min(1.0, avg_score / 100.0)
                journal_patterns[journal] = strength
        
        return journal_patterns
    
    def _calculate_time_decay_weight(self, interaction_time: str) -> float:
        """计算基于时间的衰减权重"""
        try:
            if not interaction_time:
                return 0.1  # 如果没有时间信息，给很小的权重
            
            # 解析时间
            if isinstance(interaction_time, str):
                interaction_time = interaction_time.replace('Z', '+00:00')
                if 'T' in interaction_time:
                    target_time = datetime.fromisoformat(interaction_time)
                else:
                    target_time = datetime.strptime(interaction_time, '%Y-%m-%d')
            else:
                target_time = interaction_time
            
            if hasattr(target_time, 'tzinfo') and target_time.tzinfo:
                target_time = target_time.replace(tzinfo=None)
            
            # 计算时间差（天）
            days_ago = (datetime.now() - target_time).days
            
            # 时间衰减权重算法
            if days_ago <= 3:          # 3天内：最高权重
                return 1.0
            elif days_ago <= 7:        # 一周内：很高权重
                return 0.9
            elif days_ago <= 30:       # 一月内：高权重
                return 0.8
            elif days_ago <= 90:       # 三月内：中等权重
                return 0.6
            elif days_ago <= 180:      # 半年内：中低权重
                return 0.4
            elif days_ago <= 365:      # 一年内：低权重
                return 0.3
            elif days_ago <= 730:      # 两年内：很低权重
                return 0.2
            else:                      # 超过两年：极低权重
                return 0.1
                
        except Exception as e:
            print(f"⚠️ 计算时间衰减权重失败: {e}")
            return 0.5  # 默认中等权重
    
    def _extract_content_keywords(self, papers: List[Dict]) -> Dict[str, float]:
        """从喜爱的论文中提取关键词（只基于内容）"""
        keyword_counts = defaultdict(int)
        total_papers = len(papers)
        
        for paper in papers:
            title = (paper['title'] or '').lower()
            abstract = (paper['abstract'] or '').lower()
            
            # 合并标题和摘要
            text = title + ' ' + abstract
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
            
            # 对标题中的词给予更高权重
            title_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', title))
            
            # 计算词频
            for word in set(words):  # 使用set避免重复计算
                if word in title_words:
                    keyword_counts[word] += 2  # 标题中的关键词权重加倍
                else:
                    keyword_counts[word] += 1
        
        # 计算关键词强度（基于出现频率）
        keyword_patterns = {}
        for word, count in keyword_counts.items():
            if count >= 2:  # 至少在2篇文章中出现
                # 强度 = 出现次数 / 总文章数
                strength = min(1.0, count / total_papers)
                keyword_patterns[word] = strength
        
        # 返回前30个最强的关键词
        sorted_keywords = sorted(keyword_patterns.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_keywords[:30])
    
    def _extract_preferred_authors(self, papers: List[Dict]) -> Dict[str, float]:
        """提取喜爱的作者（只基于出现频率）"""
        author_counts = defaultdict(int)
        total_papers = len(papers)
        
        for paper in papers:
            authors = paper['authors'] or ''
            # 分割作者名
            author_list = [author.strip() for author in authors.split(',')]
            
            for author in author_list:
                if len(author) > 2:  # 过滤太短的名字
                    author_counts[author] += 1
        
        # 计算作者偏好强度
        author_patterns = {}
        for author, count in author_counts.items():
            if count >= 2:  # 至少关注过该作者2篇论文
                strength = min(1.0, count / total_papers)
                author_patterns[author] = strength
        
        return author_patterns
    
    def _extract_preferred_journals(self, papers: List[Dict]) -> Dict[str, float]:
        """提取喜爱的期刊（只基于出现频率）"""
        journal_counts = defaultdict(int)
        total_papers = len(papers)
        
        for paper in papers:
            journal = paper['journal'] or ''
            if journal:
                journal_counts[journal] += 1
        
        # 计算期刊偏好强度
        journal_patterns = {}
        for journal, count in journal_counts.items():
            if count >= 1:  # 期刊只需要1篇即可
                strength = min(1.0, count / total_papers)
                journal_patterns[journal] = strength
        
        return journal_patterns
    
    def _find_candidate_papers(self, user_patterns: Dict) -> List[Dict]:
        """找到候选推荐论文（只基于未读状态）"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # 只获取未读的论文，不限制时间范围
            c.execute('''
                SELECT p.id, p.title, p.abstract, p.authors, p.journal, p.published_date, p.url,
                       p.created_at
                FROM papers p
                WHERE p.status = 'unread'  -- 只推荐未读论文
                AND p.id NOT IN (
                    -- 排除已明确标记为不喜欢的论文
                    SELECT DISTINCT pi.paper_id 
                    FROM paper_interactions pi 
                    WHERE pi.interaction_type = 'explicit_dislike'
                )
                ORDER BY p.created_at DESC  -- 新文章优先
                LIMIT 2000  -- 扩大候选池
            ''')
            
            return [dict(row) for row in c.fetchall()]
            
        except Exception as e:
            print(f"❌ 查找候选论文失败: {e}")
            return []
        finally:
            conn.close()
    
    def _score_candidates(self, candidates: List[Dict], user_patterns: Dict) -> List[Dict]:
        """为候选论文计算推荐分数（纯内容匹配）"""
        scored_candidates = []
        
        keywords = user_patterns['keywords']
        authors = user_patterns['authors'] 
        journals = user_patterns['journals']
        
        for paper in candidates:
            score = 0.0
            matched_features = []
            
            title = (paper['title'] or '').lower()
            abstract = (paper['abstract'] or '').lower()
            
            # 1. 关键词内容匹配 (权重: 80%) - 主要指标
            title_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', title))
            abstract_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', abstract))
            
            keyword_score = 0.0
            matched_keywords = []
            
            for word, strength in keywords.items():
                if word in title_words:
                    keyword_score += strength * 2.0  # 标题匹配最重要
                    matched_keywords.append(f"{word}(标题)")
                elif word in abstract_words:
                    keyword_score += strength * 1.0  # 摘要匹配次之
                    matched_keywords.append(f"{word}(摘要)")
            
            score += keyword_score * 0.8
            
            if matched_keywords:
                matched_features.append(f"关键词匹配: {', '.join(matched_keywords[:3])}")
            
            # 2. 作者匹配 (权重: 15%)
            paper_authors = paper['authors'] or ''
            author_score = 0.0
            matched_authors = []
            
            for author, strength in authors.items():
                if author in paper_authors:
                    author_score += strength
                    matched_authors.append(author)
            
            score += author_score * 0.15
            
            if matched_authors:
                matched_features.append(f"喜爱作者: {', '.join(matched_authors[:2])}")
            
            # 3. 期刊匹配 (权重: 5%)
            paper_journal = paper['journal'] or ''
            journal_score = 0.0
            
            for journal, strength in journals.items():
                if journal == paper_journal:
                    journal_score = strength
                    matched_features.append(f"喜爱期刊: {journal}")
                    break
            
            score += journal_score * 0.05
            
            # 只推荐有明确匹配的论文（提高阈值）
            if score > 0.1:  # 至少要有一些内容匹配
                paper_copy = dict(paper)
                paper_copy['recommendation_score'] = round(score, 4)
                paper_copy['matched_features'] = matched_features
                paper_copy['keyword_matches'] = len(matched_keywords)
                paper_copy['author_matches'] = len(matched_authors)
                
                scored_candidates.append(paper_copy)
        
        return scored_candidates
    
    def _filter_interacted_papers(self, candidates: List[Dict]) -> List[Dict]:
        """过滤掉已经有明确交互的论文（只过滤明确行为）"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            candidate_ids = [p['id'] for p in candidates]
            if not candidate_ids:
                return []
            
            # 只过滤掉明确不喜欢或已经收藏的论文
            placeholders = ','.join(['?' for _ in candidate_ids])
            c.execute(f'''
                SELECT DISTINCT paper_id 
                FROM paper_interactions 
                WHERE paper_id IN ({placeholders})
                AND interaction_type IN ('explicit_dislike', 'explicit_like', 'bookmark')
            ''', candidate_ids)
            
            # 获取所有已交互的论文ID
            interacted_ids = {row['paper_id'] for row in c.fetchall()}
            
            # 过滤掉已有明确交互的论文——避免重复推荐
            filtered = [p for p in candidates if p['id'] not in interacted_ids]
            
            return filtered
            
        except Exception as e:
            print(f"❌ 过滤已交互论文失败: {e}")
            return candidates
        finally:
            conn.close()
    
    def _get_fallback_recommendations(self, limit: int) -> List[Dict]:
        """获取备用推荐（当无法生成个性化推荐时）"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # 随机推荐未读论文（不基于时间）
            c.execute('''
                SELECT p.id, p.title, p.abstract, p.authors, p.journal, p.published_date, p.url,
                       p.created_at, 0.5 as recommendation_score
                FROM papers p
                WHERE p.status = 'unread'  -- 只推荐未读论文
                AND p.id NOT IN (
                    -- 排除已明确标记为不喜欢的
                    SELECT DISTINCT pi.paper_id 
                    FROM paper_interactions pi 
                    WHERE pi.interaction_type = 'explicit_dislike'
                )
                ORDER BY RANDOM()  -- 随机排序，不偏向新文章
                LIMIT ?
            ''', (limit,))
            
            results = []
            for row in c.fetchall():
                paper = dict(row)
                paper['matched_features'] = ['随机推荐（暂无兴趣数据）']
                paper['keyword_matches'] = 0
                paper['author_matches'] = 0
                results.append(paper)
            
            return results
            
        except Exception as e:
            print(f"❌ 获取备用推荐失败: {e}")
            return []
        finally:
            conn.close()
    
    def find_similar_papers(self, paper_id: int, limit: int = 5) -> List[Dict]:
        """根据指定论文找相似论文（纯内容匹配）"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            # 获取目标论文信息
            c.execute('SELECT * FROM papers WHERE id = ?', (paper_id,))
            target_paper = c.fetchone()
            
            if not target_paper:
                return []
            
            target_paper = dict(target_paper)
            
            # 提取目标论文的关键词
            title = (target_paper['title'] or '').lower()
            abstract = (target_paper['abstract'] or '').lower()
            target_keywords = set(re.findall(r'\b[a-zA-Z]{4,}\b', title + ' ' + abstract))
            target_title_keywords = set(re.findall(r'\b[a-zA-Z]{4,}\b', title))
            target_authors = set((target_paper['authors'] or '').split(','))
            target_journal = target_paper['journal']
            
            # 找候选相似论文（只推荐未读的）
            c.execute('''
                SELECT * FROM papers 
                WHERE id != ? 
                AND status = 'unread'
                ORDER BY created_at DESC
                LIMIT 500
            ''', (paper_id,))
            
            candidates = [dict(row) for row in c.fetchall()]
            
            # 计算相似度（只基于内容）
            similar_papers = []
            
            for candidate in candidates:
                similarity_score = 0.0
                
                cand_title = (candidate['title'] or '').lower()
                cand_abstract = (candidate['abstract'] or '').lower()
                cand_keywords = set(re.findall(r'\b[a-zA-Z]{4,}\b', cand_title + ' ' + cand_abstract))
                cand_title_keywords = set(re.findall(r'\b[a-zA-Z]{4,}\b', cand_title))
                
                # 1. 标题关键词匹配（最重要，权重60%）
                title_overlap = len(target_title_keywords & cand_title_keywords)
                if target_title_keywords and title_overlap > 0:
                    title_similarity = title_overlap / len(target_title_keywords)
                    similarity_score += title_similarity * 0.6
                
                # 2. 全文关键词匹配（次要，权重25%）
                keyword_overlap = len(target_keywords & cand_keywords)
                if target_keywords and keyword_overlap > 0:
                    keyword_similarity = keyword_overlap / len(target_keywords)
                    similarity_score += keyword_similarity * 0.25
                
                # 3. 作者匹配（权重10%）
                cand_authors = set((candidate['authors'] or '').split(','))
                author_overlap = len(target_authors & cand_authors)
                if target_authors and author_overlap > 0:
                    similarity_score += 0.1
                
                # 4. 期刊匹配（权重5%）
                if candidate['journal'] == target_journal and target_journal:
                    similarity_score += 0.05
                
                # 只返回有意义的匹配结果
                if similarity_score > 0.1:  # 至少要有一些关键词匹配
                    candidate['similarity_score'] = round(similarity_score, 4)
                    candidate['keyword_matches'] = keyword_overlap
                    candidate['title_matches'] = title_overlap
                    similar_papers.append(candidate)
            
            # 按相似度排序返回
            similar_papers.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar_papers[:limit]
            
        except Exception as e:
            print(f"❌ 查找相似论文失败: {e}")
            return []
        finally:
            conn.close()
    
    def get_recommendation_explanation(self, paper_id: int) -> Dict:
        """解释为什么推荐这篇论文"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('SELECT * FROM papers WHERE id = ?', (paper_id,))
            paper = c.fetchone()
            
            if not paper:
                return {}
            
            paper = dict(paper)
            user_patterns = self._analyze_comprehensive_user_patterns()
            
            explanations = []
            
            # 分析匹配的关键词
            title = (paper['title'] or '').lower()
            abstract = (paper['abstract'] or '').lower()
            paper_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', title + ' ' + abstract))
            
            matched_keywords = []
            for word, strength in user_patterns['keywords'].items():
                if word in paper_words:
                    matched_keywords.append((word, strength))
            
            if matched_keywords:
                matched_keywords.sort(key=lambda x: x[1], reverse=True)
                top_keywords = [kw[0] for kw in matched_keywords[:3]]
                explanations.append(f"关键词匹配: {', '.join(top_keywords)}")
            
            # 分析匹配的作者
            paper_authors = paper['authors'] or ''
            matched_authors = []
            for author, strength in user_patterns['authors'].items():
                if author in paper_authors:
                    matched_authors.append(author)
            
            if matched_authors:
                explanations.append(f"关注的作者: {', '.join(matched_authors[:2])}")
            
            # 分析匹配的期刊
            paper_journal = paper['journal'] or ''
            if paper_journal in user_patterns['journals']:
                explanations.append(f"关注的期刊: {paper_journal}")
            
            return {
                'paper_id': paper_id,
                'paper_title': paper['title'],
                'explanations': explanations,
                'matched_keywords_count': len(matched_keywords),
                'matched_authors_count': len(matched_authors)
            }
            
        except Exception as e:
            print(f"❌ 生成推荐解释失败: {e}")
            return {}
        finally:
            conn.close()