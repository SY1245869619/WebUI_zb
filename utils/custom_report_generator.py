"""
自定义中文HTML测试报告生成器
生成美观的中文测试报告，替代pytest-html的英文报告

@File  : custom_report_generator.py
@Author: shenyuan
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import html
import logging

logger = logging.getLogger(__name__)


class CustomReportGenerator:
    """自定义测试报告生成器"""
    
    @staticmethod
    def generate_html_report(
        test_results: Dict[str, Any],
        output_path: Path,
        modules: List[str] = None
    ) -> Path:
        """生成自定义的中文HTML测试报告
        
        Args:
            test_results: 测试结果字典，包含：
                - total: 总用例数
                - passed: 通过数
                - failed: 失败数
                - skipped: 跳过数
                - duration: 执行时长（秒）
                - test_cases: 测试用例列表，每个用例包含：
                    - name: 用例名称
                    - status: 状态 (passed/failed/skipped)
                    - duration: 执行时长
                    - error: 错误信息（如果有）
            output_path: 输出文件路径
            modules: 执行的模块列表
            
        Returns:
            生成的报告文件路径
        """
        modules = modules or []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pass_rate = (test_results.get('passed', 0) / test_results.get('total', 1) * 100) if test_results.get('total', 0) > 0 else 0
        
        # 格式化执行时长
        duration = test_results.get('duration', 0)
        duration_str = CustomReportGenerator._format_duration(duration)
        
        # 获取历史趋势数据
        trend_data = CustomReportGenerator._get_trend_data(9)  # 最近9次（加上本次共10次）
        
        # 准备图表数据
        # 1. 饼图数据：本次执行结果分布
        pie_data = {
            'passed': test_results.get('passed', 0),
            'failed': test_results.get('failed', 0),
            'skipped': test_results.get('skipped', 0)
        }
        
        # 2. 趋势图数据：最近10次执行的通过率（包括本次）
        # 将所有数据（历史+本次）合并，按时间排序
        all_trend_data = []
        
        # 添加历史数据
        for data in trend_data[:9]:  # 最多显示9次历史数据
            exec_time = data.get('execution_time', '')
            if isinstance(exec_time, str):
                try:
                    dt = datetime.fromisoformat(exec_time.replace('Z', '+00:00'))
                    all_trend_data.append({
                        'time': dt,
                        'label': dt.strftime('%m-%d %H:%M'),
                        'pass_rate': data.get('pass_rate', 0),
                        'duration': data.get('duration', 0)
                    })
                except:
                    # 如果解析失败，尝试其他格式
                    try:
                        dt = datetime.strptime(exec_time[:16], '%Y-%m-%d %H:%M')
                        all_trend_data.append({
                            'time': dt,
                            'label': dt.strftime('%m-%d %H:%M'),
                            'pass_rate': data.get('pass_rate', 0),
                            'duration': data.get('duration', 0)
                        })
                    except:
                        all_trend_data.append({
                            'time': datetime.now(),
                            'label': exec_time[:16] if len(exec_time) > 16 else exec_time,
                            'pass_rate': data.get('pass_rate', 0),
                            'duration': data.get('duration', 0)
                        })
            else:
                all_trend_data.append({
                    'time': datetime.now(),
                    'label': str(exec_time)[:16],
                    'pass_rate': data.get('pass_rate', 0),
                    'duration': data.get('duration', 0)
                })
        
        # 添加本次执行结果
        current_time = datetime.now()
        all_trend_data.append({
            'time': current_time,
            'label': timestamp[5:16],  # 只显示月-日 时:分
            'pass_rate': pass_rate,
            'duration': duration
        })
        
        # 按时间排序（从旧到新）
        all_trend_data.sort(key=lambda x: x['time'])
        
        # 提取排序后的数据
        trend_labels = [item['label'] for item in all_trend_data]
        trend_pass_rates = [item['pass_rate'] for item in all_trend_data]
        trend_durations = [item['duration'] for item in all_trend_data]
        
        # 如果没有历史数据，至少显示当前这次
        if not trend_labels:
            trend_labels = [timestamp[5:16]]  # 只显示月-日 时:分
            trend_pass_rates = [pass_rate]
            trend_durations = [duration]
        
        # 3. 柱状图数据：各测试用例执行时长（直接按测试用例显示，不按模块聚合）
        # 分别显示失败和重试的时长，不累加
        test_cases = test_results.get('test_cases', [])
        logger.info(f"[CustomReport] 开始处理 {len(test_cases)} 个测试用例")
        
        # 去重测试用例，但保留失败和重试的分别条目
        test_case_dict = {}  # {base_name: [{'duration': float, 'status': str, 'display_name': str}]}
        seen_base_names = set()  # 用于去重，确保同一个测试用例只处理一次（除非是失败或重试）
        
        for test_case in test_cases:
            test_name = test_case.get('name', '')
            test_duration = test_case.get('duration', 0)
            test_status = test_case.get('status', 'passed')
            
            # 清理测试名称（去除HTML标签和多余字符）
            import re
            clean_name = re.sub(r'<[^>]+>', '', test_name).strip()
            # 去除尾部的所有非字母数字字符（但保留路径中的斜杠和冒号）
            clean_name = re.sub(r'[^\w\s/:\.\-\[\]]+$', '', clean_name).strip()
            # 只去除尾部的特殊字符（如 ',', '</td>', 单引号等），不要去除路径中的斜杠
            clean_name = re.sub(r'[,</>\']+$', '', clean_name).strip()
            # 去除尾部的逗号和单引号（但保留路径中的斜杠）
            clean_name = re.sub(r"[,']+$", '', clean_name).strip()
            
            if not clean_name:
                continue
            
            # 提取基础名称（用于去重判断）
            # 例如：test_cases/teaching/test_teaching_first.py::TestTeachingNavigation::test_teaching_module_navigation
            # base_name应该是完整的测试路径（包括类和方法），用于唯一标识一个测试用例
            base_name = clean_name  # 使用完整的clean_name作为base_name，确保唯一性
            
            # 如果这个base_name已经处理过，且当前状态是passed，跳过（避免重复）
            # 但如果状态是failed或rerun，仍然添加（因为可能是重试或失败的情况）
            if base_name in seen_base_names and test_status == 'passed':
                logger.debug(f"[CustomReport] 跳过重复的测试用例（已处理过）: {base_name}, 状态: {test_status}")
                continue
            
            # 标记为已处理
            seen_base_names.add(base_name)
            
            # 如果基础名称不存在，创建列表
            if base_name not in test_case_dict:
                test_case_dict[base_name] = []
            
            # 提取简短的显示名称（只保留文件名，例如 test_teaching_first）
            # 例如：test_cases/teaching/test_teaching_first.py::TestTeachingNavigation::test_teaching_module_navigation
            # -> test_teaching_first
            import os
            # 提取文件路径部分（去除::后面的部分）
            file_path = clean_name.split('::')[0] if '::' in clean_name else clean_name
            
            # 如果路径中没有斜杠，说明可能已经被错误处理了，尝试从原始test_name恢复
            if '/' not in file_path and '\\' not in file_path:
                # 如果路径中没有斜杠，尝试从原始test_name中提取
                original_path = test_name.split('::')[0] if '::' in test_name else test_name
                if '/' in original_path or '\\' in original_path:
                    file_path = original_path
            
            # 使用os.path.basename获取文件名，然后去除扩展名
            file_name_with_ext = os.path.basename(file_path)
            file_name = os.path.splitext(file_name_with_ext)[0]  # 去除扩展名
            display_name = file_name
            
            logger.debug(f"[CustomReport] 文件名提取: test_name={test_name}, clean_name={clean_name}, file_path={file_path}, file_name={file_name}, display_name={display_name}")
            
            # 根据状态添加后缀标识（只在有重试或失败时添加）
            if test_status == 'rerun':
                display_name = f"{display_name} (重试)"
            elif test_status in ['failed', 'error']:
                display_name = f"{display_name} (失败)"
            
            # 添加到字典中（同一个基础名称可能有多个条目：失败和重试）
            test_case_dict[base_name].append({
                'duration': test_duration,
                'status': test_status,
                'display_name': display_name,
                'original_name': clean_name
            })
        
        # 准备柱状图数据：按测试用例显示（包括失败和重试的分别条目）
        test_case_labels = []
        test_case_duration_values = []
        test_case_pass_rates = []  # 用于热力图
        
        # 按基础名称排序，然后按状态排序（失败在前，重试在后）
        sorted_base_names = sorted(test_case_dict.keys())
        for base_name in sorted_base_names:
            entries = test_case_dict[base_name]
            # 按状态排序：failed > rerun > passed
            status_order = {'failed': 0, 'error': 0, 'rerun': 1, 'passed': 2}
            entries.sort(key=lambda x: status_order.get(x['status'], 2))
            
            for entry in entries:
                test_case_labels.append(entry['display_name'])
                test_case_duration_values.append(entry['duration'])
                # 计算通过率（1表示通过，0表示失败或重试）
                test_case_pass_rates.append(100 if entry['status'] == 'passed' else 0)
        
        logger.info(f"[CustomReport] 图表数据准备完成: {len(test_case_labels)} 个测试用例")
        logger.info(f"[CustomReport] 测试用例标签: {test_case_labels}")
        logger.info(f"[CustomReport] 测试用例时长: {test_case_duration_values}")
        
        # 为了兼容热力图（仍按模块显示），需要计算模块通过率
        # 但柱状图改为按测试用例显示
        from utils.module_helper import ModuleHelper
        module_pass_counts = {}  # {模块名: {'total': 0, 'passed': 0}}
        # 去重：只统计每个测试用例的最终状态（不包括重试）
        unique_test_cases = {}  # {base_name: final_status}
        for base_name, entries in test_case_dict.items():
            # 找到最终状态（优先失败，然后是passed，跳过rerun）
            final_status = 'passed'
            for entry in entries:
                status = entry.get('status', 'passed')
                if status in ['failed', 'error']:
                    final_status = status
                    break
                elif status == 'passed':
                    final_status = 'passed'
            unique_test_cases[base_name] = final_status
        
        # 统计模块通过率
        for base_name, final_status in unique_test_cases.items():
            # 从base_name中提取原始名称（用于模块识别）
            # base_name是文件路径，需要找到对应的original_name
            original_name = base_name
            if base_name in test_case_dict and test_case_dict[base_name]:
                original_name = test_case_dict[base_name][0].get('original_name', base_name)
            
            logger.info(f"[CustomReport] 提取模块名称: base_name={base_name}, original_name={original_name}, final_status={final_status}")
            module_name = ModuleHelper.extract_module_cn_name_from_path(original_name)
            logger.info(f"[CustomReport] 提取到的模块名称: {module_name}")
            
            if module_name:
                if module_name not in module_pass_counts:
                    module_pass_counts[module_name] = {'total': 0, 'passed': 0}
                module_pass_counts[module_name]['total'] += 1
                if final_status == 'passed':
                    module_pass_counts[module_name]['passed'] += 1
                logger.info(f"[CustomReport] 模块 {module_name} 统计: total={module_pass_counts[module_name]['total']}, passed={module_pass_counts[module_name]['passed']}")
            else:
                logger.warning(f"[CustomReport] 无法从路径 {original_name} 中提取模块名称，尝试使用base_name")
                # 如果从original_name提取失败，尝试直接从base_name提取
                if base_name and 'test_cases' in base_name:
                    module_name = ModuleHelper.extract_module_cn_name_from_path(base_name)
                    if module_name:
                        if module_name not in module_pass_counts:
                            module_pass_counts[module_name] = {'total': 0, 'passed': 0}
                        module_pass_counts[module_name]['total'] += 1
                        if final_status == 'passed':
                            module_pass_counts[module_name]['passed'] += 1
                        logger.info(f"[CustomReport] 从base_name提取到模块名称: {module_name}")
        
        # 计算模块通过率（用于热力图）
        module_labels = sorted(list(module_pass_counts.keys()))
        module_pass_rate_values = []
        for module_name in module_labels:
            counts = module_pass_counts[module_name]
            if counts['total'] > 0:
                module_pass_rate_values.append((counts['passed'] / counts['total']) * 100)
            else:
                module_pass_rate_values.append(0)
        
        logger.info(f"[CustomReport] 模块数据: {len(module_labels)} 个模块")
        logger.info(f"[CustomReport] 模块标签: {module_labels}")
        logger.info(f"[CustomReport] 模块通过率: {module_pass_rate_values}")
        
        # 如果没有模块数据，至少显示一个占位符
        if not module_labels:
            module_labels = ['暂无数据']
            module_pass_rate_values = [0]
            logger.warning(f"[CustomReport] 未提取到模块数据，使用占位符")
        
        # 生成HTML内容
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自动化测试报告 - {timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            font-size: 16px;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: #f8f9fa;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }}
        
        .stat-card.total {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .stat-card.passed {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }}
        
        .stat-card.failed {{
            background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
            color: white;
        }}
        
        .stat-card.skipped {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }}
        
        .stat-number {{
            font-size: 48px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .stat-label {{
            font-size: 16px;
            opacity: 0.9;
        }}
        
        .info-section {{
            background: #f8f9fa;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 40px;
        }}
        
        .info-item {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .info-item:last-child {{
            border-bottom: none;
        }}
        
        .info-label {{
            font-weight: 600;
            color: #495057;
        }}
        
        .info-value {{
            color: #6c757d;
        }}
        
        .pass-rate {{
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            margin-bottom: 40px;
        }}
        
        .pass-rate-number {{
            font-size: 64px;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        
        .pass-rate-label {{
            font-size: 20px;
            opacity: 0.9;
        }}
        
        .charts-section {{
            margin-top: 40px;
        }}
        
        .charts-section h2 {{
            font-size: 24px;
            margin-bottom: 30px;
            color: #212529;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}
        
        .chart-container {{
            background: #f8f9fa;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        
        .chart-container h3 {{
            font-size: 18px;
            font-weight: 600;
            color: #212529;
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .chart-container canvas {{
            max-width: 100%;
            height: auto;
        }}
        
        .chart-note {{
            margin-top: 12px;
            font-size: 12px;
            color: #6c757d;
            text-align: center;
            font-style: italic;
        }}
        
        .data-source-note {{
            margin-bottom: 20px;
            padding: 12px;
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            border-radius: 4px;
            color: #1976d2;
            font-size: 13px;
        }}
        
        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 24px;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
        }}
        
        @media (max-width: 768px) {{
            .summary {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 24px;
            }}
            
            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 自动化测试报告</h1>
            <div class="subtitle">WebUI自动化测试平台</div>
        </div>
        
        <div class="content">
            <!-- 统计卡片 -->
            <div class="summary">
                <div class="stat-card total">
                    <div class="stat-number">{test_results.get('total', 0)}</div>
                    <div class="stat-label">总用例数</div>
                </div>
                <div class="stat-card passed">
                    <div class="stat-number">{test_results.get('passed', 0)}</div>
                    <div class="stat-label">通过 ✅</div>
                </div>
                <div class="stat-card failed">
                    <div class="stat-number">{test_results.get('failed', 0)}</div>
                    <div class="stat-label">失败 ❌</div>
                </div>
                <div class="stat-card skipped">
                    <div class="stat-number">{test_results.get('skipped', 0)}</div>
                    <div class="stat-label">跳过 ⏭️</div>
                </div>
            </div>
            
            <!-- 通过率 -->
            <div class="pass-rate">
                <div class="pass-rate-number">{pass_rate:.1f}%</div>
                <div class="pass-rate-label">测试通过率</div>
            </div>
            
            <!-- 测试信息 -->
            <div class="info-section">
                <div class="info-item">
                    <span class="info-label">执行时间</span>
                    <span class="info-value">{timestamp}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">执行模块</span>
                    <span class="info-value">{', '.join(modules) if modules else '全部模块'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">执行时长</span>
                    <span class="info-value">{duration_str}</span>
                </div>
            </div>
            
            <!-- 数据统计图表 -->
            <div class="charts-section">
                <h2>📊 数据统计分析</h2>
                <p class="data-source-note">📌 数据来源：本次执行结果 + 历史测试数据（最近30天，来自test_results/目录和数据库）</p>
                
                <div class="charts-grid">
                    <!-- 饼图：本次执行结果分布 -->
                    <div class="chart-container">
                        <h3>执行结果分布</h3>
                        <canvas id="pieChart"></canvas>
                        <p class="chart-note">本次执行：通过 {pie_data['passed']} 个，失败 {pie_data['failed']} 个，跳过 {pie_data['skipped']} 个</p>
                    </div>
                    
                    <!-- 趋势图：最近10次通过率趋势 -->
                    <div class="chart-container">
                        <h3>通过率趋势（最近10次）</h3>
                        <canvas id="trendChart"></canvas>
                        <p class="chart-note">展示最近10次自动化构建的通过率变化趋势，帮助判断质量基线</p>
                    </div>
                    
                    <!-- 柱状图：各测试用例执行时长对比 -->
                    <div class="chart-container">
                        <h3>各测试用例执行时长对比</h3>
                        <canvas id="barChart"></canvas>
                        <p class="chart-note">各测试用例执行时长（秒），便于识别性能瓶颈</p>
                    </div>
                    
                    <!-- 热力图：各模块通过率 -->
                    <div class="chart-container">
                        <h3>各模块通过率热力图</h3>
                        <canvas id="heatmapChart"></canvas>
                        <p class="chart-note">颜色越深表示通过率越高（0-100%），快速识别问题模块</p>
                    </div>
                </div>
            </div>
"""
        
        html_content += f"""
            </div>
        </div>
        
        <div class="footer">
            <p>此报告由 WebUI自动化测试平台自动生成</p>
            <p>生成时间: {timestamp}</p>
        </div>
    </div>
    
    <!-- Chart.js 库 -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    
    <script>
        // 饼图：本次执行结果分布
        const pieCtx = document.getElementById('pieChart').getContext('2d');
        new Chart(pieCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['通过', '失败', '跳过'],
                datasets: [{{
                    data: [{pie_data['passed']}, {pie_data['failed']}, {pie_data['skipped']}],
                    backgroundColor: [
                        '#38ef7d',
                        '#ff6a00',
                        '#f5576c'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.5,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 15,
                            font: {{
                                size: 14
                            }}
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                let label = context.label || '';
                                if (label) {{
                                    label += ': ';
                                }}
                                const total = {test_results.get('total', 0)};
                                const value = context.parsed;
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                label += value + ' 个 (' + percentage + '%)';
                                return label;
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // 趋势图：最近10次通过率趋势
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        new Chart(trendCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(trend_labels)},
                datasets: [{{
                    label: '通过率 (%)',
                    data: {json.dumps(trend_pass_rates)},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top',
                        labels: {{
                            font: {{
                                size: 14
                            }}
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return '通过率: ' + context.parsed.y.toFixed(1) + '%';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }},
                            font: {{
                                size: 12
                            }}
                        }},
                        grid: {{
                            color: 'rgba(0, 0, 0, 0.05)'
                        }}
                    }},
                    x: {{
                        ticks: {{
                            font: {{
                                size: 11
                            }},
                            maxRotation: 45,
                            minRotation: 45
                        }},
                        grid: {{
                            display: false
                        }}
                    }}
                }}
            }}
        }});
        
        // 柱状图：各测试用例执行时长对比
        const barCtx = document.getElementById('barChart').getContext('2d');
        const testCaseLabels = {json.dumps(test_case_labels) if test_case_labels else json.dumps(['暂无数据'])};
        const testCaseDurationValues = {json.dumps(test_case_duration_values) if test_case_duration_values else json.dumps([0])};
        
        new Chart(barCtx, {{
            type: 'bar',
            data: {{
                labels: testCaseLabels,
                datasets: [{{
                    label: '执行时长（秒）',
                    data: testCaseDurationValues,
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(56, 239, 125, 0.8)',
                        'rgba(255, 106, 0, 0.8)',
                        'rgba(245, 87, 108, 0.8)',
                        'rgba(240, 147, 251, 0.8)'
                    ],
                    borderColor: [
                        '#667eea',
                        '#38ef7d',
                        '#ff6a00',
                        '#f5576c',
                        '#f093fb'
                    ],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top',
                        labels: {{
                            font: {{
                                size: 14
                            }}
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return '执行时长: ' + context.parsed.y.toFixed(2) + ' 秒';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return value.toFixed(1) + 's';
                            }},
                            font: {{
                                size: 12
                            }}
                        }},
                        grid: {{
                            color: 'rgba(0, 0, 0, 0.05)'
                        }}
                    }},
                    x: {{
                        ticks: {{
                            font: {{
                                size: 12
                            }}
                        }},
                        grid: {{
                            display: false
                        }}
                    }}
                }}
            }}
        }});
        
        // 热力图：各模块通过率（使用柱状图模拟热力图效果）
        const heatmapCtx = document.getElementById('heatmapChart').getContext('2d');
        const moduleLabels = {json.dumps(module_labels) if module_labels else json.dumps(['暂无数据'])};
        const modulePassRateValues = {json.dumps(module_pass_rate_values) if module_pass_rate_values else json.dumps([0])};
        // 根据通过率生成颜色（0-100%映射到红色到绿色）
        const heatmapColors = modulePassRateValues.map(function(rate) {{
            // 通过率越高，绿色成分越多
            const red = Math.max(0, 255 - (rate * 2.55));
            const green = Math.min(255, rate * 2.55);
            const blue = 0;
            return `rgba(${{red}}, ${{green}}, ${{blue}}, 0.8)`;
        }});
        
        new Chart(heatmapCtx, {{
            type: 'bar',
            data: {{
                labels: moduleLabels,
                datasets: [{{
                    label: '通过率 (%)',
                    data: modulePassRateValues,
                    backgroundColor: heatmapColors,
                    borderColor: heatmapColors.map(c => c.replace('0.8', '1')),
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top',
                        labels: {{
                            font: {{
                                size: 14
                            }}
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return '通过率: ' + context.parsed.y.toFixed(1) + '%';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }},
                            font: {{
                                size: 12
                            }}
                        }},
                        grid: {{
                            color: 'rgba(0, 0, 0, 0.05)'
                        }}
                    }},
                    x: {{
                        ticks: {{
                            font: {{
                                size: 12
                            }}
                        }},
                        grid: {{
                            display: false
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        
        # 保存文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    @staticmethod
    def _get_trend_data(count: int = 10) -> List[Dict]:
        """获取历史趋势数据
        
        Args:
            count: 获取最近N次执行的数据
            
        Returns:
            趋势数据列表
        """
        try:
            from core.test_result_analyzer import TestResultAnalyzer
            from core.db_client import DBClient
            
            try:
                db_client = DBClient()
                db_client.connect()
                analyzer = TestResultAnalyzer(db_client)
            except:
                analyzer = TestResultAnalyzer()
            
            # 获取最近30天的数据，然后取前N次
            trend_data = analyzer.get_trend_data(30)
            return trend_data[:count] if trend_data else []
        except Exception as e:
            # 如果获取失败，返回空列表
            return []
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化执行时长
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化后的时长字符串
        """
        if seconds < 60:
            return f"{seconds:.2f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}分{secs:.2f}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}小时{minutes}分{secs:.2f}秒"
    
    @staticmethod
    def parse_pytest_json_report(json_path: Path) -> Dict[str, Any]:
        """解析pytest的JSON报告（如果使用--json-report）
        
        Args:
            json_path: JSON报告文件路径
            
        Returns:
            解析后的测试结果字典
        """
        if not json_path.exists():
            return {}
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            result = {
                'total': data.get('summary', {}).get('total', 0),
                'passed': data.get('summary', {}).get('passed', 0),
                'failed': data.get('summary', {}).get('failed', 0),
                'skipped': data.get('summary', {}).get('skipped', 0),
                'duration': data.get('duration', 0),
                'test_cases': []
            }
            
            # 解析测试用例
            for test in data.get('tests', []):
                result['test_cases'].append({
                    'name': test.get('nodeid', ''),
                    'status': test.get('outcome', 'unknown'),
                    'duration': test.get('duration', 0),
                    'error': test.get('call', {}).get('longrepr', '') if test.get('outcome') == 'failed' else ''
                })
            
            return result
        except Exception as e:
            print(f"解析JSON报告失败: {e}")
            return {}

