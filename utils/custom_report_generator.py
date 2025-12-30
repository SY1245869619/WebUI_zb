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
        
        .test-cases {{
            margin-top: 40px;
        }}
        
        .test-cases h2 {{
            font-size: 24px;
            margin-bottom: 20px;
            color: #212529;
        }}
        
        .test-case {{
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            border-left: 4px solid #667eea;
            transition: all 0.3s;
        }}
        
        .test-case:hover {{
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .test-case.passed {{
            border-left-color: #38ef7d;
        }}
        
        .test-case.failed {{
            border-left-color: #ff6a00;
            background: #fff5f5;
        }}
        
        .test-case.skipped {{
            border-left-color: #f5576c;
        }}
        
        .test-case-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .test-case-name {{
            font-size: 16px;
            font-weight: 600;
            color: #212529;
            flex: 1;
        }}
        
        .test-case-status {{
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        }}
        
        .test-case-status.passed {{
            background: #d4edda;
            color: #155724;
        }}
        
        .test-case-status.failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .test-case-status.skipped {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .test-case-details {{
            display: flex;
            gap: 20px;
            font-size: 14px;
            color: #6c757d;
            margin-top: 12px;
        }}
        
        .test-case-error {{
            margin-top: 16px;
            padding: 16px;
            background: #fff5f5;
            border-left: 4px solid #ff6a00;
            border-radius: 8px;
            font-family: "Consolas", "Monaco", monospace;
            font-size: 13px;
            color: #721c24;
            white-space: pre-wrap;
            word-break: break-all;
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
            
            <!-- 测试用例列表 -->
            <div class="test-cases">
                <h2>测试用例详情</h2>
"""
        
        # 添加测试用例
        test_cases = test_results.get('test_cases', [])
        if test_cases:
            for case in test_cases:
                case_name = case.get('name', '未知用例')
                case_status = case.get('status', 'unknown')
                case_duration = case.get('duration', 0)
                case_error = case.get('error', '')
                
                status_text = {
                    'passed': '通过',
                    'failed': '失败',
                    'skipped': '跳过'
                }.get(case_status, case_status)
                
                duration_str = CustomReportGenerator._format_duration(case_duration)
                
                html_content += f"""
                <div class="test-case {case_status}">
                    <div class="test-case-header">
                        <div class="test-case-name">{case_name}</div>
                        <div class="test-case-status {case_status}">{status_text}</div>
                    </div>
                    <div class="test-case-details">
                        <span>⏱️ 执行时长: {duration_str}</span>
                    </div>
"""
                if case_error:
                    # HTML转义错误信息
                    case_error = case_error.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    html_content += f"""
                    <div class="test-case-error">{case_error}</div>
"""
                html_content += """
                </div>
"""
        else:
            html_content += """
                <div style="text-align: center; padding: 40px; color: #6c757d;">
                    <p>暂无测试用例详情</p>
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
</body>
</html>
"""
        
        # 保存文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
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

