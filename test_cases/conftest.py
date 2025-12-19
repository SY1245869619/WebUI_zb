"""
pytest共享夹具配置
"""
import pytest
import asyncio
from core.web_ui_driver import WebUIDriver
from pages.desktop_page import DesktopPage


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def driver():
    """创建WebUI驱动实例"""
    driver = WebUIDriver()
    await driver.start()
    yield driver
    await driver.close()


@pytest.fixture(scope="function")
async def desktop(driver):
    """桌面页面夹具"""
    desktop_page = DesktopPage(driver)
    await desktop_page.open_desktop()
    yield desktop_page
    # 测试结束后关闭所有应用
    await desktop_page.close_all_apps()


@pytest.fixture(scope="function", autouse=True)
async def reset_state(driver):
    """每个测试用例前后重置状态"""
    # 测试前：确保初始状态
    yield
    # 测试后：重置到初始状态
    await driver.reset_to_initial_state()

