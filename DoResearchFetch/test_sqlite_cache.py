#!/usr/bin/env python3
"""
测试SQLite摘要缓存系统
"""

import sys
import time

def test_sqlite_cache():
    """测试SQLite缓存基本功能"""
    print("🧪 Testing SQLite Abstract Cache System")
    print("=" * 50)
    
    sys.path.append('.')
    
    try:
        from utils.abstract_cache import abstract_cache, cache_abstract, get_cached_abstract, has_cached_abstract
        
        # 1. 测试缓存设置和获取
        print("\n1. Testing cache set and get...")
        test_article_id = "11121619"
        test_url = "https://ieeexplore.ieee.org/document/11121619/"
        test_title = "Advanced Smart Contract Vulnerability Detection via LLM-Powered Multi-Agent Systems"
        test_abstract = "Blockchain's inherent immutability, while transformative, creates critical security risks in smart contracts, where undetected vulnerabilities can result in irreversible financial losses. Current auditing tools and approaches often address specific vulnerability types, yet there is a need for a comprehensive solution that can detect a wide range of vulnerabilities with high accuracy."
        
        # 缓存摘要
        success = cache_abstract(test_article_id, test_url, test_title, test_abstract, "ieee")
        if success:
            print(f"✓ Cached abstract for article {test_article_id}")
        else:
            print(f"✗ Failed to cache abstract for article {test_article_id}")
            return False
        
        # 检查是否存在
        has_cache = has_cached_abstract(test_article_id, "ieee")
        print(f"✓ Has cached abstract: {has_cache}")
        
        # 获取缓存的摘要
        cached_abstract = get_cached_abstract(test_article_id, "ieee")
        if cached_abstract:
            print(f"✓ Retrieved cached abstract ({len(cached_abstract)} chars)")
            print(f"   Preview: {cached_abstract[:100]}...")
        else:
            print("✗ Failed to retrieve cached abstract")
            return False
        
        # 2. 测试缓存统计
        print("\n2. Testing cache statistics...")
        stats = abstract_cache.get_stats()
        print(f"✓ Cache stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # 3. 测试重复缓存（应该更新现有记录）
        print("\n3. Testing duplicate caching...")
        updated_abstract = test_abstract + " This is an updated version with more details about the multi-agent approach."
        success = cache_abstract(test_article_id, test_url, test_title, updated_abstract, "ieee")
        
        if success:
            updated_cached = get_cached_abstract(test_article_id, "ieee")
            if len(updated_cached) > len(test_abstract):
                print("✓ Successfully updated existing cache entry")
            else:
                print("⚠ Cache entry may not have been updated properly")
        
        # 4. 测试多个条目
        print("\n4. Testing multiple entries...")
        test_entries = [
            ("11121620", "https://ieeexplore.ieee.org/document/11121620/", "Test Paper 1", "Abstract for test paper 1 with sufficient length to pass validation."),
            ("11121621", "https://ieeexplore.ieee.org/document/11121621/", "Test Paper 2", "Abstract for test paper 2 with sufficient length to pass validation."),
            ("11121622", "https://ieeexplore.ieee.org/document/11121622/", "Test Paper 3", "Abstract for test paper 3 with sufficient length to pass validation."),
        ]
        
        for article_id, url, title, abstract in test_entries:
            cache_abstract(article_id, url, title, abstract, "ieee")
        
        # 检查最终统计
        final_stats = abstract_cache.get_stats()
        print(f"✓ Final cache entries: {final_stats['total_entries']}")
        print(f"✓ Database size: {final_stats['db_size_mb']} MB")
        
        # 5. 测试按来源获取条目
        print("\n5. Testing get entries by source...")
        ieee_entries = abstract_cache.get_entries_by_source("ieee", limit=3)
        print(f"✓ Retrieved {len(ieee_entries)} IEEE entries")
        for entry in ieee_entries:
            print(f"   - {entry.article_id}: {entry.title[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_performance():
    """测试缓存性能"""
    print("\n🚀 Testing Cache Performance")
    print("-" * 30)
    
    sys.path.append('.')
    
    try:
        from utils.abstract_cache import cache_abstract, get_cached_abstract
        
        # 测试写入性能
        print("Testing write performance...")
        start_time = time.time()
        
        for i in range(100):
            article_id = f"test_{i:04d}"
            url = f"https://example.com/document/{article_id}"
            title = f"Test Paper {i}"
            abstract = f"This is a test abstract for paper number {i}. " * 10  # 确保足够长
            
            cache_abstract(article_id, url, title, abstract, "test")
        
        write_time = time.time() - start_time
        print(f"✓ Wrote 100 entries in {write_time:.2f} seconds ({write_time*10:.1f}ms per entry)")
        
        # 测试读取性能
        print("Testing read performance...")
        start_time = time.time()
        
        hit_count = 0
        for i in range(100):
            article_id = f"test_{i:04d}"
            cached = get_cached_abstract(article_id, "test")
            if cached:
                hit_count += 1
        
        read_time = time.time() - start_time
        print(f"✓ Read 100 entries in {read_time:.2f} seconds ({read_time*10:.1f}ms per entry)")
        print(f"✓ Cache hit rate: {hit_count}/100 ({hit_count}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

if __name__ == "__main__":
    # 运行基本功能测试
    basic_success = test_sqlite_cache()
    
    # 运行性能测试
    if basic_success:
        perf_success = test_cache_performance()
        
        print("\n" + "=" * 50)
        if basic_success and perf_success:
            print("🎉 All tests passed! SQLite cache system is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")
    else:
        print("\n❌ Basic tests failed, skipping performance tests.")