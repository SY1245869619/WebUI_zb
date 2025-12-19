"""
Playwright浏览器驱动封装
提供统一的浏览器操作接口，支持重试机制和错误处理
"""
import asyncio
from typing import Optional, Callable, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
import yaml
import os
from pathlib import Path


class WebUIDriver:
    """WebUI驱动类，封装Playwright操作"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """初始化驱动
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    async def start(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        browser_type = getattr(self.playwright, self.config['playwright']['browser'])
        
        self.browser = await browser_type.launch(
            headless=self.config['playwright']['headless'],
            slow_mo=self.config['playwright']['slow_mo']
        )
        
        self.context = await self.browser.new_context(
            viewport={
                'width': self.config['playwright']['viewport']['width'],
                'height': self.config['playwright']['viewport']['height']
            }
        )
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.config['playwright']['timeout'])
        
    async def close(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def goto(self, url: str, wait_until: str = "networkidle"):
        """导航到指定URL
        
        Args:
            url: 目标URL
            wait_until: 等待条件 (load, domcontentloaded, networkidle, commit)
        """
        if not self.page:
            raise RuntimeError("浏览器未启动，请先调用start()")
        await self.page.goto(url, wait_until=wait_until)
    
    async def click(self, selector: str, timeout: Optional[int] = None, retry: int = 3):
        """点击元素，支持重试
        
        Args:
            selector: 元素选择器
            timeout: 超时时间
            retry: 重试次数
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")
        
        timeout = timeout or self.config['playwright']['timeout']
        
        for attempt in range(retry):
            try:
                await self.page.click(selector, timeout=timeout)
                return
            except Exception as e:
                if attempt == retry - 1:
                    raise
                await asyncio.sleep(0.5)
    
    async def fill(self, selector: str, text: str, timeout: Optional[int] = None):
        """填充输入框
        
        Args:
            selector: 元素选择器
            text: 要输入的文本
            timeout: 超时时间
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")
        
        timeout = timeout or self.config['playwright']['timeout']
        await self.page.fill(selector, text, timeout=timeout)
    
    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None, state: str = "visible"):
        """等待元素出现
        
        Args:
            selector: 元素选择器
            timeout: 超时时间
            state: 等待状态 (attached, detached, visible, hidden)
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")
        
        timeout = timeout or self.config['playwright']['timeout']
        await self.page.wait_for_selector(selector, timeout=timeout, state=state)
    
    async def get_text(self, selector: str, timeout: Optional[int] = None) -> str:
        """获取元素文本
        
        Args:
            selector: 元素选择器
            timeout: 超时时间
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")
        
        timeout = timeout or self.config['playwright']['timeout']
        await self.wait_for_selector(selector, timeout)
        return await self.page.text_content(selector)
    
    async def screenshot(self, path: str = None):
        """截图
        
        Args:
            path: 保存路径，如果为None则返回字节流
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")
        
        if path:
            await self.page.screenshot(path=path)
        else:
            return await self.page.screenshot()
    
    async def execute_with_retry(
        self, 
        func: Callable, 
        max_retries: int = 3,
        retry_delay: float = 1.0,
        on_failure: Optional[Callable] = None
    ) -> Any:
        """执行函数并支持重试
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            on_failure: 失败时的回调函数
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                return await func() if asyncio.iscoroutinefunction(func) else func()
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    if on_failure:
                        await on_failure() if asyncio.iscoroutinefunction(on_failure) else on_failure()
                    await asyncio.sleep(retry_delay)
                else:
                    raise last_error
        return None
    
    async def skip_step(self, reason: str = "步骤跳过"):
        """跳过当前步骤
        
        Args:
            reason: 跳过原因
        """
        print(f"[跳过步骤] {reason}")
        # 可以在这里记录日志或发送通知
    
    async def reset_to_initial_state(self):
        """重置到初始状态（关闭弹窗、刷新等）"""
        if not self.page:
            return
        
        try:
            # 尝试关闭所有弹窗
            close_buttons = await self.page.query_selector_all('.close, .modal-close, [aria-label="关闭"]')
            for btn in close_buttons:
                try:
                    await btn.click(timeout=1000)
                except:
                    pass
            
            # 刷新页面
            await self.page.reload(wait_until="networkidle")
        except Exception as e:
            print(f"重置状态时出错: {e}")

