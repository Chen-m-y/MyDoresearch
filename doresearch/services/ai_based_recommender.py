"""
基于DeepSeek大模型的智能推荐服务
通过语义理解进行精准的论文内容匹配推荐
"""
import json
import requests
from typing import Dict, List, Optional
from models.database import Database
from config import DATABASE_PATH, DEEPSEEK_API_KEY


class AIBasedRecommender:
    """基于DeepSeek大模型的智能推荐系统"""
    
    def __init__(self):
        self.db = Database(DATABASE_PATH)
        self.api_key = DEEPSEEK_API_KEY
        self.api_base = "https://api.deepseek.com/v1/chat/completions"
        
    def get_personalized_recommendations(self, limit: int = 10) -> List[Dict]:
        """
        获取个性化推荐论文
        使用大模型分析用户喜爱论文的语义特征，推荐相似内容
        """
        try:
            # 1. 获取用户明确喜爱的论文
            liked_papers = self._get_user_liked_papers()
            
            if not liked_papers:
                return self._get_fallback_recommendations(limit)
            
            # 2. 使用大模型分析用户兴趣
            user_interests = self._analyze_user_interests_with_ai(liked_papers)
            
            if not user_interests:
                return self._get_fallback_recommendations(limit)
            
            # 3. 获取候选论文
            candidates = self._get_candidate_papers()
            
            # 4. 使用大模型评估候选论文与用户兴趣的匹配度
            recommendations = self._score_candidates_with_ai(candidates, user_interests, limit)
            
            return recommendations
            
        except Exception as e:
            print(f"❌ 生成AI推荐失败: {e}")
            return self._get_fallback_recommendations(limit)
    
    def find_similar_papers(self, paper_id: int, limit: int = 5) -> List[Dict]:
        """
        基于指定论文找相似论文
        使用大模型进行语义相似度分析
        """
        try:
            # 获取目标论文
            target_paper = self._get_paper_by_id(paper_id)
            if not target_paper:
                return []
            
            # 获取候选论文
            candidates = self._get_candidate_papers()
            
            # 使用AI分析相似度
            similar_papers = self._find_similar_with_ai(target_paper, candidates, limit)
            
            return similar_papers
            
        except Exception as e:
            print(f"❌ AI相似论文查找失败: {e}")
            return []
    
    def _get_user_liked_papers(self) -> List[Dict]:
        """获取用户明确标记为喜爱的论文"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
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
                LIMIT 50  -- 最多分析50篇喜爱的论文
            ''')
            
            return [dict(row) for row in c.fetchall()]
            
        except Exception as e:
            print(f"❌ 获取喜爱论文失败: {e}")
            return []
        finally:
            conn.close()
    
    def _analyze_user_interests_with_ai(self, liked_papers: List[Dict]) -> Optional[str]:
        """使用AI分析用户的兴趣模式"""
        try:
            # 构建论文内容文本
            papers_text = []
            for paper in liked_papers[:10]:  # 只分析最近10篇，避免token过多
                title = paper.get('title', '')
                abstract = paper.get('abstract', '')
                if title and abstract:
                    papers_text.append(f"标题: {title}\n摘要: {abstract}")
            
            if not papers_text:
                return None
            
            # 构建AI分析prompt
            prompt = f"""请分析以下用户喜爱的论文，总结用户的研究兴趣和偏好：

{chr(10).join(papers_text)}

请用简洁的中文总结用户的核心研究兴趣、关注的技术领域、偏好的研究方法等。输出格式要求：
- 核心兴趣领域：[领域1, 领域2, ...]
- 关注技术：[技术1, 技术2, ...]  
- 研究方法偏好：[方法1, 方法2, ...]
- 应用场景：[场景1, 场景2, ...]

请保持总结简洁但准确，每个类别最多3-5个要点。"""

            # 调用DeepSeek API
            response = self._call_deepseek_api(prompt)
            return response
            
        except Exception as e:
            print(f"❌ AI兴趣分析失败: {e}")
            return None
    
    def _score_candidates_with_ai(self, candidates: List[Dict], user_interests: str, limit: int) -> List[Dict]:
        """使用AI评估候选论文与用户兴趣的匹配度"""
        try:
            recommendations = []
            
            # 分批处理候选论文，避免token限制
            batch_size = 5
            for i in range(0, min(len(candidates), 50), batch_size):  # 最多评估50篇
                batch = candidates[i:i+batch_size]
                
                # 构建论文信息
                papers_info = []
                for j, paper in enumerate(batch):
                    title = paper.get('title', '')
                    abstract = paper.get('abstract', '')
                    if title and abstract:
                        papers_info.append(f"论文{j+1}:\n标题: {title}\n摘要: {abstract}\nID: {paper['id']}")
                
                if not papers_info:
                    continue
                
                # 构建匹配度评估prompt
                prompt = f"""用户的研究兴趣：
{user_interests}

