#!/usr/bin/env python3
"""
调试read_later字段返回null的问题
"""
import sqlite3
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(__file__))

from config import DATABASE_PATH

def check_read_later_data(paper_id):
    """检查指定论文的read_later数据"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 1. 检查论文是否存在
    c.execute('SELECT id, title, status FROM papers WHERE id = ?', (paper_id,))
    paper = c.fetchone()
    
    if not paper:
        print(f"❌ 论文ID {paper_id} 不存在")
        return
    
    print(f"✅ 论文ID {paper_id} 存在:")
    print(f"   标题: {paper['title']}")
    print(f"   状态: {paper['status']}")
    
    # 2. 检查read_later表中的记录
    c.execute('SELECT * FROM read_later WHERE paper_id = ?', (paper_id,))
    read_later_records = c.fetchall()
    
    print(f"\n📋 read_later表中的记录:")
    if not read_later_records:
        print("   ❌ 没有找到read_later记录")
    else:
        for record in read_later_records:
            print(f"   记录ID: {record['id']}")
            print(f"   用户ID: {record['user_id']}")
            print(f"   论文ID: {record['paper_id']}")
            print(f"   标记时间: {record['marked_at']}")
            print(f"   优先级: {record['priority']}")
            print(f"   备注: {record['notes']}")
            print(f"   标签: {record['tags']}")
            print("   ---")
    
    # 3. 检查用户表
    c.execute('SELECT id, username, email FROM users')
    users = c.fetchall()
    
    print(f"\n👥 系统中的用户:")
    for user in users:
        print(f"   用户ID: {user['id']}, 用户名: {user['username']}, 邮箱: {user['email']}")
    
    # 4. 模拟get_paper方法的查询逻辑
    user_id = 1  # 假设用户ID为1
    print(f"\n🔍 模拟get_paper查询 (user_id={user_id}):")
    
    c.execute('SELECT * FROM read_later WHERE paper_id = ? AND user_id = ?', (paper_id, user_id))
    read_later_with_user = c.fetchone()
    
    if read_later_with_user:
        print("   ✅ 找到匹配的read_later记录:")
        print(f"   {dict(read_later_with_user)}")
    else:
        print("   ❌ 没有找到匹配的read_later记录 (用户ID不匹配？)")
    
    conn.close()

if __name__ == "__main__":
    paper_id = 2601
    if len(sys.argv) > 1:
        paper_id = int(sys.argv[1])
    
    print(f"🔍 调试论文ID {paper_id} 的read_later字段问题")
    print(f"📂 数据库路径: {DATABASE_PATH}")
    
    check_read_later_data(paper_id)