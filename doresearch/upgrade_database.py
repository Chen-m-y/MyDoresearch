#!/usr/bin/env python3
"""
数据库升级主脚本
简化版本，使用拆分后的模块
"""

import argparse
from database_upgrade import DatabaseUpgrader


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库升级工具')
    parser.add_argument('--db-path', default='data/papers.db',
                        help='数据库文件路径')
    parser.add_argument('--dry-run', action='store_true',
                        help='仅检查当前版本，不执行升级')
    parser.add_argument('--force', action='store_true',
                        help='强制升级（跳过确认）')

    args = parser.parse_args()

    upgrader = DatabaseUpgrader(args.db_path)

    if args.dry_run:
        # 仅检查版本
        current_version = upgrader.get_current_version()
        print(f"当前数据库版本: {current_version}")
        print(f"目标版本: {upgrader.version_info['target_version']}")

        if current_version == upgrader.version_info['target_version']:
            print("✅ 数据库已经是最新版本")
        else:
            print("🔄 需要升级")
        return

    # 确认升级
    if not args.force:
        current_version = upgrader.get_current_version()
        print(f"即将从版本 {current_version} 升级到 {upgrader.version_info['target_version']}")
        print(f"数据库路径: {args.db_path}")

        confirm = input("\n是否继续升级？(y/N): ")
        if confirm.lower() != 'y':
            print("升级已取消")
            return

    # 执行升级
    success = upgrader.run_upgrade()

    if success:
        # 显示升级摘要
        summary = upgrader.get_upgrade_summary()

        print("\n" + "=" * 60)
        print("📊 升级摘要")
        print("=" * 60)
        print(f"论文总数: {summary['total_papers']}")
        print(f"稍后阅读: {summary['read_later_count']}")
        print(f"状态类型: {summary['status_types']}")
        print(f"数据表数: {summary['table_count']}")
        print(f"索引数量: {summary['index_count']}")
        print(f"备份文件: {summary['backup_path']}")

        print("\n🎉 升级成功完成！")
        print("\n💡 新功能:")
        print("   📚 稍后阅读功能")
        print("   📊 高性能统计API")
        print("   🤖 Agent任务系统")
        print("   📝 状态变化时间记录")

    else:
        print("\n❌ 升级失败")
        backup_path = upgrader.backup_manager.get_backup_path()
        if backup_path:
            print(f"可以从备份恢复: {backup_path}")


if __name__ == "__main__":
    main()