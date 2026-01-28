"""
修复IEEE模板参数名称不匹配问题
将pnumber更新为punumber以匹配微服务接口
"""
import sqlite3
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import DATABASE_PATH

def fix_ieee_template_parameters():
    """修复IEEE模板参数"""
    print("🔧 修复IEEE模板参数名称...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    try:
        # 获取当前IEEE模板
        c.execute('SELECT id, parameter_schema, example_params FROM subscription_templates WHERE source_type = "ieee"')
        result = c.fetchone()
        
        if not result:
            print("❌ 未找到IEEE模板")
            return False
        
        template_id, old_schema_str, old_example_str = result
        
        print(f"旧参数模式: {old_schema_str}")
        print(f"旧示例参数: {old_example_str}")
        
        # 解析旧的JSON
        old_schema = json.loads(old_schema_str)
        old_example = json.loads(old_example_str)
        
        # 创建新的参数模式
        new_schema = {
            "type": "object",
            "required": ["punumber"],
            "properties": {
                "punumber": {
                    "type": "string", 
                    "description": "IEEE期刊的publication number",
                    "pattern": "^[0-9]+$"
                }
            }
        }
        
        # 创建新的示例参数
        new_example = {"punumber": "32"}  # IEEE Transactions on Software Engineering
        
        # 更新数据库
        c.execute('''UPDATE subscription_templates 
                    SET parameter_schema = ?, example_params = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?''',
                 (json.dumps(new_schema), json.dumps(new_example), template_id))
        
        conn.commit()
        
        print(f"✅ IEEE模板已更新:")
        print(f"   新参数模式: {json.dumps(new_schema)}")
        print(f"   新示例参数: {json.dumps(new_example)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_template_update():
    """验证模板更新"""
    print("\n🔍 验证模板更新...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    try:
        c.execute('SELECT name, parameter_schema, example_params FROM subscription_templates')
        templates = c.fetchall()
        
        for name, schema_str, example_str in templates:
            print(f"\n模板: {name}")
            schema = json.loads(schema_str)
            example = json.loads(example_str)
            print(f"  必需参数: {schema['required']}")
            print(f"  示例: {example}")
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
    finally:
        conn.close()

def main():
    """主函数"""
    print("🚀 修复IEEE模板参数名称")
    print("="*40)
    
    if fix_ieee_template_parameters():
        verify_template_update()
        print("\n✅ 修复完成！现在参数名称与微服务接口一致")
    else:
        print("\n❌ 修复失败")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)