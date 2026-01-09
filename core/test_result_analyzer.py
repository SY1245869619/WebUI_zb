"""
测试结果趋势分析器
存储和分析历史测试结果

@File  : test_result_analyzer.py
@Author: shenyuan
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from core.db_client import DBClient


class TestResultAnalyzer:
    """测试结果分析器"""
    
    def __init__(self, db_client: Optional[DBClient] = None):
        """初始化分析器
        
        Args:
            db_client: 数据库客户端（可选，如果提供则使用数据库存储）
        """
        self.db_client = db_client
        self.results_dir = Path("test_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # 如果使用数据库，创建结果表
        if self.db_client:
            self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        if not self.db_client:
            return
        
        try:
            # 检查表是否存在
            if not self.db_client.table_exists('test_results'):
                # 创建测试结果表
                create_table_sql = """
                CREATE TABLE test_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    execution_time DATETIME NOT NULL,
                    modules VARCHAR(500),
                    total INT DEFAULT 0,
                    passed INT DEFAULT 0,
                    failed INT DEFAULT 0,
                    skipped INT DEFAULT 0,
                    duration FLOAT DEFAULT 0,
                    pass_rate FLOAT DEFAULT 0,
                    report_path VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_execution_time (execution_time),
                    INDEX idx_modules (modules)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
                self.db_client.execute_update(create_table_sql)
        except Exception as e:
            print(f"初始化数据库表失败: {e}")
    
    def save_result(
        self,
        modules: List[str],
        total: int,
        passed: int,
        failed: int,
        skipped: int,
        duration: float,
        report_path: Optional[str] = None
    ):
        """保存测试结果
        
        Args:
            modules: 执行的模块列表
            total: 总用例数
            passed: 通过数
            failed: 失败数
            skipped: 跳过数
            duration: 执行时长
            report_path: 报告路径
        """
        execution_time = datetime.now()
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        result = {
            'execution_time': execution_time.isoformat(),
            'modules': ','.join(modules),
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'duration': duration,
            'pass_rate': pass_rate,
            'report_path': report_path
        }
        
        # 保存到文件
        result_file = self.results_dir / f"result_{execution_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 如果使用数据库，也保存到数据库
        if self.db_client:
            try:
                insert_sql = """
                INSERT INTO test_results 
                (execution_time, modules, total, passed, failed, skipped, duration, pass_rate, report_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                self.db_client.execute_update(
                    insert_sql,
                    (
                        execution_time,
                        ','.join(modules),
                        total,
                        passed,
                        failed,
                        skipped,
                        duration,
                        pass_rate,
                        report_path
                    )
                )
            except Exception as e:
                print(f"保存测试结果到数据库失败: {e}")
    
    def get_trend_data(self, days: int = 30) -> List[Dict]:
        """获取趋势数据
        
        Args:
            days: 查询最近N天的数据
            
        Returns:
            结果列表
        """
        start_date = datetime.now() - timedelta(days=days)
        
        if self.db_client:
            # 从数据库查询
            try:
                sql = """
                SELECT * FROM test_results 
                WHERE execution_time >= %s 
                ORDER BY execution_time DESC
                """
                results = self.db_client.execute_query(sql, (start_date,))
                return [
                    {
                        'execution_time': r['execution_time'].isoformat() if hasattr(r['execution_time'], 'isoformat') else str(r['execution_time']),
                        'modules': r['modules'],
                        'total': r['total'],
                        'passed': r['passed'],
                        'failed': r['failed'],
                        'skipped': r['skipped'],
                        'duration': r['duration'],
                        'pass_rate': r['pass_rate'],
                        'report_path': r['report_path']
                    }
                    for r in results
                ]
            except Exception as e:
                print(f"从数据库查询趋势数据失败: {e}")
        
        # 从文件查询
        results = []
        for result_file in sorted(self.results_dir.glob("result_*.json"), reverse=True):
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                    exec_time = datetime.fromisoformat(result['execution_time'])
                    if exec_time >= start_date:
                        results.append(result)
            except:
                continue
        
        # 如果文件结果为空，尝试从已有报告中解析
        if not results:
            results = self._parse_from_reports()
        
        return results[:100]  # 最多返回100条
    
    def _parse_from_reports(self) -> List[Dict]:
        """从已有报告中解析数据"""
        from utils.report_parser import ReportParser
        
        results = []
        reports_dir = Path("reports")
        if not reports_dir.exists():
            return results
        
        parser = ReportParser()
        
        # 查找所有报告文件
        report_files = sorted(
            list(reports_dir.glob("WebUI自动化测试报告_*.html")) + list(reports_dir.glob("pytest测试报告_*.html")),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:30]  # 最多解析30个报告
        
        for report_file in report_files:
            try:
                # 从文件名提取时间
                # 格式：WebUI自动化测试报告_20251230_105832.html
                name_parts = report_file.stem.split('_')
                if len(name_parts) >= 3:
                    date_str = name_parts[-2]  # 20251230
                    time_str = name_parts[-1]  # 105832
                    try:
                        exec_time = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    except:
                        exec_time = datetime.fromtimestamp(report_file.stat().st_mtime)
                else:
                    exec_time = datetime.fromtimestamp(report_file.stat().st_mtime)
                
                # 解析报告
                stats = parser.parse_html_report(report_file)
                if stats:
                    results.append({
                        'execution_time': exec_time.isoformat(),
                        'modules': 'unknown',
                        'total': stats.get('total', 0),
                        'passed': stats.get('passed', 0),
                        'failed': stats.get('failed', 0),
                        'skipped': stats.get('skipped', 0),
                        'duration': stats.get('duration', 0),
                        'pass_rate': (stats.get('passed', 0) / stats.get('total', 1) * 100) if stats.get('total', 0) > 0 else 0,
                        'report_path': str(report_file)
                    })
            except Exception as e:
                print(f"解析报告失败 {report_file}: {e}")
                continue
        
        return results
    
    def get_statistics(self, days: int = 30) -> Dict:
        """获取统计信息
        
        Args:
            days: 统计最近N天的数据
            
        Returns:
            统计字典
        """
        trend_data = self.get_trend_data(days)
        
        if not trend_data:
            return {
                'total_executions': 0,
                'avg_pass_rate': 0,
                'avg_duration': 0,
                'total_tests': 0,
                'total_passed': 0,
                'total_failed': 0
            }
        
        total_executions = len(trend_data)
        avg_pass_rate = sum(r['pass_rate'] for r in trend_data) / total_executions
        avg_duration = sum(r['duration'] for r in trend_data) / total_executions
        total_tests = sum(r['total'] for r in trend_data)
        total_passed = sum(r['passed'] for r in trend_data)
        total_failed = sum(r['failed'] for r in trend_data)
        
        return {
            'total_executions': total_executions,
            'avg_pass_rate': round(avg_pass_rate, 2),
            'avg_duration': round(avg_duration, 2),
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'overall_pass_rate': round((total_passed / total_tests * 100) if total_tests > 0 else 0, 2)
        }

