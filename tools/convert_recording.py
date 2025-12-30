"""
Playwright录制代码自动转换工具
实习生只需要粘贴录制的代码，工具会自动转换为项目格式

使用方法：
1. 运行：python tools/convert_recording.py
2. 粘贴录制的代码
3. 选择模块（teaching/exercise/exam）
4. 输入测试用例名称
5. 工具会自动生成测试文件

@File  : convert_recording.py
@Author: shenyuan
"""
import re
import sys
from pathlib import Path


def convert_sync_to_async(code: str) -> str:
    """将同步代码转换为异步代码"""
    lines = code.split('\n')
    converted_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # 跳过空行和注释
        if not stripped or stripped.startswith('#'):
            converted_lines.append(line)
            continue
        
        # 删除浏览器相关代码和函数定义残留
        if any(keyword in stripped for keyword in [
            'browser = playwright',
            'context = browser',
            'context.close()',
            'browser.close()',
            'with sync_playwright()',
            'def run(playwright',
            'Playwright)',
            '-> None:',
            'run(playwright)',
        ]):
            continue
        
        # 删除 import re（如果只有这个import）
        if stripped == 'import re' and not any('import re' in l for l in converted_lines if l.strip()):
            continue
        
        # 处理 expect 语句
        if 'expect(' in stripped and 'await expect(' not in stripped:
            line = line.replace('expect(', 'await expect(')
        
        # 处理 page. 操作（需要加await）
        if re.search(r'\bpage\.', stripped) and 'await ' not in stripped[:stripped.find('page.')]:
            # 找到缩进
            indent = len(line) - len(line.lstrip())
            # 在 page. 前面加 await
            if 'page.' in line:
                # 检查是否已经有await
                before_page = line[:line.find('page.')]
                if 'await' not in before_page:
                    # 保持原有缩进，在前面加await
                    line = ' ' * indent + 'await ' + line.lstrip()
        
        # 处理 page = 赋值（不需要加await）
        if re.search(r'\bpage\s*=', stripped) and 'await ' not in stripped:
            # page = 赋值不需要await
            pass
        
        # 处理 content_frame 操作
        if '.content_frame.' in stripped and 'await ' not in stripped[:stripped.find('.content_frame.')]:
            indent = len(line) - len(line.lstrip())
            if 'await' not in line[:line.find('.content_frame.')]:
                line = ' ' * indent + 'await ' + line.lstrip()
        
        converted_lines.append(line)
    
    return '\n'.join(converted_lines)


def generate_test_file(module: str, test_name: str, converted_code: str, author: str = "auto") -> str:
    """生成测试文件内容"""
    
    # 模块标记映射
    mark_map = {
        'teaching': 'teaching',
        'exercise': 'exercise',
        'exam': 'exam'
    }
    
    mark = mark_map.get(module, 'teaching')
    
    # 类名：Test + 模块名首字母大写 + 测试名首字母大写
    class_name = f"Test{module.capitalize()}{test_name.replace('_', '').title().replace(' ', '')}"
    
    template = f'''"""
{module.capitalize()}模块 - {test_name}测试用例
（由录制代码自动转换生成）

@File  : test_{module}_{test_name}.py
@Author: auto
"""
import pytest
from pages.desktop_page import DesktopPage
from playwright.async_api import expect


@pytest.mark.{mark}
class {class_name}:
    """{test_name}测试类"""
    
    @pytest.mark.asyncio
    async def test_{test_name}(self, desktop: DesktopPage, driver):
        """测试{test_name}"""
        try:
            page = driver.page
            
            # ========== 自动转换的录制代码 ==========
{converted_code}
            
        except Exception as e:
            await driver.skip_step(f"测试失败: {{e}}")
            raise
'''
    
    return template


