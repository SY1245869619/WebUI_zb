"""
基础页面类
所有页面对象的基类
"""
from typing import Optional
from core.web_ui_driver import WebUIDriver


class BasePage:
    """页面基类"""
    
    def __init__(self, driver: WebUIDriver):
        """初始化页面对象
        
        Args:
            driver: WebUI驱动实例
        """
        self.driver = driver
    
    @property
    def page(self):
        """获取Playwright Page对象"""
        return self.driver.page
    
    async def wait_for_load(self, timeout: Optional[int] = None):
        """等待页面加载完成"""
        # 子类可以重写此方法
        pass
    
    async def take_screenshot(self, filename: str):
        """截图
        
        Args:
            filename: 文件名
        """
        await self.driver.screenshot(filename)
    
    async def is_element_visible(self, selector: str, timeout: int = 5000) -> bool:
        """检查元素是否可见
        
        Args:
            selector: 元素选择器
            timeout: 超时时间
            
        Returns:
            是否可见
        """
        try:
            await self.driver.wait_for_selector(selector, timeout=timeout, state="visible")
            return True
        except:
            return False

