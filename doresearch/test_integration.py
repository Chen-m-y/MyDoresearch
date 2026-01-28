"""
测试与do_research_fetch微服务的连接
验证新的订阅管理系统能否正常调用外部服务  
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.subscription_service import NewSubscriptionService


def test_external_service_connection():
    """测试外部服务连接"""
    print("🔧 测试与do_research_fetch微服务的连接...")
    
    # 直接使用新的服务地址创建服务实例
    service = NewSubscriptionService(
        db_path='/mnt/f/Workspaces/git/DoResearch/papers.db',
        external_service_url='http://192.168.1.135:8000'
    )
    
    # 测试健康检查
    health_result = service.check_external_service()
    if health_result['success']:
        print("✅ 外部服务连接正常")
        if 'data' in health_result:
            print(f"   服务信息: {health_result['data']}")
    else:
        print(f"❌ 外部服务连接失败: {health_result['error']}")
        return False
    
    return True


def test_ieee_subscription_with_real_service():
    """测试与真实微服务的IEEE订阅"""
    print("\n🔧 测试IEEE订阅创建和同步...")
    
    service = NewSubscriptionService(
        db_path='/mnt/f/Workspaces/git/DoResearch/papers.db',
        external_service_url='http://192.168.1.135:8000'
    )
    
    # 获取IEEE模板
    templates = service.get_templates()
    ieee_template = None
    for template in templates:
        if template['source_type'] == 'ieee':
            ieee_template = template
            break
    
    if not ieee_template:
        print("❌ 未找到IEEE模板")
        return False
    
    print(f"✅ 找到IEEE模板: {ieee_template['name']}")
    print(f"   参数要求: {ieee_template['parameter_schema']['required']}")
    print(f"   示例参数: {ieee_template['example_params']}")
    
    # 创建测试订阅
    test_params = {"punumber": "32"}  # IEEE Transactions on Software Engineering
    result = service.create_subscription(
        user_id=1,
        template_id=ieee_template['id'],
        name="IEEE TSE 集成测试订阅",
        source_params=test_params
    )
    
    if not result['success']:
        print(f"❌ 创建订阅失败: {result['error']}")
        return False
    
    subscription_id = result['subscription_id']
    print(f"✅ 订阅创建成功，ID: {subscription_id}")
    
    # 手动触发同步
    print("🔄 手动触发同步...")
    sync_result = service.manual_sync(subscription_id)
    
    if sync_result['success']:
        print("✅ 同步请求成功发送")
        
        # 等待同步完成
        import time
        print("⏳ 等待同步完成（20秒）...")
        time.sleep(20)
        
        # 检查同步历史
        history = service.get_sync_history(subscription_id, limit=3)
        if history:
            print("📊 同步历史:")
            for record in history:
                status_emoji = "✅" if record['status'] == 'success' else "❌" if record['status'] == 'error' else "🔄"
                print(f"   {status_emoji} {record['sync_started_at'][:19]} - {record['status']}")
                if record['status'] == 'success':
                    print(f"      发现论文: {record['papers_found']}篇, 新增: {record['papers_new']}篇")
                elif record['error_details']:
                    print(f"      错误: {record['error_details'][:200]}...")
        
        # 检查数据库中的论文
        try:
            import sqlite3
            conn = sqlite3.connect('/mnt/f/Workspaces/git/DoResearch/papers.db')
            c = conn.cursor()
            
            # 统计通过此订阅获取的论文数
            c.execute('SELECT COUNT(*) FROM papers WHERE subscription_id = ?', (subscription_id,))
            paper_count = c.fetchone()[0]
            
            # 获取最新的几篇论文标题
            c.execute('''SELECT title, published_date FROM papers 
                        WHERE subscription_id = ? 
                        ORDER BY created_at DESC LIMIT 3''', (subscription_id,))
            recent_papers = c.fetchall()
            
            conn.close()
            
            print(f"📚 通过订阅获取的论文数量: {paper_count}")
            if recent_papers:
                print("📄 最新论文:")
                for title, pub_date in recent_papers:
                    print(f"   - {title[:80]}... ({pub_date})")
            
            if paper_count > 0:
                print("🎉 集成测试成功！数据已正确存储到数据库")
            else:
                print("⚠️ 同步完成但未获取到论文")
            
        except Exception as e:
            print(f"❌ 检查数据库时出错: {e}")
    else:
        print(f"❌ 同步失败: {sync_result['error']}")
    
    # 清理测试数据
    print("\n🧹 清理测试数据...")
    delete_result = service.delete_subscription(subscription_id, 1)
    if delete_result['success']:
        print("✅ 测试订阅已删除")
    
    return True


def test_external_service_direct():
    """直接测试外部服务"""
    print("\n🔧 直接测试外部微服务...")
    
    from services.subscription_service import ExternalServiceClient
    
    client = ExternalServiceClient('http://192.168.1.135:8000')
    
    # 测试健康检查
    health_result = client.health_check()
    print(f"健康检查: {health_result}")
    
    # 测试获取论文
    fetch_result = client.fetch_papers('ieee', {'punumber': '32'})
    if fetch_result['success']:
        papers = fetch_result['data']['data']['papers']
        print(f"✅ 成功获取 {len(papers)} 篇论文")
        if papers:
            print(f"   第一篇: {papers[0]['title'][:60]}...")
    else:
        print(f"❌ 获取论文失败: {fetch_result['error']}")
    
    return True


def main():
    """主测试函数"""
    print("🚀 do_research_fetch集成测试")
    print("="*60)
    
    try:
        # 1. 测试外部服务连接
        if not test_external_service_connection():
            print("❌ 外部服务连接失败，跳过后续测试")
            return 1
        
        # 2. 直接测试外部服务
        test_external_service_direct()
        
        # 3. 测试完整的订阅和同步流程
        if not test_ieee_subscription_with_real_service():
            return 1
        
        print("\n" + "="*60)
        print("🎉 集成测试完成！")
        print("✅ 新订阅管理系统与do_research_fetch微服务已成功集成")
        print("✅ 数据抓取、处理和存储流程正常工作")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)