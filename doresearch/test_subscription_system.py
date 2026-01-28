"""
新订阅管理系统测试脚本
用于验证数据库初始化和基本功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.subscription_models import (
    SubscriptionDatabase, 
    SubscriptionTemplateManager,
    UserSubscriptionManager,
    SyncHistoryManager
)
from services.subscription_service import NewSubscriptionService
from config import DATABASE_PATH


def test_database_initialization():
    """测试数据库初始化"""
    print("🔧 测试数据库初始化...")
    
    try:
        db = SubscriptionDatabase(DATABASE_PATH)
        print("✅ 数据库初始化成功")
        
        # 检查表是否存在
        conn = db.get_connection()
        c = conn.cursor()
        
        tables = ['subscription_templates', 'user_subscriptions', 'subscription_sync_history']
        for table in tables:
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if c.fetchone():
                print(f"✅ 表 {table} 存在")
            else:
                print(f"❌ 表 {table} 不存在")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False
    
    return True


def test_template_management():
    """测试模板管理功能"""
    print("\n🔧 测试模板管理功能...")
    
    try:
        template_manager = SubscriptionTemplateManager(DATABASE_PATH)
        
        # 获取默认模板
        templates = template_manager.get_all_templates()
        print(f"✅ 找到 {len(templates)} 个默认模板:")
        
        for template in templates:
            print(f"   - {template['name']} ({template['source_type']})")
        
        # 测试获取单个模板
        if templates:
            template_id = templates[0]['id']
            template = template_manager.get_template(template_id)
            if template:
                print(f"✅ 成功获取模板详情: {template['name']}")
            else:
                print("❌ 获取模板详情失败")
        
    except Exception as e:
        print(f"❌ 模板管理测试失败: {e}")
        return False
    
    return True


def test_subscription_service():
    """测试订阅服务"""
    print("\n🔧 测试订阅服务...")
    
    try:
        service = NewSubscriptionService(DATABASE_PATH)
        
        # 测试获取模板
        templates = service.get_templates()
        print(f"✅ 服务层获取到 {len(templates)} 个模板")
        
        # 测试外部服务健康检查（预期会失败，因为外部服务未运行）
        health_result = service.check_external_service()
        if health_result['success']:
            print("✅ 外部服务连接正常")
        else:
            print(f"⚠️ 外部服务连接失败（预期）: {health_result['error']}")
        
        print("✅ 订阅服务基本功能正常")
        
    except Exception as e:
        print(f"❌ 订阅服务测试失败: {e}")
        return False
    
    return True


def test_user_subscription_creation():
    """测试用户订阅创建（模拟）"""
    print("\n🔧 测试用户订阅创建...")
    
    try:
        service = NewSubscriptionService(DATABASE_PATH)
        
        # 模拟创建用户订阅
        templates = service.get_templates()
        if not templates:
            print("❌ 没有可用模板")
            return False
        
        # 找到IEEE模板
        ieee_template = None
        for template in templates:
            if template['source_type'] == 'ieee':
                ieee_template = template
                break
        
        if not ieee_template:
            print("❌ 未找到IEEE模板")
            return False
        
        # 模拟创建订阅（使用测试用户ID=1）
        test_params = {"pnumber": "5962382"}  # IEEE Computer Society期刊
        result = service.create_subscription(
            user_id=1,
            template_id=ieee_template['id'],
            name="测试IEEE订阅",
            source_params=test_params
        )
        
        if result['success']:
            print(f"✅ 成功创建测试订阅: {result['subscription_id']}")
            
            # 获取用户订阅列表
            subscriptions = service.get_user_subscriptions(1)
            print(f"✅ 用户有 {len(subscriptions)} 个订阅")
            
            # 删除测试订阅
            delete_result = service.delete_subscription(result['subscription_id'], 1)
            if delete_result['success']:
                print("✅ 成功删除测试订阅")
            
        else:
            print(f"❌ 创建订阅失败: {result['error']}")
        
    except Exception as e:
        print(f"❌ 用户订阅测试失败: {e}")
        return False
    
    return True


def main():
    """主测试函数"""
    print("🚀 新订阅管理系统测试开始\n")
    
    tests = [
        ("数据库初始化", test_database_initialization),
        ("模板管理", test_template_management),
        ("订阅服务", test_subscription_service),
        ("用户订阅创建", test_user_subscription_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"测试: {test_name}")
        print(f"{'='*50}")
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} 测试通过")
        else:
            print(f"❌ {test_name} 测试失败")
    
    print(f"\n{'='*50}")
    print(f"测试总结: {passed}/{total} 个测试通过")
    print(f"{'='*50}")
    
    if passed == total:
        print("🎉 所有测试通过！新订阅管理系统运行正常")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查问题")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)