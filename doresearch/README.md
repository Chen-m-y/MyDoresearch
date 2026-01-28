# DoResearch

论文阅读后台

```python
# start_ieee_agent.py - IEEE Agent启动脚本
#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from agents.ieee_agent import IEEEAgent

if __name__ == '__main__':
    agent = IEEEAgent(
        agent_id='ieee-agent-001',
        server_endpoint='http://localhost:5000',
        port=5001
    )
    
    print("🚀 启动IEEE下载Agent...")
    agent.run()
```
