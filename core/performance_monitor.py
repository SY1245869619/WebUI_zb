"""
性能监控模块
收集页面性能指标

@File  : performance_monitor.py
@Author: shenyuan
"""
from typing import Dict, Optional
from playwright.async_api import Page
import json


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        """初始化性能监控器"""
        self.metrics: Dict[str, Dict] = {}
    
    async def collect_metrics(self, page: Page, test_name: str) -> Dict:
        """收集页面性能指标
        
        Args:
            page: Playwright页面对象
            test_name: 测试用例名称
            
        Returns:
            性能指标字典
        """
        try:
            # 获取性能指标
            metrics = await page.evaluate("""
                () => {
                    const perfData = window.performance.timing;
                    const navigation = perfData;
                    
                    return {
                        // 页面加载时间
                        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.navigationStart,
                        loadComplete: navigation.loadEventEnd - navigation.navigationStart,
                        
                        // 资源加载时间
                        domInteractive: navigation.domInteractive - navigation.navigationStart,
                        domComplete: navigation.domComplete - navigation.navigationStart,
                        
                        // 网络时间
                        dns: navigation.domainLookupEnd - navigation.domainLookupStart,
                        tcp: navigation.connectEnd - navigation.connectStart,
                        request: navigation.responseStart - navigation.requestStart,
                        response: navigation.responseEnd - navigation.responseStart,
                        
                        // 渲染时间
                        render: navigation.domContentLoadedEventEnd - navigation.responseEnd,
                        processing: navigation.domComplete - navigation.domInteractive
                    };
                }
            """)
            
            # 获取资源加载信息
            resources = await page.evaluate("""
                () => {
                    const resources = window.performance.getEntriesByType('resource');
                    return resources.map(r => ({
                        name: r.name,
                        type: r.initiatorType,
                        duration: r.duration,
                        size: r.transferSize || 0
                    }));
                }
            """)
            
            metrics['resources'] = resources
            metrics['resource_count'] = len(resources)
            metrics['total_size'] = sum(r.get('size', 0) for r in resources)
            
            # 保存指标
            self.metrics[test_name] = metrics
            
            return metrics
        except Exception as e:
            print(f"收集性能指标失败: {e}")
            return {}
    
    def get_metrics(self, test_name: str) -> Optional[Dict]:
        """获取测试用例的性能指标
        
        Args:
            test_name: 测试用例名称
            
        Returns:
            性能指标字典
        """
        return self.metrics.get(test_name)
    
    def get_all_metrics(self) -> Dict[str, Dict]:
        """获取所有性能指标
        
        Returns:
            所有指标字典
        """
        return self.metrics
    
    def export_metrics(self, output_path: str):
        """导出性能指标到JSON文件
        
        Args:
            output_path: 输出文件路径
        """
        import json
        from pathlib import Path
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, ensure_ascii=False, indent=2)

