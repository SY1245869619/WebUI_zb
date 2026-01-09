"""
Playwright浏览器驱动封装
提供统一的浏览器操作接口，支持重试机制和错误处理

@File  : web_ui_driver.py
@Author: shenyuan
"""
import asyncio
import logging
import sys
import io
from typing import Optional, Callable, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
import yaml
import os
from pathlib import Path

# 创建logger用于记录驱动日志
logger = logging.getLogger(__name__)
# 确保logger使用UTF-8编码
logger.setLevel(logging.INFO)
# 不添加自己的handler，只使用根logger的handler，避免重复输出
# 设置propagate=True让日志传播到根logger，由根logger统一处理
logger.propagate = True


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
    
    async def start(self, video_options: Optional[dict] = None):
        """启动浏览器
        
        Args:
            video_options: 可选的视频录制配置（dict，包含record_video_dir等）
        """
        # 确保在正确的事件循环中启动Playwright
        # 获取当前运行的事件循环（必须在 async 函数中调用）
        try:
            current_loop = asyncio.get_running_loop()
            logger.info(f"[DRIVER] 启动 Playwright，当前事件循环: {current_loop}")
        except RuntimeError:
            # 如果没有运行的事件循环，获取默认的事件循环
            current_loop = asyncio.get_event_loop()
            logger.info(f"[DRIVER] 启动 Playwright，使用默认事件循环: {current_loop}")
        
        # 保存事件循环引用，以便在测试失败时使用
        self._loop = current_loop
        
        # 确保事件循环是活动的
        if current_loop.is_closed():
            raise RuntimeError("事件循环已关闭，无法启动 Playwright")
        
        # 启动 Playwright（必须在当前事件循环中调用）
        self.playwright = await async_playwright().start()
        logger.info("[DRIVER] Playwright 已启动")
        
        browser_type = getattr(self.playwright, self.config['playwright']['browser'])
        
        self.browser = await browser_type.launch(
            headless=self.config['playwright']['headless'],
            slow_mo=self.config['playwright']['slow_mo']
        )
        logger.info("[DRIVER] 浏览器已启动")
        
        # 准备context配置
        context_options = {}
        
        # 添加视频录制选项（如果提供）
        if video_options:
            context_options.update(video_options)
        
        # 检查是否启用移动端模式
        device_config = self.config.get('playwright', {}).get('device', {})
        if device_config.get('enabled', False):
            # 使用移动设备模拟
            device_name = device_config.get('name', 'iPhone 12')
            from playwright.async_api import devices
            device = devices.get(device_name)
            if device:
                # 合并设备配置和视频选项
                context_options.update(device)
                self.context = await self.browser.new_context(**context_options)
            else:
                # 如果设备不存在，使用自定义移动端配置
                context_options.update({
                    'viewport': {
                        'width': device_config.get('width', 375),
                        'height': device_config.get('height', 667)
                    },
                    'user_agent': device_config.get('user_agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)')
                })
                self.context = await self.browser.new_context(**context_options)
        else:
            # 桌面端模式
            context_options.update({
                'viewport': {
                    'width': self.config['playwright']['viewport']['width'],
                    'height': self.config['playwright']['viewport']['height']
                }
            })
            self.context = await self.browser.new_context(**context_options)
        logger.info("[DRIVER] 浏览器上下文已创建")
        
        # 启用Playwright日志记录（自动记录所有操作和断言）
        # 这会自动记录所有页面操作、网络请求、断言等
        playwright_logger = logging.getLogger("playwright")
        playwright_logger.setLevel(logging.INFO)
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.config['playwright']['timeout'])
        
        # 监听页面事件，只记录重要的日志（过滤掉页面JavaScript错误和警告）
        def handle_console(msg):
            # 只记录log类型，过滤掉error和warning（这些是页面JavaScript错误，不是测试错误）
            if msg.type == 'log':
                # 过滤掉无意义的日志（如"Gt", "false"等）
                text = msg.text.strip()
                if text and len(text) > 2 and not text.lower() in ['gt', 'false', 'true']:
                    logger.info(f"[PAGE] {msg.type}: {msg.text}")
        
        def handle_pageerror(error):
            # 只记录真正的页面错误，过滤掉SVG路径错误等无关错误
            error_str = str(error)
            if 'path' not in error_str.lower() and 'attribute d' not in error_str.lower():
                logger.error(f"[PAGE ERROR] {error}")
        
        self.page.on("console", handle_console)
        self.page.on("pageerror", handle_pageerror)
        
        logger.info(f"[DRIVER] 页面已创建，事件循环: {asyncio.get_running_loop()}")
    
    def _wrap_page_methods(self):
        """包装Playwright页面方法以自动记录操作日志"""
        # 保存原始方法
        original_click = self.page.click
        original_dblclick = self.page.dblclick
        original_fill = self.page.fill
        original_get_by_text = self.page.get_by_text
        original_get_by_role = self.page.get_by_role
        original_locator = self.page.locator
        
        async def logged_click(selector, **kwargs):
            # 尝试获取元素的描述性信息
            try:
                if hasattr(selector, 'get_text'):
                    text = await selector.get_text()
                    print(f"[ACTION] 点击元素: {text}")
                else:
                    print(f"[ACTION] 点击元素: {selector}")
            except:
                print(f"[ACTION] 点击元素: {selector}")
            try:
                result = await original_click(selector, **kwargs)
                return result
            except Exception as e:
                print(f"[ACTION ERROR] 点击失败: {selector}, 错误: {e}")
                raise
        
        async def logged_dblclick(selector, **kwargs):
            try:
                if hasattr(selector, 'get_text'):
                    text = await selector.get_text()
                    print(f"[ACTION] 双击元素: {text}")
                else:
                    print(f"[ACTION] 双击元素: {selector}")
            except:
                print(f"[ACTION] 双击元素: {selector}")
            try:
                result = await original_dblclick(selector, **kwargs)
                return result
            except Exception as e:
                print(f"[ACTION ERROR] 双击失败: {selector}, 错误: {e}")
                raise
        
        async def logged_fill(selector, value, **kwargs):
            print(f"[ACTION] 填写输入框: {selector} = {value}")
            try:
                result = await original_fill(selector, value, **kwargs)
                return result
            except Exception as e:
                print(f"[ACTION ERROR] 填写失败: {selector}, 错误: {e}")
                raise
        
        # 包装get_by_text和get_by_role（这些返回locator，需要特殊处理）
        def logged_get_by_text(text, **kwargs):
            print(f"[ACTION] 查找文本元素: {text}")
            locator = original_get_by_text(text, **kwargs)
            # 包装返回的locator的click方法
            original_locator_click = locator.click
            async def logged_locator_click(**click_kwargs):
                print(f"[ACTION] 点击文本元素: {text}")
                return await original_locator_click(**click_kwargs)
            locator.click = logged_locator_click
            return locator
        
        def logged_get_by_role(role, **kwargs):
            name = kwargs.get('name', '')
            role_desc = f"{role}" + (f" (name={name})" if name else "")
            print(f"[ACTION] 查找角色元素: {role_desc}")
            locator = original_get_by_role(role, **kwargs)
            # 包装返回的locator的click方法
            original_locator_click = locator.click
            async def logged_locator_click(**click_kwargs):
                print(f"[ACTION] 点击角色元素: {role_desc}")
                return await original_locator_click(**click_kwargs)
            locator.click = logged_locator_click
            return locator
        
        def logged_locator(selector, **kwargs):
            print(f"[ACTION] 定位元素: {selector}")
            locator = original_locator(selector, **kwargs)
            # 包装返回的locator的click方法
            original_locator_click = locator.click
            async def logged_locator_click(**click_kwargs):
                print(f"[ACTION] 点击定位元素: {selector}")
                return await original_locator_click(**click_kwargs)
            locator.click = logged_locator_click
            return locator
        
        # 替换方法
        self.page.click = logged_click
        self.page.dblclick = logged_dblclick
        self.page.fill = logged_fill
        self.page.get_by_text = logged_get_by_text
        self.page.get_by_role = logged_get_by_role
        self.page.locator = logged_locator
        
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
        
        # 检查页面是否有效
        if self.page.is_closed():
            raise RuntimeError("页面已关闭")
        
        timeout = timeout or self.config['playwright']['timeout']
        
        # 使用简单的轮询方式，避免事件循环问题
        max_attempts = timeout // 500  # 每500ms检查一次
        
        for attempt in range(max_attempts):
            try:
                locator = self.page.locator(selector).first
                if state == "visible":
                    # 使用count和bounding_box来检查元素是否可见，避免is_visible的事件循环问题
                    count = await locator.count()
                    if count > 0:
                        box = await locator.bounding_box()
                        if box and box.get('width', 0) > 0 and box.get('height', 0) > 0:
                            return
                elif state == "hidden":
                    # 检查元素是否隐藏（不存在或不可见）
                    count = await locator.count()
                    if count == 0:
                        return
                    box = await locator.bounding_box()
                    if not box or box.get('width', 0) == 0 or box.get('height', 0) == 0:
                        return
                elif state == "attached":
                    if await locator.count() > 0:
                        return
                elif state == "detached":
                    if await locator.count() == 0:
                        return
                else:
                    # 默认检查可见性
                    count = await locator.count()
                    if count > 0:
                        box = await locator.bounding_box()
                        if box and box.get('width', 0) > 0 and box.get('height', 0) > 0:
                            return
            except:
                pass
            
            # 等待一小段时间再重试
            await asyncio.sleep(0.5)
        
        # 如果所有尝试都失败，抛出异常
        raise RuntimeError(f"等待元素超时: {selector}, 状态: {state}")
    
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
    
    async def take_error_screenshot(self, error_message: str = "") -> str:
        """在发生错误时截图
        
        Args:
            error_message: 错误信息
            
        Returns:
            截图文件路径
        """
        from utils.screenshot_utils import take_error_screenshot
        return await take_error_screenshot(self.page, error_message)
    
    async def take_success_screenshot(self, step_name: str = "") -> str:
        """在特定步骤成功时截图
        
        Args:
            step_name: 步骤名称
            
        Returns:
            截图文件路径
        """
        from utils.screenshot_utils import take_success_screenshot
        return await take_success_screenshot(self.page, step_name)
    
    async def take_screenshot(self, filename: str = None) -> str:
        """通用截图方法

        Args:
            filename: 文件名（可选，如果不提供则自动生成）

        Returns:
            截图文件路径
        """
        from utils.screenshot_utils import take_screenshot
        screenshot_path = await take_screenshot(self.page, filename)
        
        # 将截图路径保存到pytest item中，以便在报告中显示
        try:
            # 通过driver的_pytest_request访问item
            if hasattr(self, '_pytest_request') and self._pytest_request:
                item = self._pytest_request.node
                if not hasattr(item, 'manual_screenshots'):
                    item.manual_screenshots = []
                if screenshot_path and screenshot_path not in item.manual_screenshots:
                    item.manual_screenshots.append(screenshot_path)
        except:
            # 如果无法访问pytest对象，忽略
            pass
        
        return screenshot_path
    
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
            # 确保在正确的事件循环中执行
            # 检查页面是否仍然有效
            if self.page.is_closed():
                return
            
            # 尝试关闭所有弹窗（使用locator而不是query_selector_all，避免事件循环问题）
            try:
                close_selectors = ['.close', '.modal-close', '[aria-label="关闭"]']
                for selector in close_selectors:
                    try:
                        close_btn = self.page.locator(selector).first
                        if await close_btn.is_visible(timeout=1000):
                            await close_btn.click(timeout=1000)
                    except:
                        pass
            except Exception as e:
                # 如果关闭弹窗失败，继续执行
                pass
            
            # 刷新页面（如果页面仍然有效）
            if not self.page.is_closed():
                try:
                    await self.page.reload(wait_until="networkidle", timeout=5000)
                except:
                    # 如果刷新失败，尝试简单的reload
                    try:
                        await self.page.reload(timeout=5000)
                    except:
                        pass
        except Exception as e:
            # 静默处理错误，避免影响测试
            print(f"重置状态时出错: {e}")

