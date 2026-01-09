"""
桌面页面对象
处理Web桌面相关操作，如点击图标打开应用

@File  : desktop_page.py
@Author: shenyuan
"""
import yaml
import asyncio
import re
from pathlib import Path
from typing import Optional
from pages.base_page import BasePage
from core.web_ui_driver import WebUIDriver


class DesktopPage(BasePage):
    """桌面页面类"""
    
    def __init__(self, driver: WebUIDriver, module_config_path: str = "config/module_config.yaml", settings_config_path: str = "config/settings.yaml"):
        """初始化桌面页面
        
        Args:
            driver: WebUI驱动实例
            module_config_path: 模块配置文件路径
            settings_config_path: 设置配置文件路径（用于获取登录配置）
        """
        super().__init__(driver)
        self.module_config = self._load_config(module_config_path)
        self.settings_config = self._load_config(settings_config_path)
        # 从登录配置动态获取桌面URL
        self.base_url = self._get_desktop_url()
        self.icon_selector = self.module_config.get('desktop', {}).get('icon_selector', '.desktop-icon')
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _get_desktop_url(self) -> str:
        """从登录配置动态获取桌面URL
        
        桌面URL从登录URL推导：
        - 如果登录URL包含 #/login，替换为 #/index
        - 如果登录URL不包含 #，添加 #/index
        - 如果登录URL包含其他路径，保持基础URL并添加 #/index
        
        Returns:
            桌面URL
        """
        login_url = self.settings_config.get('login', {}).get('url', '')
        if not login_url:
            # 如果登录URL不存在，尝试从module_config获取（向后兼容）
            return self.module_config.get('desktop', {}).get('base_url', '')
        
        # 处理登录URL，推导桌面URL
        # 移除 #/login 部分
        if '#/login' in login_url:
            desktop_url = login_url.replace('#/login', '#/index')
        elif '#/index' in login_url:
            # 如果已经是桌面URL，直接返回
            desktop_url = login_url
        elif '#' in login_url:
            # 如果包含其他hash，替换为 #/index
            desktop_url = re.sub(r'#.*', '#/index', login_url)
        else:
            # 如果没有hash，添加 #/index
            desktop_url = login_url + '#/index'
        
        return desktop_url
    
    async def open_desktop(self):
        """打开桌面页面
        
        注意：如果已经登录，通常不需要调用此方法，因为登录后会自动跳转到桌面。
        此方法主要用于手动导航到桌面。
        """
        await self.driver.goto(self.base_url)
        await self.wait_for_load()
    
    async def wait_for_load(self, timeout: Optional[int] = None):
        """等待桌面加载完成"""
        # 检查页面是否有效
        if not self.page or self.page.is_closed():
            raise RuntimeError("页面已关闭或无效")
        
        # 先等待页面基本加载完成
        try:
            await self.page.wait_for_load_state('domcontentloaded', timeout=5000)
        except:
            pass
        
        # 等待桌面容器加载，使用简单的等待策略，避免事件循环问题
        timeout = timeout or 10000
        max_attempts = timeout // 500  # 每500ms检查一次
        
        for attempt in range(max_attempts):
            try:
                # 使用简单的元素检查，避免复杂的等待逻辑
                locator = self.page.locator('.desktop-container, .desktop, [class*="desktop"]').first
                if await self._check_element_visible(locator, timeout=500):
                    return  # 找到了，直接返回
            except:
                pass
            
            # 等待一小段时间再重试
            await asyncio.sleep(0.5)
        
        # 如果所有尝试都失败，尝试最后一次检查
        try:
            locator = self.page.locator('.desktop-container, .desktop, [class*="desktop"]').first
            if await self._check_element_visible(locator, timeout=1000):
                return
        except:
            pass
        
        # 如果还是找不到，可能页面结构不同，不抛出异常，让调用者继续
    
    async def _check_element_visible(self, locator, timeout: int = 5000) -> bool:
        """检查元素是否可见（不使用is_visible API，避免事件循环问题）
        
        Args:
            locator: Playwright locator对象
            timeout: 超时时间（毫秒）
        
        Returns:
            是否可见
        """
        max_attempts = timeout // 500
        for attempt in range(max_attempts):
            try:
                # 使用count和bounding_box来检查元素是否存在和可见
                count = await locator.count()
                if count > 0:
                    box = await locator.bounding_box()
                    if box and box.get('width', 0) > 0 and box.get('height', 0) > 0:
                        return True
            except:
                pass
            await asyncio.sleep(0.5)
        return False
    
    async def click_app_icon(self, app_name: str, double_click: bool = True):
        """点击应用图标
        
        Args:
            app_name: 应用名称（如：授课教学、攻防演练、考试测评）
            double_click: 是否双击，默认True
        """
        # 检查页面是否有效
        if not self.page or self.page.is_closed():
            raise RuntimeError("页面已关闭或无效")
        
        print(f"[DesktopPage] 开始点击应用图标: {app_name}")
        
        # 先尝试关闭可能的弹窗（如磁盘空间不足提示）
        try:
            close_selectors = [
                'button:has-text("知道了")',
                'button:has-text("关闭")',
                '.close',
                '.modal-close',
                '[aria-label="关闭"]',
            ]
            for selector in close_selectors:
                try:
                    close_btn = self.page.locator(selector).first
                    if await close_btn.is_visible(timeout=1000):
                        await close_btn.click()
                        await asyncio.sleep(0.5)
                        print(f"[DesktopPage] 已关闭弹窗: {selector}")
                        break
                except:
                    continue
        except:
            pass
        
        # 直接使用 Playwright 的 get_by_text API（与 login_page.py 中相同的方法）
        # 这是最简单、最可靠的方法
        try:
            if double_click:
                await self.page.get_by_text(app_name).dblclick()
            else:
                await self.page.get_by_text(app_name).click()
            print(f"[DesktopPage] [OK] 成功点击应用图标: {app_name}")
            await asyncio.sleep(1.0)
            return
        except Exception as e:
            print(f"[DesktopPage] [ERROR] 直接点击失败: {e}")
            raise Exception(f"无法点击应用图标: {app_name}。错误: {e}")
    
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

