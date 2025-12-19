"""
命令行启动入口
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # 启动Web控制界面
    from web_ui.main import main
    main()

