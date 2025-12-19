"""
录制辅助工具
提供Playwright Codegen的使用指南和辅助脚本
"""
import subprocess
import sys
from pathlib import Path


def start_codegen(url: str = "http://localhost:3000", output_file: str = None):
    """启动Playwright Codegen录制
    
    Args:
        url: 目标URL
        output_file: 输出文件路径（可选）
    """
    cmd = ['playwright', 'codegen', url]
    
    if output_file:
        cmd.extend(['--target', 'python-async', '--output', output_file])
    else:
        cmd.extend(['--target', 'python-async'])
    
    try:
        subprocess.run(cmd, check=True)
        print(f"录制完成！代码已保存到: {output_file or '剪贴板'}")
    except subprocess.CalledProcessError as e:
        print(f"录制失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("错误: 未找到playwright命令，请先安装Playwright:")
        print("  pip install playwright")
        print("  playwright install")
        sys.exit(1)


def generate_recording_template(module_name: str, test_name: str):
    """生成录制用例模板
    
    Args:
        module_name: 模块名称（如：teaching, exam, exercise）
        test_name: 测试用例名称
    """
    template = f'''"""
{test_name} - 录制生成的测试用例
"""
import pytest
from pages.desktop_page import DesktopPage
from pages.{module_name}_app import {module_name.capitalize()}App


@pytest.mark.{module_name}
class Test{test_name.replace(" ", "")}:
    """{test_name}测试类"""
    
    @pytest.mark.asyncio
    async def test_{test_name.lower().replace(" ", "_")}(self, desktop: DesktopPage, driver):
        """{test_name}测试用例"""
        try:
            # TODO: 在这里添加录制生成的代码
            pass
        except Exception as e:
            await driver.skip_step(f"测试失败: {{e}}")
            raise
'''
    
    # 保存到对应的模块目录
    module_dir = Path(f"test_cases/{module_name}")
    module_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = module_dir / f"test_{test_name.lower().replace(' ', '_')}.py"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"模板已生成: {file_path}")
    print("请使用Playwright Codegen录制操作步骤，然后将代码复制到此文件中")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Playwright录制辅助工具')
    parser.add_argument('action', choices=['record', 'template'], help='操作类型')
    parser.add_argument('--url', default='http://localhost:3000', help='目标URL')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--module', help='模块名称（用于生成模板）')
    parser.add_argument('--test-name', help='测试用例名称（用于生成模板）')
    
    args = parser.parse_args()
    
    if args.action == 'record':
        start_codegen(args.url, args.output)
    elif args.action == 'template':
        if not args.module or not args.test_name:
            print("错误: 生成模板需要 --module 和 --test-name 参数")
            sys.exit(1)
        generate_recording_template(args.module, args.test_name)