def main():
    """主函数"""
    print("=" * 60)
    print("Playwright录制代码自动转换工具")
    print("=" * 60)
    print()
    
    # 1. 选择模块
    print("请选择模块：")
    print("1. 授课教学 (teaching)")
    print("2. 攻防演练 (exercise)")
    print("3. 考试测评 (exam)")
    choice = input("请输入选项 (1/2/3，默认1): ").strip() or "1"
    
    module_map = {"1": "teaching", "2": "exercise", "3": "exam"}
    module = module_map.get(choice, "teaching")
    
    # 2. 输入测试用例名称
    test_name = input(f"\n请输入测试用例名称（例如：navigation、course_management，默认：test_{module}）: ").strip()
    if not test_name:
        test_name = f"test_{module}"
    # 移除可能的test_前缀
    test_name = test_name.replace('test_', '')
    
    # 3. 输入作者
    author = input("请输入你的名字（默认：实习生）: ").strip() or "实习生"
    
    # 4. 粘贴代码
    print("\n" + "=" * 60)
    print("请粘贴你录制的代码（粘贴完成后，在新的一行输入 END 并按回车）：")
    print("=" * 60)
    
    code_lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        code_lines.append(line)
    
    original_code = '\n'.join(code_lines)
    
    if not original_code.strip():
        print("错误：没有输入代码！")
        return
    
    # 5. 转换代码
    print("\n正在转换代码...")
    
    # 提取核心代码（去掉函数定义和with语句）
    # 找到 def run 函数内的代码
    if 'def run(' in original_code:
        # 提取函数体
        start_idx = original_code.find('def run(')
        if start_idx != -1:
            # 找到函数体的开始
            brace_start = original_code.find(':', start_idx)
            if brace_start != -1:
                # 提取函数体内的代码（需要处理缩进）
                function_body = original_code[brace_start + 1:]
                # 找到最小缩进
                lines = function_body.split('\n')
                non_empty_lines = [l for l in lines if l.strip()]
                if non_empty_lines:
                    min_indent = min(len(l) - len(l.lstrip()) for l in non_empty_lines if l.strip())
                    # 减少缩进
                    converted_lines = []
                    for line in lines:
                        if line.strip():
                            if len(line) - len(line.lstrip()) >= min_indent:
                                converted_lines.append(line[min_indent:])
                            else:
                                converted_lines.append(line)
                        else:
                            converted_lines.append(line)
                    core_code = '\n'.join(converted_lines)
                else:
                    core_code = function_body
            else:
                core_code = original_code
        else:
            core_code = original_code
    else:
        core_code = original_code
    
    # 转换代码
    converted_code = convert_sync_to_async(core_code)
    
    # 为代码添加缩进（8个空格，因为是在try块内）
    indented_code = '\n'.join('            ' + line if line.strip() else line 
                              for line in converted_code.split('\n'))
    
    # 6. 生成测试文件
    test_file_content = generate_test_file(module, test_name, indented_code, author)
    
    # 7. 保存文件
    test_dir = Path(f"test_cases/{module}")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"test_{module}_{test_name}.py"
    filepath = test_dir / filename
    
    # 如果文件已存在，询问是否覆盖
    if filepath.exists():
        overwrite = input(f"\n文件 {filepath} 已存在，是否覆盖？(y/n，默认n): ").strip().lower()
        if overwrite != 'y':
            print("已取消保存。")
            return
    
    filepath.write_text(test_file_content, encoding='utf-8')
    
    print("\n" + "=" * 60)
    print("✅ 转换完成！")
    print("=" * 60)
    print(f"📁 文件已保存到: {filepath}")
    print(f"📝 测试类名: Test{module.capitalize()}{test_name.replace('_', '').title().replace(' ', '')}")
    print(f"🧪 测试方法: test_{test_name}")
    print()
    print("💡 提示：")
    print("   1. 检查生成的代码，确保所有操作都正确转换")
    print("   2. 可以运行测试验证：pytest " + str(filepath) + " -v")
    print("   3. 在WebUI中选择对应模块执行测试")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消操作。")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

