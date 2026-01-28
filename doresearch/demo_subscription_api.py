"""
新订阅管理系统演示脚本
展示如何通过API创建和管理订阅
"""
import requests
import json
import time
from typing import Dict, Any, Optional


class SubscriptionAPIDemo:
    """订阅管理API演示客户端"""
    
    def __init__(self, base_url: str = "http://localhost:5000", 
                 auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # 设置认证头（如果需要）
        if auth_token:
            self.session.headers.update({
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json'
            })
        else:
            # 简化演示，假设有session或cookie认证
            self.session.headers.update({'Content-Type': 'application/json'})
    
    def get_templates(self) -> Dict[str, Any]:
        """获取可用的订阅模板"""
        print("📋 获取订阅模板...")
        response = self.session.get(f"{self.base_url}/api/v2/subscription-templates")
        result = response.json()
        
        if result['success']:
            templates = result['data']
            print(f"✅ 找到 {len(templates)} 个模板:")
            for template in templates:
                print(f"   - {template['name']} ({template['source_type']})")
                print(f"     描述: {template['description']}")
        else:
            print(f"❌ 获取模板失败: {result['error']}")
        
        return result
    
    def create_ieee_subscription(self, name: str, pnumber: str) -> Dict[str, Any]:
        """创建IEEE期刊订阅"""
        print(f"\n📝 创建IEEE订阅: {name}")
        
        # 首先获取IEEE模板ID
        templates_result = self.get_templates()
        if not templates_result['success']:
            return templates_result
        
        ieee_template = None
        for template in templates_result['data']:
            if template['source_type'] == 'ieee':
                ieee_template = template
                break
        
        if not ieee_template:
            return {'success': False, 'error': '未找到IEEE模板'}
        
        # 创建订阅
        subscription_data = {
            'template_id': ieee_template['id'],
            'name': name,
            'source_params': {'pnumber': pnumber}
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v2/subscriptions",
            json=subscription_data
        )
        result = response.json()
        
        if result['success']:
            print(f"✅ 订阅创建成功，ID: {result['subscription_id']}")
        else:
            print(f"❌ 订阅创建失败: {result['error']}")
        
        return result
    
    def create_dblp_subscription(self, name: str, dblp_id: str, year: int) -> Dict[str, Any]:
        """创建DBLP会议订阅"""
        print(f"\n📝 创建DBLP会议订阅: {name}")
        
        # 获取DBLP模板
        templates_result = self.session.get(f"{self.base_url}/api/v2/subscription-templates").json()
        if not templates_result['success']:
            return templates_result
        
        dblp_template = None
        for template in templates_result['data']:
            if template['source_type'] == 'dblp':
                dblp_template = template
                break
        
        if not dblp_template:
            return {'success': False, 'error': '未找到DBLP模板'}
        
        # 创建订阅
        subscription_data = {
            'template_id': dblp_template['id'],
            'name': name,
            'source_params': {'dblp_id': dblp_id, 'year': year}
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v2/subscriptions",
            json=subscription_data
        )
        result = response.json()
        
        if result['success']:
            print(f"✅ 会议订阅创建成功，ID: {result['subscription_id']}")
        else:
            print(f"❌ 会议订阅创建失败: {result['error']}")
        
        return result
    
    def list_subscriptions(self) -> Dict[str, Any]:
        """获取用户订阅列表"""
        print("\n📋 获取订阅列表...")
        response = self.session.get(f"{self.base_url}/api/v2/subscriptions")
        result = response.json()
        
        if result['success']:
            subscriptions = result['data']
            print(f"✅ 找到 {len(subscriptions)} 个订阅:")
            for sub in subscriptions:
                print(f"   - [{sub['id']}] {sub['name']} ({sub['source_type']})")
                print(f"     状态: {sub['status']}, 参数: {sub['source_params']}")
                if sub['last_sync_at']:
                    print(f"     最后同步: {sub['last_sync_at']}")
        else:
            print(f"❌ 获取订阅列表失败: {result['error']}")
        
        return result
    
    def manual_sync(self, subscription_id: int) -> Dict[str, Any]:
        """手动触发同步"""
        print(f"\n🔄 手动同步订阅 {subscription_id}...")
        response = self.session.post(f"{self.base_url}/api/v2/subscriptions/{subscription_id}/sync")
        result = response.json()
        
        if result['success']:
            print(f"✅ 同步请求已发送: {result['message']}")
        else:
            print(f"❌ 同步请求失败: {result['error']}")
        
        return result
    
    def get_sync_history(self, subscription_id: int) -> Dict[str, Any]:
        """获取同步历史"""
        print(f"\n📊 获取订阅 {subscription_id} 的同步历史...")
        response = self.session.get(f"{self.base_url}/api/v2/subscriptions/{subscription_id}/history")
        result = response.json()
        
        if result['success']:
            history = result['data']
            print(f"✅ 找到 {len(history)} 条同步记录:")
            for record in history[:5]:  # 显示最近5条
                status_emoji = "✅" if record['status'] == 'success' else "❌"
                print(f"   {status_emoji} {record['sync_started_at'][:19]}")
                print(f"      状态: {record['status']}, 发现: {record['papers_found']}篇, 新增: {record['papers_new']}篇")
                if record['error_details']:
                    print(f"      错误: {record['error_details']}")
        else:
            print(f"❌ 获取同步历史失败: {result['error']}")
        
        return result
    
    def get_subscription_papers(self, subscription_id: int, limit: int = 5) -> Dict[str, Any]:
        """获取订阅的论文"""
        print(f"\n📚 获取订阅 {subscription_id} 的论文...")
        response = self.session.get(
            f"{self.base_url}/api/v2/subscriptions/{subscription_id}/papers",
            params={'per_page': limit}
        )
        result = response.json()
        
        if result['success']:
            papers = result['data']['papers']
            pagination = result['data']['pagination']
            print(f"✅ 找到 {pagination['total']} 篇论文，显示前 {len(papers)} 篇:")
            for paper in papers:
                print(f"   - {paper['title'][:80]}...")
                print(f"     期刊: {paper['journal']}, 状态: {paper['status']}")
                print(f"     发表日期: {paper['published_date']}")
        else:
            print(f"❌ 获取论文失败: {result['error']}")
        
        return result
    
    def update_subscription(self, subscription_id: int, **updates) -> Dict[str, Any]:
        """更新订阅配置"""
        print(f"\n✏️ 更新订阅 {subscription_id}...")
        response = self.session.put(
            f"{self.base_url}/api/v2/subscriptions/{subscription_id}",
            json=updates
        )
        result = response.json()
        
        if result['success']:
            print("✅ 订阅更新成功")
        else:
            print(f"❌ 订阅更新失败: {result['error']}")
        
        return result
    
    def delete_subscription(self, subscription_id: int) -> Dict[str, Any]:
        """删除订阅"""
        print(f"\n🗑️ 删除订阅 {subscription_id}...")
        response = self.session.delete(f"{self.base_url}/api/v2/subscriptions/{subscription_id}")
        result = response.json()
        
        if result['success']:
            print("✅ 订阅删除成功")
        else:
            print(f"❌ 订阅删除失败: {result['error']}")
        
        return result


def demo_admin_apis(base_url: str = "http://localhost:5000"):
    """演示管理员API"""
    print("\n" + "="*60)
    print("🔧 管理员API演示")
    print("="*60)
    
    session = requests.Session()
    session.headers.update({'Content-Type': 'application/json'})
    
    # 检查外部服务状态
    print("\n🔍 检查外部微服务状态...")
    try:
        response = session.get(f"{base_url}/api/admin/external-service/health")
        result = response.json()
        if result['success']:
            print("✅ 外部服务运行正常")
            print(f"   服务信息: {result['data']}")
        else:
            print(f"⚠️ 外部服务连接失败: {result['error']}")
    except Exception as e:
        print(f"⚠️ 无法连接管理API: {e}")
    
    # 获取订阅统计
    print("\n📊 获取系统统计...")
    try:
        response = session.get(f"{base_url}/api/admin/subscriptions/stats")
        result = response.json()
        if result['success']:
            stats = result['data']
            print("✅ 系统统计:")
            print(f"   总订阅数: {stats['total_subscriptions']}")
            print(f"   活跃订阅: {stats['active_subscriptions']}")
            print(f"   按源类型分布: {stats['by_source_type']}")
            print(f"   24小时同步次数: {stats['syncs_last_24h']}")
            print(f"   同步成功率: {stats['success_rate']}%")
        else:
            print(f"❌ 获取统计失败: {result['error']}")
    except Exception as e:
        print(f"⚠️ 无法获取统计信息: {e}")


def main():
    """主演示函数"""
    print("🚀 新订阅管理系统API演示")
    print("="*60)
    
    # 初始化演示客户端
    demo = SubscriptionAPIDemo()
    
    try:
        # 1. 获取可用模板
        demo.get_templates()
        
        # 2. 创建IEEE期刊订阅
        ieee_result = demo.create_ieee_subscription(
            "IEEE Computer Society 演示订阅",
            "5962382"  # IEEE Computer Society期刊
        )
        
        # 3. 创建DBLP会议订阅
        dblp_result = demo.create_dblp_subscription(
            "ICSE 2024 演示订阅",
            "icse",
            2024
        )
        
        # 4. 获取订阅列表
        subscriptions_result = demo.list_subscriptions()
        
        if subscriptions_result['success'] and subscriptions_result['data']:
            # 选择第一个订阅进行后续操作
            first_sub = subscriptions_result['data'][0]
            subscription_id = first_sub['id']
            
            # 5. 手动触发同步（这会失败，因为外部服务未运行）
            demo.manual_sync(subscription_id)
            
            # 6. 获取同步历史
            demo.get_sync_history(subscription_id)
            
            # 7. 获取订阅的论文
            demo.get_subscription_papers(subscription_id)
            
            # 8. 更新订阅配置
            demo.update_subscription(
                subscription_id,
                name="更新的订阅名称",
                sync_frequency=43200  # 12小时
            )
            
            # 9. 最后删除演示订阅
            print(f"\n⚠️ 即将删除演示订阅 {subscription_id}...")
            time.sleep(2)
            demo.delete_subscription(subscription_id)
        
        # 演示管理员API
        demo_admin_apis()
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        print("💡 请确保DoResearch服务正在运行")
    
    print("\n" + "="*60)
    print("🎉 API演示完成!")
    print("💡 请查看完整的API文档: docs/SUBSCRIPTION_API.md")
    print("="*60)


if __name__ == "__main__":
    main()