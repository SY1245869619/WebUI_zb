"""
授课教学应用页面对象
"""
from pages.base_page import BasePage
from core.web_ui_driver import WebUIDriver


class TeachingApp(BasePage):
    """授课教学应用页面类"""
    
    def __init__(self, driver: WebUIDriver):
        """初始化授课教学应用页面
        
        Args:
            driver: WebUI驱动实例
        """
        super().__init__(driver)
        self.app_modal_selector = '.teaching-app-modal, .app-modal[data-app="teaching"]'
    
    async def wait_for_load(self, timeout: int = 10000):
        """等待应用弹窗加载"""
        await self.driver.wait_for_selector(self.app_modal_selector, timeout=timeout)
    
    async def is_app_opened(self) -> bool:
        """检查应用是否已打开
        
        Returns:
            是否已打开
        """
        return await self.is_element_visible(self.app_modal_selector)
    
    async def start_teaching(self):
        """开始授课"""
        # 示例：点击开始授课按钮
        await self.driver.click('button:has-text("开始授课"), .start-teaching-btn')
    
    async def select_course(self, course_name: str):
        """选择课程
        
        Args:
            course_name: 课程名称
        """
        # 示例：选择课程
        await self.driver.click(f'[data-course="{course_name}"]')
        await self.page.wait_for_timeout(500)
    
    async def close_app(self):
        """关闭应用"""
        await self.driver.click('.app-close, .modal-close, [aria-label="关闭"]')

