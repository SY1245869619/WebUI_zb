"""
截图工具
提供统一的截图方法，支持错误截图和成功截图

@File  : screenshot_utils.py
@Author: shenyuan
"""
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
from playwright.async_api import Page


class ScreenshotHelper:
    """截图辅助类"""
    
    def __init__(self, screenshot_dir: str = "screenshots"):
        """初始化截图辅助类
        
        Args:
            screenshot_dir: 截图保存目录
        """
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    async def take_error_screenshot(self, page: Page, error_message: str = "", prefix: str = "error") -> str:
        """在发生错误时截图
        
        Args:
            page: Playwright Page 对象
            error_message: 错误信息（用于生成文件名）
            prefix: 文件名前缀，默认为 "error"
            
        Returns:
            截图文件路径
        """
        try:
            # 生成文件名：error_YYYYMMDD_HHMMSS_错误信息前10个字符.png
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 清理错误信息，只保留安全字符
            safe_error = "".join(c for c in error_message[:20] if c.isalnum() or c in ('_', '-')).strip()
            if safe_error:
                filename = f"{prefix}_{timestamp}_{safe_error}.png"
            else:
                filename = f"{prefix}_{timestamp}.png"
            
            filepath = self.screenshot_dir / filename
            
            # 截图
            await page.screenshot(path=str(filepath), full_page=True)
            print(f"[ScreenshotHelper] 错误截图已保存: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"[ScreenshotHelper] 保存错误截图失败: {e}")
            return ""
    
    async def take_success_screenshot(self, page: Page, step_name: str = "", prefix: str = "success") -> str:
        """在特定步骤成功时截图
        
        Args:
            page: Playwright Page 对象
            step_name: 步骤名称（用于生成文件名）
            prefix: 文件名前缀，默认为 "success"
            
        Returns:
            截图文件路径
        """
        try:
            # 生成文件名：success_YYYYMMDD_HHMMSS_步骤名称.png
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 清理步骤名称，只保留安全字符
            safe_name = "".join(c for c in step_name[:30] if c.isalnum() or c in ('_', '-')).strip()
            if safe_name:
                filename = f"{prefix}_{timestamp}_{safe_name}.png"
            else:
                filename = f"{prefix}_{timestamp}.png"
            
            filepath = self.screenshot_dir / filename
            
            # 截图
            await page.screenshot(path=str(filepath), full_page=True)
            print(f"[ScreenshotHelper] 成功截图已保存: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"[ScreenshotHelper] 保存成功截图失败: {e}")
            return ""
    
    async def take_screenshot(self, page: Page, filename: str = None) -> str:
        """通用截图方法
        
        Args:
            page: Playwright Page 对象
            filename: 文件名（可选，如果不提供则自动生成）
            
        Returns:
            截图文件路径
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            # 确保文件名以 .png 结尾
            if not filename.endswith('.png'):
                filename += '.png'
            
            filepath = self.screenshot_dir / filename
            
            # 截图
            await page.screenshot(path=str(filepath), full_page=True)
            print(f"[ScreenshotHelper] 截图已保存: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"[ScreenshotHelper] 保存截图失败: {e}")
            return ""


# 全局实例
_screenshot_helper = ScreenshotHelper()


async def take_error_screenshot(page: Page, error_message: str = "") -> str:
    """便捷函数：在发生错误时截图
    
    Args:
        page: Playwright Page 对象
        error_message: 错误信息
        
    Returns:
        截图文件路径
    """
    return await _screenshot_helper.take_error_screenshot(page, error_message)


async def take_success_screenshot(page: Page, step_name: str = "") -> str:
    """便捷函数：在特定步骤成功时截图
    
    Args:
        page: Playwright Page 对象
        step_name: 步骤名称
        
    Returns:
        截图文件路径
    """
    return await _screenshot_helper.take_success_screenshot(page, step_name)


async def take_screenshot(page: Page, filename: str = None) -> str:
    """便捷函数：通用截图
    
    Args:
        page: Playwright Page 对象
        filename: 文件名（可选）
        
    Returns:
        截图文件路径
    """
    return await _screenshot_helper.take_screenshot(page, filename)

