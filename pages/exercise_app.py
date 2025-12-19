"""
攻防演练应用页面对象
"""
from pages.base_page import BasePage
from core.web_ui_driver import WebUIDriver


class ExerciseApp(BasePage):
    """攻防演练应用页面类"""
    
    def __init__(self, driver: WebUIDriver):
        """初始化攻防演练应用页面
        
        Args:
            driver: WebUI驱动实例
        """
        super().__init__(driver)
        self.app_modal_selector = '.exercise-app-modal, .app-modal[data-app="exercise"]'
    
    async def wait_for_load(self, timeout: int = 10000):
        """等待应用弹窗加载"""
        await self.driver.wait_for_selector(self.app_modal_selector, timeout=timeout)
    
    async def is_app_opened(self) -> bool:
        """检查应用是否已打开
        
        Returns:
            是否已打开
        """
        return await self.is_element_visible(self.app_modal_selector)
    
    async def start_exercise(self, exercise_type: str = "攻防演练"):
        """开始演练
        
        Args:
            exercise_type: 演练类型
        """
        await self.driver.click('button:has-text("开始演练"), .start-exercise-btn')
        await self.page.wait_for_timeout(500)
    
    async def select_scenario(self, scenario_name: str):
        """选择演练场景
        
        Args:
            scenario_name: 场景名称
        """
        await self.driver.click(f'[data-scenario="{scenario_name}"]')
    
    async def close_app(self):
        """关闭应用"""
        await self.driver.click('.app-close, .modal-close, [aria-label="关闭"]')

