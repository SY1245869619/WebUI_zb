"""
登录页面对象
处理Web平台登录相关操作

@File  : login_page.py
@Author: shenyuan
"""
import yaml
import logging
import sys
import io
from pathlib import Path
from typing import Optional
from pages.base_page import BasePage
from core.web_ui_driver import WebUIDriver

# 创建logger用于记录登录日志
logger = logging.getLogger(__name__)
# 确保logger使用UTF-8编码
logger.setLevel(logging.INFO)
# 不添加自己的handler，只使用根logger的handler，避免重复输出
# 设置propagate=True让日志传播到根logger，由根logger统一处理
logger.propagate = True


class LoginPage(BasePage):
    """登录页面类"""
    
    def __init__(self, driver: WebUIDriver, config_path: str = "config/settings.yaml"):
        """初始化登录页面
        
        Args:
            driver: WebUI驱动实例
            config_path: 配置文件路径
        """
        super().__init__(driver)
        self.config = self._load_config(config_path)
        self.login_url = self.config['login']['url']
        self.username = self.config['login']['username']
        self.password = self.config['login']['password']
        self.username_selector = self.config['login']['username_selector']
        self.password_selector = self.config['login']['password_selector']
        self.login_button_selector = self.config['login']['login_button_selector']
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    async def open_login_page(self):
        """打开登录页面"""
        await self.driver.goto(self.login_url)
        await self.wait_for_load()
    
    async def wait_for_load(self, timeout: Optional[int] = None):
        """等待登录页面加载完成"""
        # 等待登录表单加载
        try:
            # 尝试等待用户名输入框或密码输入框
            await self.driver.wait_for_selector(
                f'{self.username_selector}, {self.password_selector}',
                timeout=timeout or 10000
            )
        except:
            # 如果找不到，等待页面加载完成
            await self.page.wait_for_load_state('networkidle')
    
    async def input_username(self, username: Optional[str] = None):
        """输入用户名
        
        Args:
            username: 用户名，如果为None则使用配置中的用户名
        """
        username = username or self.username
        # 尝试多种选择器定位用户名输入框
        selectors = self.username_selector.split(', ')
        
        for selector in selectors:
            try:
                if await self.is_element_visible(selector.strip(), timeout=3000):
                    await self.driver.fill(selector.strip(), username)
                    return
            except:
                continue
        
        # 如果都找不到，尝试通过文本定位
        try:
            await self.page.fill('input[type="text"]', username)
        except Exception as e:
            raise Exception(f"无法找到用户名输入框，错误: {e}")
    
    async def input_password(self, password: Optional[str] = None):
        """输入密码
        
        Args:
            password: 密码，如果为None则使用配置中的密码
        """
        password = password or self.password
        # 尝试多种选择器定位密码输入框
        selectors = self.password_selector.split(', ')
        
        for selector in selectors:
            try:
                if await self.is_element_visible(selector.strip(), timeout=3000):
                    await self.driver.fill(selector.strip(), password)
                    return
            except:
                continue
        
        # 如果都找不到，尝试通过类型定位
        try:
            await self.page.fill('input[type="password"]', password)
        except Exception as e:
            raise Exception(f"无法找到密码输入框，错误: {e}")
    
    async def click_login_button(self):
        """点击登录按钮"""
        # 尝试多种选择器定位登录按钮
        selectors = self.login_button_selector.split(', ')
        
        for selector in selectors:
            try:
                if await self.is_element_visible(selector.strip(), timeout=3000):
                    await self.driver.click(selector.strip())
                    return
            except:
                continue
        
        # 如果都找不到，尝试通过文本定位
        try:
            await self.page.click('button:has-text("登录")')
        except:
            # 最后尝试提交表单
            try:
                await self.page.keyboard.press('Enter')
            except Exception as e:
                raise Exception(f"无法找到登录按钮，错误: {e}")
    
    async def login(self, username: Optional[str] = None, password: Optional[str] = None):
        """执行完整登录流程
        
        Args:
            username: 用户名，如果为None则使用配置中的用户名
            password: 密码，如果为None则使用配置中的密码
        """
        username = username or self.username
        password = password or self.password
        
        # 打开登录页面
        await self.open_login_page()
        
        # 使用用户提供的具体步骤进行登录
        try:
            # 点击账号输入框
            await self.page.get_by_role("textbox", name="请输入账号").click()
            # 输入账号
            await self.page.get_by_role("textbox", name="请输入账号").fill(username)
            # 全选并复制（用户提供的步骤，可能用于某些特殊场景）
            await self.page.get_by_role("textbox", name="请输入账号").press("ControlOrMeta+a")
            await self.page.get_by_role("textbox", name="请输入账号").press("ControlOrMeta+c")
            
            # 点击密码输入框
            await self.page.get_by_role("textbox", name="请输入密码").click()
            # 输入密码
            await self.page.get_by_role("textbox", name="请输入密码").fill(password)
            
            # 点击登录按钮
            await self.page.get_by_role("button", name="登录").click()
            
            # 等待登录完成（使用 asyncio.sleep 避免事件循环问题）
            import asyncio
            await asyncio.sleep(2)
            
            # 点击"跳过了解"按钮（如果存在）
            try:
                skip_button = self.page.get_by_role("button", name="跳过了解")
                if await skip_button.is_visible(timeout=3000):
                    await skip_button.click()
                    import asyncio
                    await asyncio.sleep(1)
            except:
                # 如果找不到"跳过了解"按钮，说明可能已经跳过或不存在，继续执行
                pass
        except Exception as e:
            # 如果使用get_by_role失败，回退到原来的方法
            await self.input_username(username)
            await self.input_password(password)
            await self.click_login_button()
            import asyncio
            await asyncio.sleep(2)
            
            # 尝试点击"跳过了解"按钮
            try:
                skip_button = self.page.get_by_role("button", name="跳过了解")
                if await skip_button.is_visible(timeout=3000):
                    await skip_button.click()
                    await asyncio.sleep(1)
            except:
                pass
        
        # 验证是否登录成功
        try:
            # 等待登录后的页面元素出现（如桌面图标）
            import asyncio
            await asyncio.sleep(2)  # 等待页面跳转
            
            # 检查是否成功跳转到桌面
            current_url = self.page.url
            logger.info(f"[LoginPage] 登录后 URL: {current_url}")
            
            # 如果还在登录页面，说明登录可能失败
            if 'login' in current_url.lower():
                logger.warning("[LoginPage] [WARNING] 登录后仍在登录页面，可能登录失败")
            else:
                logger.info("[LoginPage] 登录成功，已跳转到桌面")
        except Exception as e:
            logger.error(f"[LoginPage] 验证登录状态时出错: {e}")
    
    async def is_logged_in(self) -> bool:
        """检查是否已登录
        
        Returns:
            是否已登录
        """
        # 可以根据实际页面调整判断逻辑
        # 例如：检查是否存在桌面元素、用户信息等
        try:
            # 如果URL包含login，说明还在登录页
            current_url = self.page.url
            if 'login' in current_url.lower():
                return False
            
            # 检查是否存在桌面相关元素
            desktop_selectors = [
                '.desktop',
                '.desktop-container',
                '[class*="desktop"]',
                '.app-icon'
            ]
            
            for selector in desktop_selectors:
                try:
                    if await self.is_element_visible(selector, timeout=2000):
                        return True
                except:
                    continue
            
            return False
        except:
            return False

