"""
pytest共享夹具配置

@File  : conftest.py
@Author: shenyuan
"""
import pytest
import pytest_asyncio
import asyncio
import yaml
from pathlib import Path
from core.web_ui_driver import WebUIDriver
from pages.desktop_page import DesktopPage
from pages.login_page import LoginPage


@pytest_asyncio.fixture(scope="function")
async def driver():
    """创建WebUI驱动实例（每个测试函数一个实例，确保事件循环一致）"""
    driver = WebUIDriver()
    await driver.start()
    yield driver
    await driver.close()


@pytest_asyncio.fixture(scope="function")
async def login(driver):
    """登录夹具 - 自动执行登录（模块级别，每个模块只登录一次，提高执行速度）"""
    # 检查配置是否启用自动登录
    config_path = Path("config/settings.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if config.get('login', {}).get('auto_login', True):
            login_page = LoginPage(driver)
            # 检查是否已登录
            if not await login_page.is_logged_in():
                await login_page.login()
            yield login_page
        else:
            yield None
    else:
        yield None


@pytest_asyncio.fixture(scope="function")
async def desktop(driver, login):
    """桌面页面夹具 - 自动登录后打开桌面"""
    desktop_page = DesktopPage(driver)
    
    # 简单检查：如果不在桌面，等待一下（login fixture 已经处理了登录）
    import asyncio
    await asyncio.sleep(1)  # 等待桌面加载
    
    yield desktop_page
    
    # 测试结束后关闭所有应用
    try:
        await desktop_page.close_all_apps()
    except:
        pass


@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_state(driver):
    """每个测试用例前后重置状态"""
    # 测试前：确保初始状态
    yield
    # 测试后：重置到初始状态（轻量级重置，避免影响性能）
    try:
        await driver.reset_to_initial_state()
    except:
        # 如果重置失败，不影响测试继续
        pass


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """在测试失败时自动截图"""
    outcome = yield
    rep = outcome.get_result()
    
    # 只在测试失败时截图
    if rep.when == "call" and rep.failed:
        # 获取 driver fixture
        if 'driver' in item.fixturenames:
            try:
                driver = item.funcargs.get('driver')
                if driver and hasattr(driver, 'page') and driver.page and not driver.page.is_closed():
                    import asyncio
                    # 尝试在事件循环中执行截图
                    try:
                        loop = asyncio.get_running_loop()
                        # 如果已经在事件循环中，创建任务
                        asyncio.create_task(driver.take_error_screenshot(str(rep.longrepr)[:100]))
                    except RuntimeError:
                        # 如果不在事件循环中，创建新的事件循环
                        asyncio.run(driver.take_error_screenshot(str(rep.longrepr)[:100]))
            except Exception as e:
                print(f"[Conftest] 自动截图失败: {e}")

