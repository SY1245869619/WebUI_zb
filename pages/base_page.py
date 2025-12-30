"""
基础页面类
所有页面对象的基类

@File  : base_page.py
@Author: shenyuan
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
    
    async def take_screenshot(self, filename: str = None):
        """截图（使用统一的截图工具）
        
        Args:
            filename: 文件名（可选，如果不提供则自动生成）
            
        Returns:
            截图文件路径
        """
        from utils.screenshot_utils import take_screenshot
        return await take_screenshot(self.page, filename)
    
    async def take_error_screenshot(self, error_message: str = ""):
        """在发生错误时截图
        
        Args:
            error_message: 错误信息
            
        Returns:
            截图文件路径
        """
        from utils.screenshot_utils import take_error_screenshot
        return await take_error_screenshot(self.page, error_message)
    
    async def take_success_screenshot(self, step_name: str = ""):
        """在特定步骤成功时截图
        
        Args:
            step_name: 步骤名称
            
        Returns:
            截图文件路径
        """
        from utils.screenshot_utils import take_success_screenshot
        return await take_success_screenshot(self.page, step_name)
    
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

