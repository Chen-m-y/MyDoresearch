"""
基于SSE的任务处理器 - 使用统一的SSE管理器
"""
import os
import time
import threading
import requests
import base64
import re
from typing import Dict, Optional

# 使用统一的SSE管理器
from services.sse_manager import sse_manager
from services.task_manager import TaskManager
from services.agent_manager import AgentManager
from services.deepseek_analyzer import DeepSeekAnalyzer
from models.task_models import TaskStatus
from models.database import Database
from config import DATABASE_PATH, TASK_CHECK_INTERVAL, PDF_DIR, AGENT_REQUEST_TIMEOUT


class TaskProcessor:
    def __init__(self):
        self.task_manager = TaskManager()
        self.agent_manager = AgentManager()
        self.deepseek_analyzer = DeepSeekAnalyzer()
        self.db = Database(DATABASE_PATH)
        self.running = False
        self.thread = None

        # 使用统一的SSE管理器实例
        self.sse_manager = sse_manager

        print("✅ 任务处理器已初始化（使用统一SSE管理器）")

    def start(self):
        """启动任务处理器"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._process_loop, daemon=True)
            self.thread.start()
            print("📋 任务处理器已启动（SSE模式）")

    def stop(self):
        """停止任务处理器"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("📋 任务处理器已停止")

    def _process_loop(self):
        """任务处理主循环"""
        while self.running:
            try:
                # 检查传统Agent健康状态
                self.agent_manager.check_agent_health()

                # 获取待处理任务
                pending_tasks = self.task_manager.get_pending_tasks()

                if pending_tasks:
                    print(f"📋 发现 {len(pending_tasks)} 个待处理任务")

                for task in pending_tasks:
                    if not self.running:
                        break

                    try:
                        self._process_task(task)
                    except Exception as e:
                        print(f"❌ 处理任务 {task['id']} 失败: {e}")
                        self.task_manager.update_task_status(
                            task['id'],
                            TaskStatus.FAILED.value,
                            error_message=str(e)
                        )

                # 等待下次检查
                time.sleep(TASK_CHECK_INTERVAL)

            except Exception as e:
                print(f"❌ 任务处理循环出错: {e}")
                time.sleep(10)

    def _process_task(self, task: Dict):
        """处理单个任务"""
        task_id = task['id']
        paper_id = task['paper_id']
        task_type = task['task_type']

        print(f"🔄 开始处理任务: {task_id} - {task['title']}")

        # 更新任务状态为进行中
        self.task_manager.update_task_status(task_id, TaskStatus.IN_PROGRESS.value, progress=0)

        try:
            if task_type == 'deep_analysis':
                self._process_deep_analysis_task(task)
            elif task_type == 'pdf_download_only':
                self._process_pdf_download_task(task)
            elif task_type == 'full_analysis':
                self._process_full_analysis_task(task)
            elif task_type == 'pdf_download':
                # 兼容旧的pdf_download类型
                self._process_pdf_download_task(task)
            else:
                raise Exception(f"未知的任务类型: {task_type}")

        except Exception as e:
            error_msg = str(e)
            print(f"❌ 任务失败: {task_id} - {error_msg}")
            self.task_manager.update_task_status(
                task_id,
                TaskStatus.FAILED.value,
                error_message=error_msg
            )

    def _process_deep_analysis_task(self, task: Dict):
        """处理深度分析任务"""
        task_id = task['id']
        paper_id = task['paper_id']

        try:
            # 首先检查是否已经有PDF文件
            existing_pdf_path = self._check_existing_pdf(paper_id)

            if existing_pdf_path and os.path.exists(existing_pdf_path):
                print(f"📁 发现已存在的PDF文件: {existing_pdf_path}")
                self.task_manager.update_task_step(task_id, 'download_pdf', TaskStatus.COMPLETED.value, result=existing_pdf_path)

                # 读取现有PDF内容
                with open(existing_pdf_path, 'rb') as f:
                    pdf_content = f.read()

                pdf_path = existing_pdf_path
                self.task_manager.update_task_status(task_id, TaskStatus.DOWNLOADING.value, progress=33)

            else:
                # 步骤1: 下载PDF
                print(f"📥 步骤1: 下载PDF...")
                self.task_manager.update_task_step(task_id, 'download_pdf', TaskStatus.IN_PROGRESS.value)

                pdf_content = self._download_pdf(task)
                if not pdf_content:
                    raise Exception("PDF下载失败")

                self.task_manager.update_task_status(task_id, TaskStatus.DOWNLOADING.value, progress=33)

                # 保存PDF文件
                pdf_path = self._save_pdf(paper_id, pdf_content)
                self.task_manager.update_task_step(
                    task_id, 'download_pdf', TaskStatus.COMPLETED.value, result=pdf_path
                )

            # 步骤2: DeepSeek分析
            print(f"🧠 步骤2: DeepSeek深度分析...")
            self.task_manager.update_task_status(task_id, TaskStatus.ANALYZING.value, progress=66)
            self.task_manager.update_task_step(task_id, 'analyze_with_deepseek', TaskStatus.IN_PROGRESS.value)

            # 直接使用PDF内容进行分析
            analysis_result = self.deepseek_analyzer.analyze_pdf(pdf_content, task['title'])

            self.task_manager.update_task_step(
                task_id, 'analyze_with_deepseek', TaskStatus.COMPLETED.value,
                result="分析完成"
            )

            # 步骤3: 保存结果
            print(f"💾 步骤3: 保存分析结果...")
            self.task_manager.update_task_step(task_id, 'save_results', TaskStatus.IN_PROGRESS.value)

            self._save_analysis_result(paper_id, pdf_path, analysis_result)

            self.task_manager.update_task_step(task_id, 'save_results', TaskStatus.COMPLETED.value)

            # 任务完成
            self.task_manager.update_task_status(
                task_id, TaskStatus.COMPLETED.value, progress=100,
                result="深度分析完成"
            )

            print(f"✅ 任务完成: {task_id}")

        except Exception as e:
            raise Exception(f"深度分析任务失败: {e}")

    def _process_pdf_download_task(self, task: Dict):
        """处理仅PDF下载任务"""
        task_id = task['id']
        paper_id = task['paper_id']

        try:
            print(f"📥 开始仅PDF下载任务: {paper_id}")

            # 首先检查是否已经有PDF文件
            existing_pdf_path = self._check_existing_pdf(paper_id)

            if existing_pdf_path and os.path.exists(existing_pdf_path):
                print(f"📁 发现已存在的PDF文件: {existing_pdf_path}")
                self.task_manager.update_task_step(task_id, 'download_pdf', TaskStatus.COMPLETED.value, result=existing_pdf_path)
                # 任务完成
                self.task_manager.update_task_status(
                    task_id, TaskStatus.COMPLETED.value, progress=100,
                    result=f"PDF已存在: {existing_pdf_path}"
                )
            else:
                # 下载PDF
                print(f"📥 开始下载PDF...")
                self.task_manager.update_task_step(task_id, 'download_pdf', TaskStatus.IN_PROGRESS.value)
                self.task_manager.update_task_status(task_id, TaskStatus.IN_PROGRESS.value, progress=50)

                pdf_content = self._download_pdf(task)
                if not pdf_content:
                    raise Exception("PDF下载失败")

                # 保存PDF文件
                pdf_path = self._save_pdf(paper_id, pdf_content)
                
                # 更新数据库中的PDF路径
                self._update_pdf_path(paper_id, pdf_path)
                
                self.task_manager.update_task_step(
                    task_id, 'download_pdf', TaskStatus.COMPLETED.value, result=pdf_path
                )

                # 任务完成
                self.task_manager.update_task_status(
                    task_id, TaskStatus.COMPLETED.value, progress=100,
                    result=f"PDF下载完成: {pdf_path}"
                )

            print(f"✅ PDF下载任务完成: {task_id}")

        except Exception as e:
            raise Exception(f"PDF下载任务失败: {e}")

    def _process_full_analysis_task(self, task: Dict):
        """处理完整分析任务（下载PDF + AI分析）"""
        task_id = task['id']
        paper_id = task['paper_id']

        try:
            print(f"🔍 开始完整分析任务: {paper_id}")

            # 步骤1: 下载PDF（如果需要）
            existing_pdf_path = self._check_existing_pdf(paper_id)

            if existing_pdf_path and os.path.exists(existing_pdf_path):
                print(f"📁 发现已存在的PDF文件: {existing_pdf_path}")
                self.task_manager.update_task_step(task_id, 'download_pdf', TaskStatus.COMPLETED.value, result=existing_pdf_path)

                # 读取现有PDF内容
                with open(existing_pdf_path, 'rb') as f:
                    pdf_content = f.read()

                pdf_path = existing_pdf_path
                self.task_manager.update_task_status(task_id, TaskStatus.DOWNLOADING.value, progress=33)

            else:
                # 下载PDF
                print(f"📥 步骤1: 下载PDF...")
                self.task_manager.update_task_step(task_id, 'download_pdf', TaskStatus.IN_PROGRESS.value)

                pdf_content = self._download_pdf(task)
                if not pdf_content:
                    raise Exception("PDF下载失败")

                self.task_manager.update_task_status(task_id, TaskStatus.DOWNLOADING.value, progress=33)

                # 保存PDF文件
                pdf_path = self._save_pdf(paper_id, pdf_content)
                self.task_manager.update_task_step(
                    task_id, 'download_pdf', TaskStatus.COMPLETED.value, result=pdf_path
                )

            # 步骤2: AI分析
            print(f"🧠 步骤2: AI深度分析...")
            self.task_manager.update_task_status(task_id, TaskStatus.ANALYZING.value, progress=66)
            self.task_manager.update_task_step(task_id, 'analyze_with_ai', TaskStatus.IN_PROGRESS.value)

            # 使用DeepSeek分析
            analysis_result = self.deepseek_analyzer.analyze_pdf(pdf_content, task['title'])

            self.task_manager.update_task_step(
                task_id, 'analyze_with_ai', TaskStatus.COMPLETED.value,
                result="AI分析完成"
            )

            # 步骤3: 保存结果
            print(f"💾 步骤3: 保存分析结果...")
            self.task_manager.update_task_step(task_id, 'save_results', TaskStatus.IN_PROGRESS.value)

            self._save_analysis_result(paper_id, pdf_path, analysis_result)

            self.task_manager.update_task_step(task_id, 'save_results', TaskStatus.COMPLETED.value)

            # 任务完成
            self.task_manager.update_task_status(
                task_id, TaskStatus.COMPLETED.value, progress=100,
                result="完整分析完成"
            )

            print(f"✅ 完整分析任务完成: {task_id}")

        except Exception as e:
            raise Exception(f"完整分析任务失败: {e}")

    def _update_pdf_path(self, paper_id: int, pdf_path: str):
        """更新数据库中的PDF路径"""
        conn = self.db.get_connection()
        try:
            c = conn.cursor()
            c.execute('UPDATE papers SET pdf_path = ? WHERE id = ?', (pdf_path, paper_id))
            conn.commit()
            print(f"💾 已更新数据库中的PDF路径: {paper_id} -> {pdf_path}")
        finally:
            conn.close()

    def _check_existing_pdf(self, paper_id: int) -> Optional[str]:
        """检查是否已经存在PDF文件"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()

            # 查询数据库中是否已有PDF路径记录
            c.execute('SELECT pdf_path FROM papers WHERE id = ?', (paper_id,))
            result = c.fetchone()

            if result and result['pdf_path']:
                pdf_path = result['pdf_path']
                # 检查文件是否真实存在
                if os.path.exists(pdf_path):
                    file_size = os.path.getsize(pdf_path)
                    print(f"📋 数据库记录的PDF路径: {pdf_path} (大小: {file_size / 1024 / 1024:.2f}MB)")
                    return pdf_path
                else:
                    print(f"⚠️ 数据库记录的PDF文件不存在: {pdf_path}")
                    # 清除无效的路径记录
                    c.execute('UPDATE papers SET pdf_path = NULL WHERE id = ?', (paper_id,))
                    conn.commit()

            # 如果数据库中没有记录，尝试查找可能存在的文件
            possible_patterns = [
                f"paper_{paper_id}_*.pdf",
                f"ieee_*_{paper_id}.pdf",
                f"*_{paper_id}_*.pdf"
            ]

            import glob
            for pattern in possible_patterns:
                full_pattern = os.path.join(PDF_DIR, pattern)
                matching_files = glob.glob(full_pattern)

                if matching_files:
                    # 选择最新的文件
                    latest_file = max(matching_files, key=os.path.getmtime)
                    file_size = os.path.getsize(latest_file)
                    print(f"📁 发现匹配的PDF文件: {latest_file} (大小: {file_size / 1024 / 1024:.2f}MB)")

                    # 更新数据库记录
                    c.execute('UPDATE papers SET pdf_path = ? WHERE id = ?', (latest_file, paper_id))
                    conn.commit()

                    return latest_file

            conn.close()
            return None

        except Exception as e:
            print(f"⚠️ 检查现有PDF文件时出错: {e}")
            return None

    def _download_pdf(self, task: Dict) -> Optional[bytes]:
        """下载PDF文件 - 使用SSE Agent"""
        # 提取IEEE文章编号
        ieee_number = self._extract_ieee_number(task)
        if not ieee_number:
            raise Exception("无法提取IEEE文章编号")

        print(f"📄 IEEE文章编号: {ieee_number}")

        # 直接使用SSE Agent下载
        return self._download_via_sse(ieee_number)

    def _download_via_sse(self, article_number: str) -> bytes:
        """通过SSE Agent下载PDF"""
        # 调试：检查SSE Agent状态
        active_agents = self.sse_manager.get_active_agents()
        print(f"🔍 当前活跃的SSE Agent数量: {len(active_agents)}")

        for agent in active_agents:
            print(f"   - {agent['name']} ({agent['agent_id']}): {agent['capabilities']}")

        ieee_agents = [agent for agent in active_agents
                      if 'ieee_download' in agent.get('capabilities', [])]

        print(f"🔍 具有ieee_download能力的Agent数量: {len(ieee_agents)}")

        if not ieee_agents:
            # 详细诊断
            print("🔍 诊断信息:")
            print(f"   - 总Agent数: {len(active_agents)}")
            if active_agents:
                print("   - Agent详情:")
                for agent in active_agents:
                    print(f"     * {agent['agent_id']}: {agent.get('capabilities', [])}")
            else:
                print("   - 没有任何活跃的SSE Agent")

            raise Exception("没有可用的SSE IEEE下载Agent")

        agent_info = ieee_agents[0]
        print(f"🌐 使用SSE Agent下载: {agent_info['name']} ({agent_info['agent_id']})")

        # 任务提交前再次校验Agent状态
        print("🔍 任务提交前校验Agent状态...")
        current_active_agents = self.sse_manager.get_active_agents()
        current_ieee_agents = [agent for agent in current_active_agents
                              if 'ieee_download' in agent.get('capabilities', []) 
                              and agent['agent_id'] == agent_info['agent_id']]
        
        if not current_ieee_agents:
            print(f"❌ Agent {agent_info['agent_id']} 已掉线，重新查找可用Agent...")
            # 重新获取可用Agent
            current_ieee_agents = [agent for agent in current_active_agents
                                  if 'ieee_download' in agent.get('capabilities', [])]
            if not current_ieee_agents:
                raise Exception("所有IEEE下载Agent都已掉线")
            agent_info = current_ieee_agents[0]
            print(f"🔄 切换到Agent: {agent_info['name']} ({agent_info['agent_id']})")

        # 提交任务
        task_id = self.sse_manager.submit_task(
            'ieee_download',
            {'article_number': article_number},
            'ieee_download'
        )

        if not task_id:
            raise Exception("SSE任务提交失败")

        print(f"📋 SSE任务已提交: {task_id}")

        # 等待结果
        result = self.sse_manager.get_task_result(task_id, timeout=300)
        if not result:
            raise Exception("SSE任务超时或失败")

        if not result.get('success'):
            error_msg = result.get('result', {}).get('error', '未知错误')
            raise Exception(f"SSE下载失败: {error_msg}")

        # 解码PDF内容
        pdf_base64 = result.get('result', {}).get('pdf_content')
        if not pdf_base64:
            raise Exception("没有收到PDF内容")

        pdf_data = base64.b64decode(pdf_base64)
        print(f"✅ SSE PDF下载成功，大小: {len(pdf_data) / 1024 / 1024:.2f} MB")
        return pdf_data

    def _extract_ieee_number(self, task: Dict) -> Optional[str]:
        """提取IEEE文章编号"""
        # 1. 从新的metadata格式中获取
        metadata = task.get('metadata')
        if metadata and isinstance(metadata, str):
            try:
                import json
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        
        if metadata and isinstance(metadata, dict):
            article_number = metadata.get('article_number')
            if article_number:
                return article_number

        # 2. 直接从字段获取（兼容旧格式）
        ieee_number = task.get('ieee_article_number')
        if ieee_number:
            return ieee_number

        # 3. 从DOI提取
        doi = task.get('doi')
        if doi and 'ieee' in doi.lower():
            ieee_match = re.search(r'(\d+)', doi)
            if ieee_match:
                return ieee_match.group(1)

        # 4. 从URL提取
        url = task.get('url')
        if url and 'ieee' in url.lower():
            ieee_match = re.search(r'/document/(\d+)', url)
            if ieee_match:
                return ieee_match.group(1)

        return None

    def _save_pdf(self, paper_id: int, pdf_content: bytes) -> str:
        """保存PDF文件"""
        # 确保目录存在
        os.makedirs(PDF_DIR, exist_ok=True)

        # 生成文件名
        pdf_filename = f"paper_{paper_id}_{int(time.time())}.pdf"
        pdf_path = os.path.join(PDF_DIR, pdf_filename)

        # 保存文件
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)

        print(f"💾 PDF已保存: {pdf_path}")
        return pdf_path

    def _save_analysis_result(self, paper_id: int, pdf_path: str, analysis_result: str):
        """保存分析结果到数据库"""
        conn = self.db.get_connection()
        try:
            c = conn.cursor()
            c.execute('''UPDATE papers
                         SET pdf_path        = ?,
                             analysis_result = ?,
                             analysis_at     = ?
                         WHERE id = ?''',
                      (pdf_path, analysis_result, time.time(), paper_id))
            conn.commit()
            print(f"💾 分析结果已保存到数据库")
        finally:
            conn.close()

    def get_agent_status(self) -> Dict:
        """获取Agent状态（仅SSE Agent）"""
        # 获取SSE Agent状态
        sse_agents = self.sse_manager.get_active_agents()
        ieee_sse_agents = [agent for agent in sse_agents
                          if 'ieee_download' in agent.get('capabilities', [])]

        return {
            'sse_enabled': True,
            'total_agents': len(sse_agents),
            'ieee_agents': len(ieee_sse_agents),
            'active_agents': sse_agents,
            'agents': sse_agents  # 保持兼容性
        }