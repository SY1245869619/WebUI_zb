"""
测试报告解析工具
从pytest输出和HTML报告中提取测试统计信息

@File  : report_parser.py
@Author: shenyuan
"""
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


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
            # 尝试多种编码方式读取HTML文件，避免乱码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            content = None
            for encoding in encodings:
                try:
                    with open(html_path, 'r', encoding=encoding, errors='replace') as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            if content is None:
                # 如果所有编码都失败，使用errors='replace'强制读取
                with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            
            result = {}
            
            # 从HTML中提取统计信息
            # pytest-html报告的格式可能是：
            # 1. <p>1 passed, 1 failed in 10.23s</p>
            # 2. "3 tests took 00:01:33" 或 "3 tests took 1.23s"
            # 3. "0 Failed," "3 Passed," "0 Skipped," 等复选框文本
            
            # 方法1: 从复选框文本中提取（更准确）
            # 查找类似 "3 Passed," 或 "0 Failed," 的文本
            checkbox_pattern = r'(\d+)\s+(Passed|Failed|Skipped|Error|Expected failures|Unexpected passes|Reruns)'
            checkbox_matches = re.findall(checkbox_pattern, content, re.IGNORECASE)
            
            passed = failed = skipped = error = 0
            total_from_checkbox = 0
            
            for count, status in checkbox_matches:
                count = int(count)
                status_lower = status.lower()
                if 'passed' in status_lower and 'unexpected' not in status_lower:
                    passed = count
                    total_from_checkbox += count
                elif 'failed' in status_lower and 'expected' not in status_lower:
                    failed = count
                    total_from_checkbox += count
                elif 'skipped' in status_lower:
                    skipped = count
                    total_from_checkbox += count
                elif 'error' in status_lower:
                    error = count
                    total_from_checkbox += count
            
            # 方法2: 如果方法1没找到，尝试从 "X tests took" 格式中提取总数
            if total_from_checkbox == 0:
                tests_took_pattern = r'(\d+)\s+tests\s+took'
                tests_took_match = re.search(tests_took_pattern, content, re.IGNORECASE)
                if tests_took_match:
                    total_from_checkbox = int(tests_took_match.group(1))
            
            # 方法3: 从 "X passed, Y failed" 格式中提取
            if passed == 0 and failed == 0 and skipped == 0:
                stats_pattern = r'(\d+)\s+(passed|failed|skipped|error)'
                matches = re.findall(stats_pattern, content, re.IGNORECASE)
                
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
            # 优先使用从复选框提取的总数，否则计算总和
            result['total'] = total_from_checkbox if total_from_checkbox > 0 else (passed + failed + skipped + error)
            
            # 提取执行时长
            # 格式可能是 "in 10.23s" 或 "took 00:01:33" 或 "took 1.23s"
            duration = 0.0
            
            # 方法1: 查找 "in X.XXs" 格式
            duration_pattern = r'in\s+([\d.]+)s'
            duration_match = re.search(duration_pattern, content, re.IGNORECASE)
            if duration_match:
                duration = float(duration_match.group(1))
            else:
                # 方法2: 查找 "took HH:MM:SS" 格式
                took_time_pattern = r'took\s+(\d{2}):(\d{2}):(\d{2})'
                took_time_match = re.search(took_time_pattern, content, re.IGNORECASE)
                if took_time_match:
                    hours = int(took_time_match.group(1))
                    minutes = int(took_time_match.group(2))
                    seconds = float(took_time_match.group(3))
                    duration = hours * 3600 + minutes * 60 + seconds
                else:
                    # 方法3: 查找 "took X.XXs" 格式
                    took_sec_pattern = r'took\s+([\d.]+)s'
                    took_sec_match = re.search(took_sec_pattern, content, re.IGNORECASE)
                    if took_sec_match:
                        duration = float(took_sec_match.group(1))
            
            if duration > 0:
                result['duration'] = duration
            
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
            
            # 尝试多种编码方式读取HTML文件，避免乱码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            content = None
            for encoding in encodings:
                try:
                    with open(html_path, 'r', encoding=encoding, errors='replace') as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            if content is None:
                # 如果所有编码都失败，使用errors='replace'强制读取
                with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            test_cases = []
            
            # 方法1: 查找测试用例表格（多种可能的ID和class）
            table = soup.find('table', {'id': 'results-table'})
            if not table:
                table = soup.find('table', id='results-table')
            if not table:
                table = soup.find('table', class_='results')
            if not table:
                # 查找所有table，找到包含测试结果的表格
                all_tables = soup.find_all('table')
                for t in all_tables:
                    # 检查表格是否包含Result、Test等列
                    headers = t.find_all('th')
                    header_texts = [h.get_text(strip=True).lower() for h in headers]
                    if any(keyword in ' '.join(header_texts) for keyword in ['result', 'test', 'duration']):
                        table = t
                        break
            
            if table:
                # 查找tbody中的行（pytest-html将测试用例放在tbody中）
                tbody = table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                else:
                    # 如果没有tbody，直接查找所有tr（跳过表头）
                    rows = table.find_all('tr')[1:]
                # 使用字典存储测试用例，key为测试名称，value为测试用例信息
                # 这样可以去重，只保留每个测试用例的最终状态
                test_cases_dict = {}
                
                # 调试：打印所有行的信息
                for idx, row in enumerate(rows):
                    cells = row.find_all('td')
                    if len(cells) < 2:
                        # 检查是否是展开的详情行（通常包含错误信息或日志）
                        # 这些行可能只有1个单元格，但包含重要的错误信息
                        if len(cells) == 1:
                            # 检查是否是详情行（包含log div或其他详情内容）
                            detail_div = row.find('div', class_='log')
                            if detail_div:
                                # 这是详情行，尝试关联到上一个测试用例
                                # 查找前一个测试用例行
                                prev_row = row.find_previous_sibling('tr')
                                if prev_row and prev_row.find_all('td'):
                                    # 如果前一行是测试用例行，跳过这个详情行（错误信息已在解析时处理）
                                    pass
                        # 跳过详情行（只有1个单元格，包含错误信息或日志）
                        logger.debug(f"[ReportParser] 跳过行 {idx+1}: 单元格数量不足 ({len(cells)})")
                        continue
                    
                    # 不再打印调试信息
                    
                    # 解析状态
                    status_cell = cells[0]
                    status_text = status_cell.get_text(strip=True).lower()
                    # 支持多种状态：passed, failed, skipped, error, rerun
                    if 'passed' in status_text:
                        status = 'passed'
                    elif 'failed' in status_text:
                        status = 'failed'
                    elif 'skipped' in status_text:
                        status = 'skipped'
                    elif 'error' in status_text:
                        status = 'error'
                    elif 'rerun' in status_text:
                        # Rerun状态通常表示测试重试，跳过rerun记录，只保留最终状态
                        continue
                    else:
                        status = 'passed'  # 默认状态
                    
                    # 解析用例名称（可能是第二个或第三个单元格）
                    test_cell = cells[1] if len(cells) > 1 else None
                    if not test_cell:
                        logger.debug(f"[ReportParser] 行 {idx+1}: Test列单元格不存在")
                        continue
                    
                    # 尝试从原始HTML中提取测试名称，避免BeautifulSoup解码问题
                    test_name = ''
                    try:
                        # 方法1：直接使用get_text()获取文本（最简单直接）
                        test_name = test_cell.get_text(strip=True)
                        
                        # 方法2：如果get_text()返回空，尝试从HTML中提取
                        if not test_name:
                            test_cell_html = str(test_cell)
                            # 使用正则表达式提取测试名称（包括所有内容，包括我们添加的中文标识）
                            # 匹配 <td>...</td> 中的内容
                            name_match = re.search(r'<td[^>]*class="col-[^"]*"[^>]*>(.*?)</td>', test_cell_html, re.DOTALL)
                            if name_match:
                                raw_name = name_match.group(1)
                                # 清理HTML标签，但保留文本内容
                                raw_name = re.sub(r'<[^>]+>', '', raw_name)
                                # 解码HTML实体
                                import html
                                raw_name = html.unescape(raw_name)
                                test_name = raw_name.strip()
                    except Exception as e:
                        logger.warning(f"[ReportParser] 提取测试名称失败: {e}")
                        # 如果正则提取失败，使用BeautifulSoup
                        try:
                            test_name = test_cell.get_text(strip=True)
                        except:
                            test_name = ''
                    
                    if not test_name:
                        logger.debug(f"[ReportParser] 行 {idx+1}: 无法提取测试名称，跳过")
                        continue
                    
                    logger.debug(f"[ReportParser] 行 {idx+1}: 提取到测试名称: {test_name}")
                    
                    # 跳过setup/teardown相关的行（这些不是真正的测试用例）
                    if '::setup' in test_name or '::teardown' in test_name:
                        logger.debug(f"[ReportParser] 跳过setup/teardown行: {test_name}")
                        continue
                    
                    # 清理测试名称：提取原始测试路径（移除我们添加的中文标识和HTML转义）
                    # 测试名称格式可能是：[授课教学] test_teaching_first.py::TestTeachingNavigation::test_teaching_module_navigation
                    # 或者：test_cases/teaching/test_teaching_first.py::TestTeachingNavigation::test_teaching_module_navigation
                    # 或者：test_teaching_first.py::TestTeachingNavigation::test_teaching_module_navigation&lt;/td&gt;
                    clean_test_name = test_name
                    # 移除HTML转义字符
                    clean_test_name = clean_test_name.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
                    # 移除HTML标签
                    clean_test_name = re.sub(r'<[^>]+>', '', clean_test_name)
                    # 移除我们添加的中文模块标识 [模块名]（如果存在）
                    clean_test_name = re.sub(r'^\[[^\]]+\]\s*', '', clean_test_name)
                    # 移除末尾可能的 </td> 等标签残留
                    clean_test_name = clean_test_name.replace('</td>', '').strip()
                    # 如果还是包含 ::，确保格式正确
                    if '::' in clean_test_name:
                        # 移除 :: 后面可能的中文标识
                        parts = clean_test_name.split('::')
                        clean_parts = []
                        for part in parts:
                            # 移除 [ 或 | 之后的内容
                            if '[' in part:
                                part = part.split('[')[0].strip()
                            if '|' in part:
                                part = part.split('|')[0].strip()
                            clean_parts.append(part.strip())
                        clean_test_name = '::'.join(clean_parts)
                    
                    # 确保测试名称包含完整路径（如果只有文件名，尝试从test_cell的上下文推断）
                    if not clean_test_name.startswith('test_cases/'):
                        # 如果测试名称不包含路径，尝试从原始HTML中提取
                        if 'test_cases/' in test_name:
                            # 从原始test_name中提取完整路径
                            path_match = re.search(r'(test_cases/[^:]+)', test_name)
                            if path_match:
                                base_path = path_match.group(1)
                                if '::' in clean_test_name:
                                    file_part = clean_test_name.split('::')[0]
                                    clean_test_name = f"{base_path}::{clean_test_name.split('::', 1)[1]}"
                                else:
                                    clean_test_name = base_path
                    
                    # 解析时长（Duration列通常是第三个单元格，索引为2）
                    duration = 0.0
                    if len(cells) > 2:
                        duration_cell = cells[2]  # Duration列通常是第三个单元格
                        try:
                            duration_text = duration_cell.get_text(strip=True)
                            # 解析时长格式 "28.64s" 或 "00:00:32" 或 "32.5s"
                            if 's' in duration_text.lower():
                                # 移除's'和其他非数字字符，保留数字和小数点
                                duration = float(re.sub(r'[^\d.]', '', duration_text))
                            elif ':' in duration_text:
                                parts = duration_text.split(':')
                                if len(parts) == 3:
                                    duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                                elif len(parts) == 2:
                                    duration = int(parts[0]) * 60 + float(parts[1])
                            elif re.match(r'^\d+\.?\d*$', duration_text):
                                duration = float(duration_text)
                        except Exception as e:
                            logger.debug(f"[ReportParser] 解析时长失败: {e}, duration_text: {duration_text if 'duration_text' in locals() else 'N/A'}")
                    
                    # 解析错误信息（如果有）
                    error = ''
                    if status == 'failed':
                        # 查找错误详情 - 可能在下一行或展开的div中
                        # 方法1: 查找同一行中的log div
                        log_div = row.find('div', class_='log')
                        if not log_div:
                            # 方法2: 查找下一行的log div
                            next_row = row.find_next_sibling('tr')
                            if next_row:
                                log_div = next_row.find('div', class_='log')
                        if not log_div:
                            # 方法3: 查找后续的log div
                            log_div = row.find_next('div', class_='log')
                        if log_div:
                            error = log_div.get_text(strip=True)
                            # 限制错误信息长度
                            if len(error) > 500:
                                error = error[:500] + '...'
                    
                    # 使用字典存储，如果已存在则更新（保留最新的状态和时长）
                    # 这样可以去重，只保留每个测试用例的最终状态
                    if clean_test_name not in test_cases_dict:
                        test_cases_dict[clean_test_name] = {
                            'name': clean_test_name,
                            'status': status,
                            'duration': duration,
                            'error': error
                        }
                        # 不再打印调试信息
                    else:
                        # 如果已存在，更新状态和时长（保留更重要的状态，如failed > passed）
                        existing = test_cases_dict[clean_test_name]
                        if status == 'failed' or (status == 'error' and existing['status'] != 'failed'):
                            existing['status'] = status
                            existing['error'] = error
                        if duration > existing['duration']:
                            existing['duration'] = duration
                            # 不再打印调试信息
                
                # 将字典转换为列表
                test_cases = list(test_cases_dict.values())
            
            # 不再打印调试信息
            
            # 如果解析到的测试用例数量少于预期，尝试从pytest输出中解析（备用方案）
            # 这通常发生在HTML报告格式变化或解析逻辑需要调整时
            
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

