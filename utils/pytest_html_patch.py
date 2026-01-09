"""
pytest-html编码补丁
用于修复pytest-html在Windows系统下生成HTML报告时的中文乱码问题

使用方法：
在 conftest.py 或测试文件开头导入此模块：
    import utils.pytest_html_patch

注意：此补丁会修改pytest-html的html_report.py文件：
1. 确保charset保持为UTF-8（不再使用GB2312，因为文件内容本身就是UTF-8编码）
2. 将write_text()改为使用open()方式，强制使用UTF-8编码写入文件

如果此补丁无法正常工作，可以手动修改：
C:\Python310\lib\site-packages\pytest_html\html_report.py
1. 确保 charset="utf-8"（不要改为GB2312）
2. 将 self.logfile.write_text(report_content) 改为：
   with self.logfile.open('w', encoding='utf-8', errors='replace') as f:
       f.write(report_content)
"""

import sys
from pathlib import Path

def patch_pytest_html_charset():
    """修补pytest-html的charset设置和文件写入编码"""
    try:
        import pytest_html
        pytest_html_path = Path(pytest_html.__file__).parent
        html_report_file = pytest_html_path / 'html_report.py'
        
        if not html_report_file.exists():
            print(f"[pytest_html_patch] 警告: 未找到 {html_report_file}")
            return False
        
        # 读取文件内容
        content = html_report_file.read_text(encoding='utf-8', errors='replace')
        modified = False
        
        # 注意：不再修改charset为GB2312，保持UTF-8
        # 因为BeautifulSoup和Python内部都使用UTF-8，强制使用GB2312会导致乱码
        # 如果之前已经改为GB2312，改回UTF-8
        if 'charset="GB2312"' in content:
            content = content.replace('charset="GB2312"', 'charset="utf-8"')
            modified = True
            print("[pytest_html_patch] 已将charset从GB2312改回UTF-8，避免中文乱码")
        
        # 修复write_text的编码问题：将默认的GBK编码改为UTF-8
        # 问题：pathlib.write_text()在Windows上即使指定encoding='utf-8'，内部仍可能使用GBK
        # 解决方案：使用open()方式强制使用UTF-8编码
        
        # 检查是否已经使用open方式
        if "with self.logfile.open('w', encoding='utf-8'" in content:
            # 已经修复过了
            pass
        else:
            # 查找所有可能的write_text模式
            lines = content.split('\n')
            for i, line in enumerate(lines):
                # 匹配各种write_text模式（包括已经有encoding参数的）
                if 'self.logfile.write_text(report_content' in line:
                    # 计算缩进
                    indent = len(line) - len(line.lstrip())
                    # 替换为使用open方式（更可靠）
                    new_lines = [
                        ' ' * indent + "with self.logfile.open('w', encoding='utf-8', errors='replace') as f:",
                        ' ' * (indent + 4) + "f.write(report_content)"
                    ]
                    lines[i] = '\n'.join(new_lines)
                    content = '\n'.join(lines)
                    modified = True
                    break
        
        # 如果文件被修改，保存
        if modified:
            # 备份原文件
            backup_file = html_report_file.with_suffix('.py.bak')
            if not backup_file.exists():
                try:
                    import shutil
                    shutil.copy2(html_report_file, backup_file)
                    print(f"[pytest_html_patch] 已备份原文件到: {backup_file}")
                except:
                    pass
            
            # 写入修改后的内容
            html_report_file.write_text(content, encoding='utf-8')
            print(f"[pytest_html_patch] 已成功修补pytest-html的编码设置")
            print(f"[pytest_html_patch] 文件位置: {html_report_file}")
            return True
        else:
            # 检查是否已经修补过
            has_charset_utf8 = 'charset="utf-8"' in content
            has_write_fix = "with self.logfile.open('w', encoding='utf-8'" in content
            if has_charset_utf8 and has_write_fix:
                print("[pytest_html_patch] pytest-html已经修补过，无需重复修补")
                return True
            elif not has_charset_utf8:
                # 如果charset不是UTF-8，改回UTF-8
                if 'charset="GB2312"' in content:
                    content = content.replace('charset="GB2312"', 'charset="utf-8"')
                    html_report_file.write_text(content, encoding='utf-8')
                    print("[pytest_html_patch] 已将charset从GB2312改回UTF-8，避免中文乱码")
                    return True
            elif not has_write_fix:
                print("[pytest_html_patch] 警告: charset已修复，但write_text编码问题未修复，尝试修复...")
                # 再次尝试修复write_text
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'self.logfile.write_text(report_content' in line:
                        indent = len(line) - len(line.lstrip())
                        new_lines = [
                            ' ' * indent + "with self.logfile.open('w', encoding='utf-8', errors='replace') as f:",
                            ' ' * (indent + 4) + "f.write(report_content)"
                        ]
                        lines[i] = '\n'.join(new_lines)
                        content = '\n'.join(lines)
                        html_report_file.write_text(content, encoding='utf-8')
                        print("[pytest_html_patch] write_text编码问题已修复")
                        return True
            else:
                print(f"[pytest_html_patch] 警告: 未找到需要修补的内容")
                return False
    except Exception as e:
        print(f"[pytest_html_patch] 修补失败: {e}")
        import traceback
        print(traceback.format_exc())
        print(f"[pytest_html_patch] 请手动修改 pytest_html/html_report.py 文件")
        print(f"[pytest_html_patch] 1. 将 charset=\"utf-8\" 改为 charset=\"GB2312\"")
        print(f"[pytest_html_patch] 2. 将 write_text(report_content) 改为 write_text(report_content, encoding='utf-8', errors='replace')")
        return False

# 自动执行修补
if __name__ != '__main__':
    # 只在导入时执行，不在直接运行时执行
    try:
        patch_pytest_html_charset()
    except:
        pass