请评估以下论文与用户兴趣的匹配度：

{chr(10).join(papers_info)}

请为每篇论文打分（0-100分）并说明理由。输出JSON格式：
[
  {{"id": 论文ID, "score": 分数, "reason": "匹配理由"}},
  ...
]

评分标准：
- 90-100分：完全匹配用户核心兴趣
- 70-89分：高度相关，值得推荐
- 50-69分：部分相关，可能感兴趣
- 30-49分：略有相关
- 0-29分：不相关

只返回JSON，不要其他文字。"""

                # 调用AI评估
                response = self._call_deepseek_api(prompt)
                if response:
                    try:
                        scores = json.loads(response)
                        for score_info in scores:
                            paper_id = score_info.get('id')
                            score = score_info.get('score', 0)
                            reason = score_info.get('reason', '')
                            
                            # 找到对应的论文
                            for paper in batch:
                                if paper['id'] == paper_id and score >= 50:  # 只推荐50分以上的
                                    paper_copy = dict(paper)
                                    paper_copy['recommendation_score'] = score / 100.0
                                    paper_copy['ai_reason'] = reason
                                    recommendations.append(paper_copy)
                                    break
                    except json.JSONDecodeError:
                        print(f"⚠️ AI返回的JSON格式错误: {response}")
                        continue
            
            # 按评分排序并返回top结果
            recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            print(f"❌ AI候选论文评分失败: {e}")
            return []
    
    def _find_similar_with_ai(self, target_paper: Dict, candidates: List[Dict], limit: int) -> List[Dict]:
        """使用AI查找相似论文"""
        try:
            target_title = target_paper.get('title', '')
            target_abstract = target_paper.get('abstract', '')
            
            if not target_title or not target_abstract:
                return []
            
            similar_papers = []
            
            # 分批处理
            batch_size = 5
            for i in range(0, min(len(candidates), 30), batch_size):  # 最多评估30篇
                batch = candidates[i:i+batch_size]
                
                papers_info = []
                for j, paper in enumerate(batch):
                    title = paper.get('title', '')
                    abstract = paper.get('abstract', '')
                    if title and abstract:
                        papers_info.append(f"论文{j+1}:\n标题: {title}\n摘要: {abstract}\nID: {paper['id']}")
                
                if not papers_info:
                    continue
                
                prompt = f"""目标论文：
标题: {target_title}
摘要: {target_abstract}

请评估以下论文与目标论文的相似度：

{chr(10).join(papers_info)}

请为每篇论文评估相似度（0-100分）。输出JSON格式：
[
  {{"id": 论文ID, "similarity": 相似度分数, "reason": "相似之处"}},
  ...
]

相似度标准：
- 90-100分：主题完全相同，方法相似
- 70-89分：主题相同，方法或角度略有差异
- 50-69分：相关主题，值得参考
- 30-49分：有一定关联
- 0-29分：不相关

