"""
测试报告解析工具
从pytest输出和HTML报告中提取测试统计信息

@File  : report_parser.py
@Author: shenyuan
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class ReportParser:
    """测试报告解析器"""
    
    @staticmethod
    def parse_pytest_output(output_lines: List[str]) -> Dict[str, Any]:
        """解析pytest输出，提取测试统计信息
        
        Args:
            output_lines: pytest输出的行列表
            
        Returns:
            包含测试统计信息的字典
        """
        result = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'error': 0,
            'duration': 0.0,
            'error_details': []
        }
        
        output_text = '\n'.join(output_lines)
        
        # 解析测试统计（例如：1 passed, 1 failed in 10.23s）
        stats_pattern = r'(\d+)\s+(passed|failed|skipped|error|warnings)'
        matches = re.findall(stats_pattern, output_text, re.IGNORECASE)
        
        for count, status in matches:
            count = int(count)
            status_lower = status.lower()
            if 'passed' in status_lower:
                result['passed'] = count
            elif 'failed' in status_lower:
                result['failed'] = count
            elif 'skipped' in status_lower:
                result['skipped'] = count
            elif 'error' in status_lower:
                result['error'] = count
        
        # 计算总数
        result['total'] = result['passed'] + result['failed'] + result['skipped'] + result['error']
        
        # 解析执行时长（例如：in 10.23s 或 in 1.23s）
        duration_pattern = r'in\s+([\d.]+)s'
        duration_match = re.search(duration_pattern, output_text, re.IGNORECASE)
        if duration_match:
            result['duration'] = float(duration_match.group(1))
        
        # 解析失败用例详情
        failed_tests = []
        current_test = None
        current_error = []
        
        for line in output_lines:
            # 匹配失败用例（例如：FAILED test_teaching_first.py::TestTeachingFirst::test_first）
            failed_match = re.match(r'FAILED\s+(.+?::.+?::.+?)(?:\s|$)', line)
            if failed_match:
                if current_test:
                    failed_tests.append({
                        'name': current_test,
                        'error': '\n'.join(current_error).strip()
                    })
                current_test = failed_match.group(1)
                current_error = []
            elif current_test:
                # 收集错误信息（直到下一个测试用例或空行）
                if line.strip() and not line.startswith('=') and not line.startswith('-'):
                    current_error.append(line.strip())
                elif not line.strip() and current_error:
                    failed_tests.append({
                        'name': current_test,
                        'error': '\n'.join(current_error).strip()
                    })
                    current_test = None
                    current_error = []
        
        # 添加最后一个失败用例
        if current_test:
            failed_tests.append({
                'name': current_test,
                'error': '\n'.join(current_error).strip()
            })
        
        result['error_details'] = failed_tests[:10]  # 最多保留10个错误详情
        
        return result
    
    @staticmethod
    def parse_html_report(html_path: Path) -> Dict[str, Any]:
        """解析pytest-html生成的HTML报告
        
        Args:
            html_path: HTML报告文件路径
            
        Returns:
            包含测试统计信息的字典
        """
        if not html_path.exists():
            return {}
        
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = {}
            
            # 从HTML中提取统计信息
            # pytest-html报告的格式通常是：<p>1 passed, 1 failed in 10.23s</p>
            stats_pattern = r'(\d+)\s+(passed|failed|skipped|error)'
            matches = re.findall(stats_pattern, content, re.IGNORECASE)
            
            passed = failed = skipped = error = 0
            for count, status in matches:
                count = int(count)
                status_lower = status.lower()
                if 'passed' in status_lower:
                    passed = count
                elif 'failed' in status_lower:
                    failed = count
                elif 'skipped' in status_lower:
                    skipped = count
                elif 'error' in status_lower:
                    error = count
            
            result['passed'] = passed
            result['failed'] = failed
            result['skipped'] = skipped
            result['error'] = error
            result['total'] = passed + failed + skipped + error
            
            # 提取执行时长
            duration_pattern = r'in\s+([\d.]+)s'
            duration_match = re.search(duration_pattern, content, re.IGNORECASE)
            if duration_match:
                result['duration'] = float(duration_match.group(1))
            
            return result
        except Exception as e:
            print(f"解析HTML报告失败: {e}")
            return {}
    
    @staticmethod
    def parse_test_cases_from_html(html_path: Path) -> List[Dict[str, Any]]:
        """从pytest-html报告中解析测试用例列表
        
        Args:
            html_path: HTML报告文件路径
            
        Returns:
            测试用例列表，每个用例包含name, status, duration, error
        """
        if not html_path.exists():
            return []
        
        try:
            from bs4 import BeautifulSoup
            
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            test_cases = []
            
            # 查找测试用例表格
            table = soup.find('table', {'id': 'results-table'})
            if not table:
                # 尝试查找其他可能的表格
                table = soup.find('table', class_='results')
            
            if table:
                rows = table.find_all('tr')[1:]  # 跳过表头
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        # 解析状态
                        status_cell = cells[0]
                        status_text = status_cell.get_text(strip=True).lower()
                        status = 'passed' if 'passed' in status_text else 'failed' if 'failed' in status_text else 'skipped'
                        
                        # 解析用例名称
                        test_cell = cells[1]
                        test_name = test_cell.get_text(strip=True)
                        
                        # 解析时长
                        duration_cell = cells[2] if len(cells) > 2 else None
                        duration = 0.0
                        if duration_cell:
                            duration_text = duration_cell.get_text(strip=True)
                            # 解析时长格式 "00:00:32" 或 "32.5s"
                            if ':' in duration_text:
                                parts = duration_text.split(':')
                                duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                            elif 's' in duration_text:
                                duration = float(duration_text.replace('s', ''))
                        
                        # 解析错误信息（如果有）
                        error = ''
                        if status == 'failed':
                            # 查找错误详情
                            error_div = row.find_next('div', class_='log')
                            if error_div:
                                error = error_div.get_text(strip=True)
                        
                        test_cases.append({
                            'name': test_name,
                            'status': status,
                            'duration': duration,
                            'error': error
                        })
            
            return test_cases
        except ImportError:
            # 如果没有BeautifulSoup，使用正则表达式简单解析
            test_cases = []
            # 简单的正则匹配
            test_pattern = r'<tr[^>]*>.*?<td[^>]*>.*?(passed|failed|skipped).*?</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>'
            matches = re.finditer(test_pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                status = match.group(1).lower()
                name = re.sub(r'<[^>]+>', '', match.group(2)).strip()
                duration_text = re.sub(r'<[^>]+>', '', match.group(3)).strip()
                
                # 解析时长
                duration = 0.0
                if ':' in duration_text:
                    parts = duration_text.split(':')
                    duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                elif 's' in duration_text:
                    duration = float(re.sub(r'[^\d.]', '', duration_text))
                
                test_cases.append({
                    'name': name,
                    'status': status,
                    'duration': duration,
                    'error': ''
                })
            
            return test_cases
        except Exception as e:
            print(f"解析测试用例失败: {e}")
            return []
    
    @staticmethod
    def get_latest_report_path() -> Optional[Path]:
        """获取最新的HTML报告路径
        
        Returns:
            最新的报告文件路径，如果不存在则返回None
        """
        reports_dir = Path("reports")
        if not reports_dir.exists():
            return None
        
        # 查找所有HTML报告文件
        html_reports = list(reports_dir.glob("report_*.html"))
        if not html_reports:
            return None
        
        # 返回最新的文件（按修改时间排序）
        return max(html_reports, key=lambda p: p.stat().st_mtime)

