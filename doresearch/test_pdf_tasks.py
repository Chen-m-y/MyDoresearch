#!/usr/bin/env python3
"""
测试PDF抓取任务记录功能
"""
import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:5000"
TEST_PAPER_ID = 123
TEST_ARTICLE_NUMBER = "9123456"

def test_create_pdf_download_task():
    """测试创建PDF下载任务"""
    print("=== 测试创建PDF下载任务 ===")
    
    url = f"{BASE_URL}/api/download/pdf"
    data = {
        "paper_id": TEST_PAPER_ID,
        "article_number": TEST_ARTICLE_NUMBER,
        "priority": 8
    }
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"创建任务成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result.get('task_id')
        else:
            print(f"创建任务失败: {response.text}")
            return None
    
    except Exception as e:
        print(f"请求异常: {e}")
        return None

def test_list_tasks():
    """测试获取任务列表"""
    print("\n=== 测试获取任务列表 ===")
    
    url = f"{BASE_URL}/api/tasks"
    
    try:
        response = requests.get(url)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            tasks = response.json()
            print(f"任务列表 (共{len(tasks)}个):")
            for task in tasks:
                print(f"  - 任务ID: {task['id']}")
                print(f"    类型: {task['task_type']} - {task.get('task_type_desc', '')} {task.get('task_type_icon', '')}")
                print(f"    状态: {task['status']}")
                print(f"    论文ID: {task['paper_id']}")
                if 'metadata' in task and task['metadata']:
                    if 'article_number' in task['metadata']:
                        print(f"    文章号: {task['metadata']['article_number']}")
                    if 'task_description' in task['metadata']:
                        print(f"    描述: {task['metadata']['task_description']}")
                print(f"    创建时间: {task.get('created_at', 'N/A')}")
                if 'steps' in task:
                    print(f"    步骤数: {len(task['steps'])}")
                elif 'steps_count' in task:
                    print(f"    步骤数: {task['steps_count']}")
                print()
        else:
            print(f"获取任务列表失败: {response.text}")
    
    except Exception as e:
        print(f"请求异常: {e}")

def test_filter_tasks():
    """测试任务筛选功能"""
    print("\n=== 测试任务筛选功能 ===")
    
    # 测试按类型筛选
    print("1. 筛选仅下载PDF任务:")
    try:
        response = requests.get(f"{BASE_URL}/api/tasks?task_type=pdf_download_only&include_steps=false")
        if response.status_code == 200:
            tasks = response.json()
            print(f"找到 {len(tasks)} 个PDF下载任务")
            for task in tasks:
                print(f"  - {task['id']}: {task['task_type']} ({task.get('task_type_desc', '')})")
        else:
            print(f"筛选失败: {response.text}")
    except Exception as e:
        print(f"筛选异常: {e}")
    
    print("\n2. 筛选完整分析任务:")
    try:
        response = requests.get(f"{BASE_URL}/api/tasks?task_type=full_analysis&include_steps=false")
        if response.status_code == 200:
            tasks = response.json()
            print(f"找到 {len(tasks)} 个完整分析任务")
            for task in tasks:
                print(f"  - {task['id']}: {task['task_type']} ({task.get('task_type_desc', '')})")
        else:
            print(f"筛选失败: {response.text}")
    except Exception as e:
        print(f"筛选异常: {e}")
    
    print("\n3. 筛选待处理任务:")
    try:
        response = requests.get(f"{BASE_URL}/api/tasks?status=pending&include_steps=false")
        if response.status_code == 200:
            tasks = response.json()
            print(f"找到 {len(tasks)} 个待处理任务")
            for task in tasks:
                print(f"  - {task['id']}: {task['status']} - {task['task_type']}")
        else:
            print(f"筛选失败: {response.text}")
    except Exception as e:
        print(f"筛选异常: {e}")

def test_get_task_details(task_id):
    """测试获取任务详情"""
    if not task_id:
        print("\n=== 跳过任务详情测试 (无task_id) ===")
        return
    
    print(f"\n=== 测试获取任务详情 (ID: {task_id}) ===")
    
    url = f"{BASE_URL}/api/tasks/{task_id}"
    
    try:
        response = requests.get(url)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            task = response.json()
            print(f"任务详情: {json.dumps(task, indent=2, ensure_ascii=False)}")
        else:
            print(f"获取任务详情失败: {response.text}")
    
    except Exception as e:
        print(f"请求异常: {e}")

def test_full_analysis_task():
    """测试创建完整分析任务"""
    print("\n=== 测试创建完整分析任务 ===")
    
    url = f"{BASE_URL}/api/tasks/analysis"
    data = {
        "paper_id": TEST_PAPER_ID + 2,
        "priority": 7
    }
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"完整分析任务结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"创建完整分析任务失败: {response.text}")
    
    except Exception as e:
        print(f"请求异常: {e}")

def test_async_download():
    """测试异步下载API（已集成任务记录）"""
    print("\n=== 测试异步下载API ===")
    
    url = f"{BASE_URL}/api/download/async"
    data = {
        "paper_id": TEST_PAPER_ID + 1,
        "article_number": "9654321",
        "priority": 6
    }
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"异步下载结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"异步下载失败: {response.text}")
    
    except Exception as e:
        print(f"请求异常: {e}")

def test_task_types_validation():
    """测试任务类型区分和验证"""
    print("\n=== 测试任务类型区分 ===")
    
    # 测试仅下载PDF任务
    print("1. 创建仅下载PDF任务:")
    test_create_pdf_download_task()
    
    # 测试完整分析任务
    print("\n2. 创建完整分析任务:")
    test_full_analysis_task()
    
    # 检查任务列表中的类型
    time.sleep(1)
    test_list_tasks()

def main():
    """主测试函数"""
    print("开始测试任务创建和类型区分功能...")
    
    # 测试1: 创建PDF下载任务（仅下载）
    print("\n" + "="*50)
    task_id = test_create_pdf_download_task()
    
    # 测试2: 创建完整分析任务
    print("\n" + "="*50)
    test_full_analysis_task()
    
    # 测试3: 异步下载API
    print("\n" + "="*50)
    test_async_download()
    
    # 等待一秒
    time.sleep(1)
    
    # 测试4: 获取任务列表，查看任务类型区分
    print("\n" + "="*50)
    test_list_tasks()
    
    # 测试5: 获取任务详情
    print("\n" + "="*50)
    test_get_task_details(task_id)
    
    # 测试6: 任务类型验证
    print("\n" + "="*50)
    test_task_types_validation()
    
    # 测试7: 任务筛选功能
    print("\n" + "="*50)
    test_filter_tasks()
    
    print("\n" + "="*50)
    print("✅ 所有测试完成!")
    print("📋 验证要点:")
    print("  - 每个任务都有唯一的UUID")
    print("  - 任务类型明确区分(pdf_download_only, full_analysis等)")
    print("  - API响应包含完整的任务信息(类型描述、图标、元数据)")
    print("  - 任务列表正确显示所有任务类型")
    print("  - 支持按状态和类型筛选任务")
    print("  - 支持性能优化的include_steps参数")

if __name__ == "__main__":
    main()