"""
桌面页面对象
处理Web桌面相关操作，如点击图标打开应用
"""
import yaml
from pathlib import Path
from typing import Optional
from pages.base_page import BasePage
from core.web_ui_driver import WebUIDriver


class DesktopPage(BasePage):
    """桌面页面类"""
    
    def __init__(self, driver: WebUIDriver, config_path: str = "config/module_config.yaml"):
        """初始化桌面页面
        
        Args:
            driver: WebUI驱动实例
            config_path: 模块配置文件路径
        """
        super().__init__(driver)
        self.config = self._load_config(config_path)
        self.base_url = self.config['desktop']['base_url']
        self.icon_selector = self.config['desktop']['icon_selector']
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    async def open_desktop(self):
        """打开桌面页面"""
        await self.driver.goto(self.base_url)
        await self.wait_for_load()
    
    async def wait_for_load(self, timeout: Optional[int] = None):
        """等待桌面加载完成"""
        # 等待桌面容器加载
        await self.driver.wait_for_selector('.desktop-container, .desktop, [class*="desktop"]', timeout=timeout)
    
    async def click_app_icon(self, app_name: str, double_click: bool = True):
        """点击应用图标
        
        Args:
            app_name: 应用名称（如：授课教学、攻防演练、考试测评）
            double_click: 是否双击，默认True
        """
        # 根据应用名称查找图标
        # 可以使用多种定位方式：文本、图标标题等
        icon_selectors = [
            f'[title="{app_name}"]',
            f'[aria-label="{app_name}"]',
            f'.app-icon:has-text("{app_name}")',
            f'[data-app="{app_name}"]',
        ]
        
        icon_found = False
        for selector in icon_selectors:
            try:
                if await self.is_element_visible(selector, timeout=3000):
                    if double_click:
                        await self.page.dblclick(selector)
                    else:
                        await self.driver.click(selector)
                    icon_found = True
                    break
            except:
                continue
        
        if not icon_found:
            # 如果找不到，尝试通过文本定位
            try:
                await self.page.click(f'text="{app_name}"')
                if double_click:
                    await self.page.dblclick(f'text="{app_name}"')
            except Exception as e:
                raise Exception(f"无法找到应用图标: {app_name}, 错误: {e}")
        
        # 等待应用弹窗打开
        await self.page.wait_for_timeout(1000)
    
    async def close_all_apps(self):
        """关闭所有打开的应用弹窗"""
        close_selectors = [
            '.app-close',
            '.modal-close',
            '[aria-label="关闭"]',
            '.close-button',
            'button:has-text("关闭")',
        ]
        
        for selector in close_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    try:
                        await element.click(timeout=1000)
                    except:
                        pass
            except:
                pass
    
    async def get_app_icon_count(self) -> int:
        """获取桌面图标数量
        
        Returns:
            图标数量
        """
        try:
            icons = await self.page.query_selector_all(self.icon_selector)
            return len(icons)
        except:
            return 0

