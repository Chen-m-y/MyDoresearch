#!/usr/bin/env python3
"""
IEEE下载Agent - 简化版本
向后兼容性包装器，实际实现已拆分到ieee子模块中
"""

# 导入新模块的接口，保持向后兼容
from .ieee import IEEEAgent


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='IEEE下载Agent')
    parser.add_argument('--server-url', default='http://localhost:5000',
                        help='服务器URL')
    parser.add_argument('--agent-id', 
                        help='Agent ID (默认自动生成)')
    
    args = parser.parse_args()
    
    # 创建并启动Agent
    agent = IEEEAgent(
        server_url=args.server_url,
        agent_id=args.agent_id
    )
    
    try:
        agent.start()
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号")
    except Exception as e:
        print(f"❌ Agent运行异常: {e}")
    finally:
        agent.stop()


if __name__ == "__main__":
    main()