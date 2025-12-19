"""
考试测评应用页面对象
"""
from pages.base_page import BasePage
from core.web_ui_driver import WebUIDriver


class ExamApp(BasePage):
    """考试测评应用页面类"""
    
    def __init__(self, driver: WebUIDriver):
        """初始化考试测评应用页面
        
        Args:
            driver: WebUI驱动实例
        """
        super().__init__(driver)
        self.app_modal_selector = '.exam-app-modal, .app-modal[data-app="exam"]'
    
    async def wait_for_load(self, timeout: int = 10000):
        """等待应用弹窗加载"""
        await self.driver.wait_for_selector(self.app_modal_selector, timeout=timeout)
    
    async def is_app_opened(self) -> bool:
        """检查应用是否已打开
        
        Returns:
            是否已打开
        """
        return await self.is_element_visible(self.app_modal_selector)
    
    async def create_exam(self, exam_name: str):
        """创建考试
        
        Args:
            exam_name: 考试名称
        """
        await self.driver.click('button:has-text("创建考试"), .create-exam-btn')
        await self.page.wait_for_timeout(500)
        await self.driver.fill('input[name="exam_name"], .exam-name-input', exam_name)
    
    async def start_exam(self, exam_id: str):
        """开始考试
        
        Args:
            exam_id: 考试ID
        """
        await self.driver.click(f'[data-exam-id="{exam_id}"]')
        await self.driver.click('button:has-text("开始考试")')
    
    async def close_app(self):
        """关闭应用"""
        await self.driver.click('.app-close, .modal-close, [aria-label="关闭"]')