只返回JSON，不要其他文字。"""

                response = self._call_deepseek_api(prompt)
                if response:
                    try:
                        similarities = json.loads(response)
                        for sim_info in similarities:
                            paper_id = sim_info.get('id')
                            similarity = sim_info.get('similarity', 0)
                            reason = sim_info.get('reason', '')
                            
                            for paper in batch:
                                if paper['id'] == paper_id and similarity >= 50:
                                    paper_copy = dict(paper)
                                    paper_copy['similarity_score'] = similarity / 100.0
                                    paper_copy['similarity_reason'] = reason
                                    similar_papers.append(paper_copy)
                                    break
                    except json.JSONDecodeError:
                        continue
            
            # 排序并返回
            similar_papers.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar_papers[:limit]
            
        except Exception as e:
            print(f"❌ AI相似度分析失败: {e}")
            return []
    
    def _call_deepseek_api(self, prompt: str) -> Optional[str]:
        """调用DeepSeek API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,  # 降低随机性，提高一致性
                "max_tokens": 2000
            }
            
            response = requests.post(self.api_base, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            print(f"❌ DeepSeek API调用失败: {e}")
            return None
    
    def _get_candidate_papers(self) -> List[Dict]:
        """获取候选推荐论文"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT p.id, p.title, p.abstract, p.authors, p.journal, p.published_date, p.url,
                       p.created_at
                FROM papers p
                WHERE p.status = 'unread'  -- 只推荐未读论文
                AND p.id NOT IN (
                    -- 排除已明确标记为不喜欢的
                    SELECT DISTINCT pi.paper_id 
                    FROM paper_interactions pi 
                    WHERE pi.interaction_type = 'explicit_dislike'
                )
                AND p.id NOT IN (
                    -- 排除已经喜欢的（避免重复推荐）
                    SELECT DISTINCT pi.paper_id 
                    FROM paper_interactions pi 
                    WHERE pi.interaction_type IN ('explicit_like', 'bookmark')
                )
                AND p.abstract IS NOT NULL 
                AND LENGTH(p.abstract) > 50  -- 确保有足够的摘要信息
                ORDER BY p.created_at DESC
                LIMIT 200  -- 候选池大小
            ''')
            
            return [dict(row) for row in c.fetchall()]
            
        except Exception as e:
            print(f"❌ 获取候选论文失败: {e}")
            return []
        finally:
            conn.close()
    
    def _get_paper_by_id(self, paper_id: int) -> Optional[Dict]:
        """根据ID获取论文信息"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('SELECT * FROM papers WHERE id = ?', (paper_id,))
            result = c.fetchone()
            
            return dict(result) if result else None
            
        except Exception as e:
            print(f"❌ 获取论文失败: {e}")
            return None
        finally:
            conn.close()
    
    def _get_fallback_recommendations(self, limit: int) -> List[Dict]:
        """获取备用推荐（当AI分析失败时）"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT p.id, p.title, p.abstract, p.authors, p.journal, p.published_date, p.url,
                       p.created_at, 0.5 as recommendation_score
                FROM papers p
                WHERE p.status = 'unread'
                AND p.id NOT IN (
                    SELECT DISTINCT pi.paper_id 
                    FROM paper_interactions pi 
                    WHERE pi.interaction_type = 'explicit_dislike'
                )
                ORDER BY p.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            results = []
            for row in c.fetchall():
                paper = dict(row)
                paper['ai_reason'] = '最新论文推荐（暂无兴趣数据）'
                results.append(paper)
            
            return results
            
        except Exception as e:
            print(f"❌ 获取备用推荐失败: {e}")
            return []
        finally:
            conn.close()

    def get_user_interests_summary(self) -> Optional[str]:
        """获取用户兴趣总结（用于前端显示）"""
        try:
            liked_papers = self._get_user_liked_papers()
            if not liked_papers:
                return None
            
            return self._analyze_user_interests_with_ai(liked_papers)
            
        except Exception as e:
            print(f"❌ 获取用户兴趣总结失败: {e}")
            return None

    def explain_recommendation(self, paper_id: int) -> Dict:
        """使用AI解释为什么推荐某篇特定论文"""
        try:
            # 获取目标论文
            target_paper = self._get_paper_by_id(paper_id)
            if not target_paper:
                return {
                    'paper_id': paper_id,
                    'error': '论文不存在'
                }
            
            # 获取用户喜爱的论文
            liked_papers = self._get_user_liked_papers()
            if not liked_papers:
                return {
                    'paper_id': paper_id,
                    'paper_title': target_paper.get('title', ''),
                    'explanation': '暂无用户兴趣数据，无法生成个性化推荐解释',
                    'suggestion': '请先标记一些您喜欢的论文，系统将基于这些数据为您提供个性化推荐解释'
                }
            
            # 使用AI分析为什么推荐这篇论文
            explanation = self._generate_recommendation_explanation(target_paper, liked_papers)
            
            return {
                'paper_id': paper_id,
                'paper_title': target_paper.get('title', ''),
                'explanation': explanation,
                'analysis_method': 'AI语义分析'
            }
            
        except Exception as e:
            print(f"❌ 生成推荐解释失败: {e}")
            return {
                'paper_id': paper_id,
                'error': str(e)
            }
    
    def _generate_recommendation_explanation(self, target_paper: Dict, liked_papers: List[Dict]) -> str:
        """使用AI生成推荐解释"""
        try:
            target_title = target_paper.get('title', '')
            target_abstract = target_paper.get('abstract', '')
            
            if not target_title or not target_abstract:
                return '该论文缺少标题或摘要信息，无法进行详细分析'
            
            # 构建用户喜爱论文的简要信息
            liked_papers_info = []
            for paper in liked_papers[:5]:  # 只用前5篇避免token过多
                title = paper.get('title', '')
                if title:
                    liked_papers_info.append(f"- {title}")
            
            if not liked_papers_info:
                return '用户喜爱论文信息不完整，无法生成个性化解释'
            
            # 构建AI解释prompt
            prompt = f"""用户喜爱的论文包括：
{chr(10).join(liked_papers_info)}

现在需要解释为什么推荐以下论文：
标题: {target_title}
摘要: {target_abstract}

请分析这篇论文与用户兴趣的匹配点，解释推荐理由。要求：
1. 具体说明该论文与用户喜爱论文的相似之处
2. 指出哪些研究领域、技术方法或应用场景相匹配
3. 解释为什么这篇论文可能对用户有价值
4. 语言简洁明了，150字以内

只返回解释文字，不要其他格式。"""

            explanation = self._call_deepseek_api(prompt)
            
            if explanation:
                return explanation
            else:
                return 'AI分析暂时不可用，请稍后再试'
                
        except Exception as e:
            print(f"❌ AI解释生成失败: {e}")
            return f'生成解释时出现错误: {str(e)}'