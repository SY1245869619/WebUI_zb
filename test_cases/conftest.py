"""
pytest共享夹具配置

@File  : conftest.py
@Author: shenyuan
"""
import pytest
import pytest_asyncio
import asyncio
import yaml
import logging
import sys
import os
import re
from pathlib import Path
from threading import Lock
from core.web_ui_driver import WebUIDriver
from pages.desktop_page import DesktopPage
from pages.login_page import LoginPage

# 全局列表：存储测试用例信息（按执行顺序），用于在pytest_html_results_table_row中获取测试名称
# 每个元素是item.nodeid
_test_item_list = []
_test_item_lock = Lock()
_test_item_index = 0  # 当前处理的测试项索引

# 确保环境变量设置UTF-8编码（在导入其他模块之前）
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 导入pytest-html编码补丁，修复Windows系统下的中文乱码问题
# 注意：此补丁会尝试修改pytest-html的html_report.py文件中的charset设置
# 如果自动修补失败，请手动修改：
# C:\Python310\lib\site-packages\pytest_html\html_report.py
# 将 charset="utf-8" 改为 charset="GB2312"
try:
    import utils.pytest_html_patch
except Exception as e:
    print(f"[conftest] 警告: 无法导入pytest-html编码补丁: {e}")
    print(f"[conftest] 如果pytest HTML报告出现乱码，请手动修改pytest_html/html_report.py")

# 配置根logger使用UTF-8编码（在pytest启动前配置）
# 这确保所有日志输出都使用UTF-8，包括pytest-html捕获的日志
# 注意：不要清除pytest的handlers，只添加我们自己的handler
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
# 只添加UTF-8编码的handler，不删除pytest的handler（pytest需要自己的handler）
import io
# 检查是否已经有UTF-8 handler
has_utf8_handler = False
for handler in root_logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        # 检查stream的编码
        if hasattr(handler.stream, 'encoding') and handler.stream.encoding == 'utf-8':
            has_utf8_handler = True
            break
        # 如果是TextIOWrapper，检查其编码
        elif hasattr(handler.stream, 'buffer') and hasattr(handler.stream, 'encoding'):
            if handler.stream.encoding == 'utf-8':
                has_utf8_handler = True
                break
if not has_utf8_handler:
    utf8_handler = logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace'))
    utf8_handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(utf8_handler)

# 导入pytest-html用于添加测试用例详情到报告
try:
    import pytest_html
except ImportError:
    pytest_html = None

# 包装Playwright的expect以记录断言日志
# 使用logging模块，让pytest-html能捕获日志
from playwright.async_api import expect as original_expect

# 创建logger用于记录断言日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# 允许传播到根logger，这样pytest-html也能捕获到日志
logger.propagate = True

def logged_expect(locator):
    """包装expect以记录断言日志"""
    class LoggedExpect:
        def __init__(self, locator):
            self.locator = locator
            self._expect = original_expect(locator)
        
        async def to_be_visible(self, **kwargs):
            try:
                # 尝试获取元素的描述
                locator_str = str(locator)
                # 使用logging记录，pytest-html可以捕获
                if hasattr(locator, 'get_text'):
                    try:
                        text = await locator.get_text()
                        logger.info(f"[ASSERT] 断言元素可见: {text}")
                    except:
                        logger.info(f"[ASSERT] 断言元素可见: {locator_str}")
                else:
                    # 清理locator字符串，移除不必要的selector细节，使日志更简洁
                    # 移除 Playwright selector 中的 `i` 标记（大小写不敏感标记）
                    # 注意：需要处理多种格式：`"i]`, `"i'`, `'i]`, `'i'`, `"i>`, `'i>`
                    clean_locator = locator_str.replace('"i]', '"]').replace("'i]", "']").replace('"i>', '">').replace("'i>", "'>")
                    # 处理Unicode转义序列（如 \u540d\u79f0 应该显示为 名称）
                    # 注意：需要处理所有包含 \u 转义序列的情况
                    if '\\u' in clean_locator:
                        try:
                            import re
                            # 优先匹配 internal:text="\u540d\u79f0"i 或 internal:text="\u540d\u79f0"> 模式
                            # 注意：需要匹配可能没有 'i' 标记的情况，如 internal:text="\u540d\u79f0">
                            pattern = r'(internal:text=")([^"]*)([^>]*>)'
                            def replace_unicode(match):
                                try:
                                    prefix = match.group(1)
                                    unicode_part = match.group(2)
                                    suffix = match.group(3)
                                    # 解码Unicode转义序列
                                    # 注意：如果unicode_part包含 \u 转义序列，需要先编码为latin-1再解码
                                    if '\\u' in unicode_part:
                                        decoded = unicode_part.encode('latin-1', errors='ignore').decode('unicode_escape')
                                    else:
                                        decoded = unicode_part
                                    # 移除后缀中的 'i' 标记
                                    suffix = suffix.replace("'i", "'").replace('"i', '"').replace("'i>", "'>").replace('"i>', '">')
                                    return prefix + decoded + suffix
                                except Exception as e:
                                    # 如果解码失败，返回原始匹配
                                    return match.group(0)
                            clean_locator = re.sub(pattern, replace_unicode, clean_locator)
                            # 如果还有未转码的 \u 转义序列，尝试全局替换
                            if '\\u' in clean_locator:
                                # 尝试匹配所有剩余的 \u 转义序列
                                unicode_pattern = r'\\u([0-9a-fA-F]{4})'
                                def decode_unicode_hex(match):
                                    try:
                                        code_point = int(match.group(1), 16)
                                        return chr(code_point)
                                    except:
                                        return match.group(0)
                                clean_locator = re.sub(unicode_pattern, decode_unicode_hex, clean_locator)
                        except Exception as e:
                            # 如果处理失败，保持原样
                            pass
                    logger.info(f"[ASSERT] 断言元素可见: {clean_locator}")
                return await self._expect.to_be_visible(**kwargs)
            except Exception as e:
                locator_str = str(locator)
                logger.error(f"[ASSERT ERROR] 断言失败 - 元素不可见: {locator_str}, 错误: {e}")
                # 在断言失败时立即截图（如果可能）
                try:
                    # 尝试从locator获取page对象
                    if hasattr(locator, '_frame') and hasattr(locator._frame, '_page'):
                        page = locator._frame._page
                        if page and not page.is_closed():
                            # 在后台任务中截图，不阻塞异常抛出
                            import asyncio
                            try:
                                loop = asyncio.get_running_loop()
                                async def take_error_screenshot():
                                    try:
                                        from utils.screenshot_utils import take_screenshot
                                        # 从locator中提取元素名称作为截图文件名
                                        error_name = f"断言失败"
                                        if hasattr(locator, '_selector'):
                                            selector = str(locator._selector)
                                            if 'name="' in selector:
                                                import re
                                                name_match = re.search(r'name="([^"]+)"', selector)
                                                if name_match:
                                                    error_name = f"断言失败_{name_match.group(1)}"
                                        await take_screenshot(page, error_name)
                                    except Exception as screenshot_error:
                                        logger.debug(f"[ASSERT ERROR] 截图失败: {screenshot_error}")
                                loop.create_task(take_error_screenshot())
                            except Exception as loop_error:
                                logger.debug(f"[ASSERT ERROR] 无法创建截图任务: {loop_error}")
                except Exception as screenshot_ex:
                    logger.debug(f"[ASSERT ERROR] 尝试截图时出错: {screenshot_ex}")
                raise
        
        async def to_contain_text(self, text, **kwargs):
            try:
                locator_str = str(locator)
                # 清理locator字符串，移除不必要的selector细节
                # 注意：需要处理多种格式：`"i]`, `"i'`, `'i]`, `'i'`, `"i>`, `'i>`
                clean_locator = locator_str.replace('"i]', '"]').replace("'i]", "']").replace('"i>', '">').replace("'i>", "'>")
                # 处理Unicode转义序列
                if '\\u' in clean_locator and 'internal:text=' in clean_locator:
                    try:
                        # 提取包含Unicode转义序列的部分
                        import re
                        # 匹配 internal:text="\u540d\u79f0"i 这样的模式
                        pattern = r'(internal:text=")([^"]*)([^>]*>)'
                        def replace_unicode(match):
                            prefix = match.group(1)
                            unicode_part = match.group(2)
                            suffix = match.group(3)
                            # 解码Unicode转义序列
                            try:
                                decoded = unicode_part.encode('latin-1', errors='ignore').decode('unicode_escape')
                                # 移除后缀中的 'i' 标记
                                suffix = suffix.replace("'i", "'").replace('"i', '"')
                                return prefix + decoded + suffix
                            except:
                                return match.group(0)
                        clean_locator = re.sub(pattern, replace_unicode, clean_locator)
                    except:
                        pass
                # 确保使用UTF-8编码输出
                logger.info(f"[ASSERT] 断言元素包含文本: {clean_locator} 包含 '{text}'")
                return await self._expect.to_contain_text(text, **kwargs)
            except Exception as e:
                locator_str = str(locator)
                logger.error(f"[ASSERT ERROR] 断言失败 - 元素不包含文本: {locator_str}, 错误: {e}")
                raise
        
        def __getattr__(self, name):
            # 代理其他方法到原始expect对象
            return getattr(self._expect, name)
    
    return LoggedExpect(locator)

# 替换playwright.async_api模块中的expect
import playwright.async_api
playwright.async_api.expect = logged_expect
# 也替换sys.modules中的，确保导入时使用包装版本
if 'playwright.async_api' in sys.modules:
    sys.modules['playwright.async_api'].expect = logged_expect


@pytest_asyncio.fixture(scope="function")
async def driver(request):
    """创建WebUI驱动实例（每个测试函数一个实例，确保事件循环一致）"""
    import os
    from core.video_recorder import VideoRecorder
    from core.performance_monitor import PerformanceMonitor
    
    # 初始化性能监控
    perf_monitor = PerformanceMonitor()
    
    # 检查是否启用视频录制（默认关闭）
    enable_video = os.environ.get('ENABLE_VIDEO_RECORDING', '0') == '1'
    
    video_options = None
    video_recorder = None
    
    if enable_video:
        # 只有在启用时才初始化视频录制
        video_recorder = VideoRecorder()
        # 获取测试用例名称（用于视频录制）
        test_name = request.node.name if hasattr(request, 'node') else f"test_{id(request)}"
        # 获取视频录制配置选项（必须在创建context之前）
        video_options = video_recorder.get_recording_options(test_name)
    
    # 创建driver并启动（如果启用视频录制，传入视频录制选项）
    driver = WebUIDriver()
    await driver.start(video_options=video_options)
    
    # 将request保存到driver中，以便截图时能够访问item
    driver._pytest_request = request
    
    # 将监控器附加到driver
    if video_recorder:
        driver.video_recorder = video_recorder
    driver.perf_monitor = perf_monitor
    
    # 获取测试用例名称（用于性能监控）
    test_name = request.node.name if hasattr(request, 'node') else f"test_{id(request)}"
    
    yield driver
    
    # 关闭前收集性能指标
    if hasattr(driver, 'page') and driver.page and not driver.page.is_closed():
        try:
            await perf_monitor.collect_metrics(driver.page, test_name)
        except:
            pass
    
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


# 在pytest session开始时清空列表
@pytest.hookimpl
def pytest_sessionstart(session):
    """pytest session开始时清空测试用例列表"""
    global _test_item_list, _test_item_index
    with _test_item_lock:
        _test_item_list.clear()
        _test_item_index = 0
        # 重置hook的初始化标记
        if hasattr(pytest_html_results_table_row, '_initialized'):
            delattr(pytest_html_results_table_row, '_initialized')
        logger.debug(f"[Conftest] pytest session开始，清空测试用例列表")

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """在测试失败时自动截图和保存视频，并添加错误信息到pytest-html报告
    同时处理手动截图（成功和失败时都添加）
    
    注意：pytest-html 3.2.0 会自动生成测试用例详情，我们只需要在失败时添加错误信息
    """
    outcome = yield
    rep = outcome.get_result()
    
    # 存储测试用例信息到全局列表，供pytest_html_results_table_row使用
    # 按执行顺序存储item.nodeid
    if rep.when == "call":
        with _test_item_lock:
            if item.nodeid not in _test_item_list:
                _test_item_list.append(item.nodeid)
                logger.debug(f"[Conftest] 添加测试用例到全局列表: {item.nodeid}, 当前列表长度: {len(_test_item_list)}")
    
    # 初始化extra列表
    if not hasattr(rep, 'extra'):
        rep.extra = []
    
    # 处理手动截图（无论成功还是失败，都要添加到报告中）
    # 区分截图类型：手动截图、错误截图、成功截图
    if rep.when == "call" and pytest_html:
        # 检查是否有手动截图（保存在item中）
        if hasattr(item, 'manual_screenshots') and item.manual_screenshots:
            # 用于跟踪已添加的截图类型标签，每种类型只添加一次
            added_types = set()
            
            for screenshot_path in item.manual_screenshots:
                try:
                    # 使用pathlib.Path（已在文件顶部导入）
                    # 处理路径：可能是相对路径或绝对路径
                    screenshot_file = Path(screenshot_path)
                    if not screenshot_file.is_absolute():
                        # 如果是相对路径，转换为绝对路径
                        screenshot_file = Path.cwd() / screenshot_file
                    
                    if screenshot_file.exists():
                        # 判断截图类型（根据文件名前缀）
                        screenshot_type = "手动截图"
                        filename = screenshot_file.name.lower()
                        if filename.startswith('error_') or filename.startswith('断言失败_') or filename.startswith('等待元素_'):
                            screenshot_type = "错误截图"
                        elif filename.startswith('success_') or filename.startswith('成功_'):
                            screenshot_type = "成功截图"
                        elif '关键步骤' in filename or '操作完成' in filename:
                            screenshot_type = "关键步骤截图"
                        
                        # 使用绝对路径（Windows格式，转换为正斜杠）
                        # 格式：C:/Users/SHENYUAN/Desktop/WebUI_zb/screenshots/filename.png
                        absolute_path_str = str(screenshot_file.resolve()).replace('\\', '/')
                        
                        # 每种截图类型只添加一次标签
                        if screenshot_type not in added_types:
                            color_map = {
                                "错误截图": "#d32f2f",  # 红色
                                "成功截图": "#2e7d32",  # 绿色
                                "关键步骤截图": "#1976d2",  # 蓝色
                                "手动截图": "#1976d2"  # 蓝色
                            }
                            color = color_map.get(screenshot_type, "#1976d2")
                            rep.extra.append(pytest_html.extras.html(
                                f'<div style="margin: 5px 0; text-align: right;"><strong style="color: {color};">{screenshot_type}:</strong></div>'
                            ))
                            added_types.add(screenshot_type)
                        
                        rep.extra.append(pytest_html.extras.png(absolute_path_str))
                        logger.info(f"[Conftest] {screenshot_type}已添加到报告: {screenshot_path}, 绝对路径: {absolute_path_str}")
                except Exception as e:
                    logger.warning(f"[Conftest] 添加手动截图到报告失败: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
    
    # pytest-html 会自动收集测试结果并生成详情，不需要手动处理
    # 只在失败时添加错误信息到extra
    if rep.when == "call" and pytest_html and rep.outcome == "failed":
        # 添加错误信息（如果有）
        if hasattr(rep, 'longrepr') and rep.longrepr:
            error_msg = str(rep.longrepr)[:1000]  # 限制长度
            # HTML转义
            error_msg = error_msg.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            rep.extra.append(pytest_html.extras.html(
                f'<div class="log" style="background-color: #ffebee; padding: 10px; border-left: 4px solid #d32f2f;">'
                f'<strong style="color: #d32f2f;">错误信息:</strong><br/>'
                f'<pre style="white-space: pre-wrap; word-wrap: break-word;">{error_msg}</pre>'
                f'</div>'
            ))
    
    # 只在测试失败时自动截图和保存视频
    if rep.when == "call" and rep.failed:
        # 获取 driver fixture
        if 'driver' in item.fixturenames:
            try:
                driver = item.funcargs.get('driver')
                if driver and hasattr(driver, 'page') and driver.page and not driver.page.is_closed():
                    import asyncio
                    # Path已在文件顶部导入，不需要重复导入
                    
                    # 尝试在事件循环中执行截图
                    async def take_screenshot():
                        try:
                            # 生成截图文件名（使用测试用例名称）
                            test_name = item.nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")
                            # 从错误信息中提取关键信息（如等待的元素名称）
                            error_msg = ""
                            if rep.longrepr:
                                error_str = str(rep.longrepr)
                                # 提取等待的元素信息，例如：waiting for get_by_role("menuitem", name="资源安装--")
                                import re
                                wait_match = re.search(r'waiting for get_by_role\([^)]+name="([^"]+)"', error_str)
                                if wait_match:
                                    error_msg = f"等待元素_{wait_match.group(1)}"
                                else:
                                    error_msg = error_str[:50]
                            screenshot_path = await driver.take_error_screenshot(error_msg)
                            
                            # 如果截图成功，添加到pytest-html报告中
                            if screenshot_path and pytest_html and Path(screenshot_path).exists():
                                # 将截图路径转换为相对路径（相对于报告文件）
                                # pytest-html报告在reports目录，截图在screenshots目录（项目根目录）
                                screenshot_file = Path(screenshot_path)
                                if not screenshot_file.is_absolute():
                                    screenshot_file = Path.cwd() / screenshot_file
                                
                                # 从reports目录到screenshots目录的相对路径
                                # 报告在 reports/ 目录，截图在 screenshots/ 目录
                                # 所以相对路径应该是 ../screenshots/filename.png
                                relative_path = Path('..') / 'screenshots' / screenshot_file.name
                                
                                # 使用pytest-html的extras添加截图
                                if not hasattr(rep, 'extra'):
                                    rep.extra = []
                                # 使用绝对路径（Windows格式，转换为正斜杠）
                                # 格式：C:/Users/SHENYUAN/Desktop/WebUI_zb/screenshots/filename.png
                                absolute_path_str = str(screenshot_file.resolve()).replace('\\', '/')
                                
                                # 添加错误截图类型标签（右对齐显示，且只添加一次）
                                # 检查是否已经添加过错误截图标签
                                if not hasattr(rep, '_error_screenshot_label_added'):
                                    rep.extra.append(pytest_html.extras.html(
                                        f'<div style="margin: 5px 0; text-align: right;"><strong style="color: #d32f2f;">错误截图:</strong></div>'
                                    ))
                                    rep._error_screenshot_label_added = True
                                rep.extra.append(pytest_html.extras.png(absolute_path_str))
                                logger.info(f"[Conftest] 失败截图已添加到报告: {screenshot_path}, 绝对路径: {absolute_path_str}")
                        except Exception as e:
                            logger.error(f"[Conftest] 截图失败: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                    
                    # 修复事件循环问题：确保在正确的事件循环中执行截图
                    # 注意：在pytest hook中，测试已经结束，可能不在事件循环中
                    # 我们需要使用driver的事件循环来执行截图
                    try:
                        # 尝试获取driver的事件循环（如果driver保存了事件循环引用）
                        driver_loop = None
                        if hasattr(driver, '_loop'):
                            driver_loop = driver._loop
                        elif hasattr(driver, 'context') and hasattr(driver.context, '_connection') and hasattr(driver.context._connection, '_loop'):
                            driver_loop = driver.context._connection._loop
                        
                        if driver_loop and not driver_loop.is_closed() and driver.page and not driver.page.is_closed():
                            # 使用driver的事件循环执行截图
                            import concurrent.futures
                            future = asyncio.run_coroutine_threadsafe(take_screenshot(), driver_loop)
                            try:
                                # 等待截图完成（最多5秒）
                                future.result(timeout=5.0)
                            except concurrent.futures.TimeoutError:
                                logger.warning(f"[Conftest] 截图任务超时")
                            except Exception as e:
                                logger.warning(f"[Conftest] 截图任务失败: {e}")
                        else:
                            # 尝试获取当前运行的事件循环
                            try:
                                loop = asyncio.get_running_loop()
                                if driver.page and not driver.page.is_closed():
                                    task = loop.create_task(take_screenshot())
                                    # 不等待任务完成，避免阻塞
                            except RuntimeError:
                                # 如果不在事件循环中，尝试使用新的事件循环
                                try:
                                    if driver.page and not driver.page.is_closed():
                                        # 使用同步方式调用异步函数（不推荐，但作为最后手段）
                                        new_loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(new_loop)
                                        try:
                                            new_loop.run_until_complete(asyncio.wait_for(take_screenshot(), timeout=5.0))
                                        finally:
                                            new_loop.close()
                                except Exception as e:
                                    logger.warning(f"[Conftest] 不在事件循环中，尝试创建新事件循环失败: {e}")
                    except Exception as e:
                        logger.warning(f"[Conftest] 截图失败: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                    
                    # 保存失败用例的视频（仅在启用视频录制时）
                    if hasattr(driver, 'video_recorder') and driver.video_recorder and hasattr(driver, 'context'):
                        try:
                            test_name = item.name
                            video_path = driver.video_recorder.save_video(driver.context, test_name, failed=True)
                            if video_path:
                                logger.info(f"[Conftest] 失败用例视频已保存: {video_path}")
                        except Exception as e:
                            logger.error(f"[Conftest] 保存视频失败: {e}")
            except Exception as e:
                logger.error(f"[Conftest] 自动截图失败: {e}")
                import traceback
                logger.error(traceback.format_exc())


# pytest-html hook：修改Test列显示，添加中文模块标识
# 注意：pytest-html 3.2.0 版本的 hook 只接受 cells 参数
# pytest-html hook：修改Test列显示，添加中文模块标识
# 注意：pytest-html 3.2.0 版本的 hook 只接受 cells 参数
# 使用tryfirst=True确保我们的hook先执行，不使用hookwrapper
@pytest.hookimpl(trylast=True)
def pytest_html_results_table_row(cells):
    """修改pytest-html报告中的Test列，添加中文模块标识和详细信息
    
    注意：pytest-html使用BeautifulSoup处理HTML，HTML报告的charset是GB2312
    我们需要确保中文字符在写入时使用正确的编码
    
    使用trylast=True确保我们的hook最后执行，这样我们的修改不会被其他hook覆盖
    不使用hookwrapper，直接修改cells
    """
    # 重置索引（每次生成报告时重置，使用函数属性来标记）
    global _test_item_index
    init_key = '_initialized'
    # 使用时间戳作为key，确保每次报告生成时都重置
    import time
    current_time = int(time.time())
    time_key = f'_initialized_{current_time}'
    if not hasattr(pytest_html_results_table_row, time_key):
        _test_item_index = 0
        setattr(pytest_html_results_table_row, time_key, True)
        # 清除旧的初始化标记
        for attr in dir(pytest_html_results_table_row):
            if attr.startswith('_initialized_') and attr != time_key:
                delattr(pytest_html_results_table_row, attr)
        logger.info(f"[Conftest] 重置测试项索引，全局列表长度: {len(_test_item_list)}, 列表内容: {_test_item_list}")
    
    # 检查是否是真正的测试行（不是extra详情行）
    # extra行的cells数量可能不同，或者第一个cell是extra类
    if len(cells) < 2:
        return  # 跳过非标准行
    
    # 检查第一个cell是否是Result列（应该有col-result类）
    first_cell = cells[0] if len(cells) > 0 else None
    if first_cell:
        first_cell_str = str(first_cell)
        # 如果第一个cell是extra类，跳过这一行
        if 'class="extra"' in first_cell_str or 'colspan' in first_cell_str:
            return
        # 检查是否是真正的测试行（Result列应该有col-result类）
        if hasattr(first_cell, 'get'):
            first_cell_class = first_cell.get('class', [])
            if isinstance(first_cell_class, list) and 'col-result' not in first_cell_class:
                # 如果不是col-result类，可能是extra详情行，跳过
                return
        elif not ('col-result' in first_cell_str or 'Passed' in first_cell_str or 'Failed' in first_cell_str or 'Rerun' in first_cell_str):
            # 如果无法获取class属性，检查字符串中是否包含Result列的特征
            return
    
    # Test列通常是第二个单元格（索引为1）
    if len(cells) > 1:
        try:
            # 获取测试名称（Test列）
            test_cell = cells[1]  # Test列是第二个单元格
            
            # 方法1：尝试从全局列表中按顺序获取测试信息
            # pytest-html在生成报告时，通常按照测试执行的顺序调用hook
            test_nodeid = None
            with _test_item_lock:
                logger.info(f"[Conftest] hook被调用，当前索引: {_test_item_index}, 列表长度: {len(_test_item_list)}")
                if _test_item_index < len(_test_item_list):
                    test_nodeid = _test_item_list[_test_item_index]
                    _test_item_index += 1
                    logger.info(f"[Conftest] 从全局列表获取测试名称: {test_nodeid}, 索引: {_test_item_index-1}")
                else:
                    logger.warning(f"[Conftest] 全局列表索引超出范围: {_test_item_index} >= {len(_test_item_list)}, 列表内容: {_test_item_list}")
            
            # 方法2：如果方法1失败，尝试从test_cell中获取
            test_name = ''
            if not test_nodeid:
                try:
                    # 使用get_text()获取文本
                    if hasattr(test_cell, 'get_text'):
                        test_name = test_cell.get_text(strip=True)
                    # 如果get_text失败，尝试从HTML中提取
                    if not test_name:
                        test_cell_html = str(test_cell)
                        name_match = re.search(r'<td[^>]*class="col-[^"]*"[^>]*>(.*?)</td>', test_cell_html, re.DOTALL)
                        if name_match:
                            raw_name = name_match.group(1)
                            raw_name = re.sub(r'<[^>]+>', '', raw_name)
                            import html
                            test_name = html.unescape(raw_name).strip()
                    # 如果还是失败，使用str()
                    if not test_name:
                        test_name = str(test_cell).strip()
                except Exception as e:
                    logger.debug(f"[Conftest] 获取测试名称失败: {e}")
                    test_name = str(test_cell) if test_cell else ''
            
            # 如果test_nodeid存在，使用它；否则使用test_name
            if test_nodeid:
                test_name = test_nodeid
            
            if not test_name:
                # 如果仍然无法获取，尝试从Result列或其他地方获取信息
                # 或者直接跳过
                logger.debug("[Conftest] 无法获取测试名称，跳过Test列更新")
                return
            
            # 从测试路径中动态提取模块信息（不硬编码）
            from utils.module_helper import ModuleHelper
            from pathlib import Path
            import re
            
            # 从测试名称中提取详细信息（test_name格式可能是：test_cases/teaching/test_teaching_first.py::TestClass::test_method）
            test_file = test_name.split('::')[0] if '::' in test_name else test_name
            test_class = ''
            test_method = ''
            if '::' in test_name:
                parts = test_name.split('::')
                if len(parts) >= 2:
                    test_class = parts[1] if len(parts) > 2 else ''
                    test_method = parts[-1]
            
            # 从测试路径中提取模块中文名称（动态识别，不硬编码）
            module_name = ModuleHelper.extract_module_cn_name_from_path(test_name) or ''
            
            # 尝试从测试文件中提取类的中文名称
            class_cn_name = ''
            if test_class:
                try:
                    # 获取测试文件的完整路径
                    test_file_path = Path(test_file)
                    if not test_file_path.is_absolute():
                        # 如果是相对路径，尝试从test_cases目录查找
                        if 'test_cases/' in test_file:
                            test_file_path = Path(test_file)
                        else:
                            # 尝试从当前目录查找
                            test_file_path = Path('test_cases') / test_file_path
                    
                    if test_file_path.exists():
                        with open(test_file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # 从类的文档字符串中提取中文名称
                            # 例如：class TestTeachingNavigation: """授课教学-导航功能测试类"""
                            # 使用非贪婪匹配，避免匹配到文档字符串的结束标记
                            class_pattern = rf'class\s+{re.escape(test_class)}\s*:\s*"""(.*?)"""'
                            class_match = re.search(class_pattern, content, re.DOTALL)
                            if class_match:
                                class_doc = class_match.group(1).strip()
                                # 提取第一行的中文部分（通常是类的中文名称）
                                first_line = class_doc.split('\n')[0].strip()
                                # 提取中文部分（匹配中文字符和常见分隔符，但不包括引号）
                                chinese_match = re.search(r'([\u4e00-\u9fff][^\n"]*)', first_line)
                                if chinese_match:
                                    class_cn_name = chinese_match.group(1).strip()
                                    # 清理常见的后缀
                                    class_cn_name = class_cn_name.replace('测试类', '').replace('测试', '').strip()
                                    # 确保没有多余的引号
                                    class_cn_name = class_cn_name.replace('"', '').replace("'", '').strip()
                                    # 如果包含"--"，处理为"-"
                                    if '--' in class_cn_name:
                                        class_cn_name = class_cn_name.replace('--', '-')
                except Exception as e:
                    logger.debug(f"[Conftest] 提取类中文名称失败: {e}")
            
            # 构建更详细的测试名称（优化显示，移除重复的test_name）
            # 提取文件名（不含路径）
            file_name = test_file.split('/')[-1].split('\\')[-1] if test_file else ''
            
            # 构建显示名称：完整路径 + 中文模块名 + 中文类名
            detailed_name = test_name  # 保留完整路径
            
            # 在末尾添加中文信息
            cn_info_parts = []
            if module_name:
                cn_info_parts.append(f"[模块: {module_name}]")
            if class_cn_name:
                cn_info_parts.append(f"[类: {class_cn_name}]")
            
            if cn_info_parts:
                detailed_name += " " + " ".join(cn_info_parts)
            
            # 更新Test列内容
            # 注意：pytest-html使用BeautifulSoup，需要正确设置文本内容
            # 使用最可靠的方法：直接设置string属性（BeautifulSoup会自动处理）
            try:
                if detailed_name:
                    # 直接设置string属性（这是BeautifulSoup推荐的方式，会自动替换所有内容）
                    test_cell.string = detailed_name
                    logger.info(f"[Conftest] Test列已更新: {detailed_name}")
                    
                    # 验证是否设置成功
                    if hasattr(test_cell, 'string'):
                        actual_value = str(test_cell.string) if test_cell.string else ''
                        if actual_value != detailed_name:
                            logger.warning(f"[Conftest] Test列设置后验证失败: 期望 '{detailed_name}', 实际 '{actual_value}'")
                            # 如果验证失败，尝试备用方法：使用NavigableString
                            try:
                                from bs4 import NavigableString
                                test_cell.clear()
                                test_cell.append(NavigableString(detailed_name))
                                logger.info(f"[Conftest] Test列已更新（使用NavigableString备用方法）: {detailed_name}")
                            except Exception as e2:
                                logger.error(f"[Conftest] 备用方法也失败: {e2}")
                else:
                    logger.warning(f"[Conftest] detailed_name为空，无法更新Test列，test_nodeid: {test_nodeid}, test_name: {test_name}")
            except Exception as e:
                logger.error(f"[Conftest] 更新Test列失败: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # 尝试备用方法：使用NavigableString
                try:
                    from bs4 import NavigableString
                    test_cell.clear()
                    test_cell.append(NavigableString(detailed_name if detailed_name else test_name))
                    logger.info(f"[Conftest] Test列已更新（使用NavigableString）: {detailed_name if detailed_name else test_name}")
                except Exception as e2:
                    logger.error(f"[Conftest] 备用方法也失败: {e2}")
                    pass
            
            # 修改Duration列，添加单位（通常是第三个或第四个单元格）
            if len(cells) >= 3:
                duration_cell = cells[2]  # Duration列通常是第三个单元格
                try:
                    # 获取原始文本（不包含HTML标签）
                    duration_text = duration_cell.get_text(strip=True) if hasattr(duration_cell, 'get_text') else str(duration_cell).strip()
                    # 清理文本，移除HTML标签和空白字符
                    if duration_text:
                        # 移除HTML标签
                        duration_text = re.sub(r'<[^>]+>', '', duration_text).strip()
                    
                    # 如果已经有数字但没有单位，添加单位
                    if duration_text and not duration_text.endswith(('s', '秒', 'ms', 'S')):
                        try:
                            # 尝试解析为数字（移除可能的单位字符）
                            clean_text = re.sub(r'[^\d.]', '', duration_text)
                            if clean_text:
                                float(clean_text)  # 验证是数字
                                # 清空单元格并设置新内容
                                if hasattr(duration_cell, 'clear'):
                                    duration_cell.clear()
                                # 使用NavigableString设置纯文本
                                from bs4 import NavigableString
                                duration_cell.append(NavigableString(f"{clean_text}s"))
                        except (ValueError, AttributeError):
                            pass  # 如果不是数字，保持原样
                except Exception as e:
                    logger.debug(f"[Conftest] 修改Duration列失败: {e}")
                    pass
            
            # Links列：不处理，保持为空（用户要求）
        except Exception as e:
            logger.error(f"[Conftest] 修改pytest-html报告列失败: {e}")


@pytest.hookimpl
def pytest_sessionfinish(session, exitstatus):
    """在pytest会话结束后，直接修改HTML报告文件，确保中文信息被正确保存"""
    try:
        # 获取pytest-html报告路径
        html_report_path = None
        
        # 方法1：从session.config.option.htmlpath获取（pytest-html存储报告路径的地方）
        if hasattr(session.config.option, 'htmlpath') and session.config.option.htmlpath:
            html_report_path_str = session.config.option.htmlpath
            # htmlpath可能是字符串或列表
            if isinstance(html_report_path_str, list):
                html_report_path_str = html_report_path_str[0] if html_report_path_str else None
            if html_report_path_str:
                html_report_path = Path(html_report_path_str)
        
        # 如果还是找不到，尝试从环境变量或默认路径获取
        if not html_report_path or not html_report_path.exists():
            # 尝试查找最新的HTML报告文件
            reports_dir = Path('reports')
            if reports_dir.exists():
                html_files = list(reports_dir.glob('pytest自动化测试报告_*.html'))
                if html_files:
                    html_report_path = max(html_files, key=lambda p: p.stat().st_mtime)
        
        if html_report_path and html_report_path.exists():
            logger.info(f"[Conftest] 开始修改HTML报告文件: {html_report_path}")
            
            # 读取HTML文件
            from bs4 import BeautifulSoup
            with open(html_report_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # 查找所有Test列的单元格
            # pytest-html的Test列通常在第二个td（索引1），且可能包含col-name或col-test类
            # 我们需要找到所有测试行的Test列单元格
            test_cells_map = {}  # 存储 {test_nodeid: test_cell} 的映射
            
            # 查找所有测试行（tbody中的tr）
            tbody_list = soup.find_all('tbody')
            logger.info(f"[Conftest] 找到 {len(tbody_list)} 个tbody")
            
            for tbody in tbody_list:
                rows = tbody.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        # 检查第一个cell是否是Result列（col-result类）
                        first_cell = cells[0]
                        first_cell_class = first_cell.get('class', [])
                        if isinstance(first_cell_class, list) and 'col-result' not in first_cell_class:
                            # 跳过非测试行（如extra详情行）
                            continue
                        
                        # Test列通常是第二个单元格（索引1）
                        test_cell = cells[1]
                        test_text = test_cell.get_text(strip=True)
                        
                        # 清理test_text，去除可能的HTML标签和特殊字符，以及中文信息
                        clean_test_text = re.sub(r'<[^>]+>', '', test_text).strip()
                        # 去除中文信息部分（[模块:xxx] [类:xxx]），只保留原始路径用于匹配
                        clean_test_text_for_match = re.sub(r'\s*\[模块:[^\]]+\]\s*', '', clean_test_text)
                        clean_test_text_for_match = re.sub(r'\s*\[类:[^\]]+\]\s*', '', clean_test_text_for_match)
                        clean_test_text_for_match = re.sub(r"[,']+$", '', clean_test_text_for_match).strip()
                        
                        # 如果已经包含中文信息，检查是否需要更新（可能部分行有中文，部分没有）
                        has_chinese = '[模块:' in test_text or '[类:' in test_text
                        
                        # 在全局列表中查找匹配的测试用例
                        matched_nodeid = None
                        for test_nodeid in _test_item_list:
                            # 检查test_nodeid是否与test_text匹配（使用清理后的文本）
                            if test_nodeid in clean_test_text_for_match or clean_test_text_for_match in test_nodeid:
                                matched_nodeid = test_nodeid
                                break
                        
                        # 如果匹配到测试用例，添加到映射中（无论是否已有中文信息，都要处理以确保一致性）
                        if matched_nodeid:
                            # 为每个匹配的单元格都添加到映射中（可能有多个：rerun和passed）
                            # 使用test_nodeid + 行索引作为key，确保每个单元格都被处理
                            row_index = len([k for k in test_cells_map.keys() if isinstance(k, str) and k.startswith(matched_nodeid)])
                            cell_key = f"{matched_nodeid}_{row_index}"
                            if cell_key not in test_cells_map:
                                test_cells_map[cell_key] = {
                                    'cell': test_cell,
                                    'nodeid': matched_nodeid,
                                    'has_chinese': has_chinese
                                }
                                logger.info(f"[Conftest] 匹配到测试用例: {matched_nodeid} -> {clean_test_text_for_match} (第{row_index+1}个, 已有中文: {has_chinese})")
            
            logger.info(f"[Conftest] 找到 {len(test_cells_map)} 个需要更新的Test列单元格")
            
            # 遍历所有匹配的单元格，为每个测试添加中文信息
            from utils.module_helper import ModuleHelper
            # re模块已在文件顶部导入，这里不需要重复导入
            
            for cell_key, cell_info in test_cells_map.items():
                test_nodeid = cell_info['nodeid']
                test_cell = cell_info['cell']
                has_chinese = cell_info.get('has_chinese', False)
                current_text = test_cell.get_text(strip=True)
                
                # 如果已经包含完整的中文信息，跳过（但确保所有行都有中文）
                if has_chinese and '[模块:' in current_text and '[类:' in current_text:
                    logger.debug(f"[Conftest] 测试 {test_nodeid} 已包含完整中文信息，跳过")
                    continue
                
                # 即使部分行有中文，也要确保所有行都有完整的中文信息
                
                # 提取模块和类的中文名称
                test_file = test_nodeid.split('::')[0] if '::' in test_nodeid else test_nodeid
                test_class = ''
                if '::' in test_nodeid:
                    parts = test_nodeid.split('::')
                    if len(parts) >= 2:
                        test_class = parts[1] if len(parts) > 2 else ''
                
                module_name = ModuleHelper.extract_module_cn_name_from_path(test_nodeid) or ''
                class_cn_name = ''
                
                if test_class:
                    try:
                        test_file_path = Path(test_file)
                        if not test_file_path.is_absolute():
                            if 'test_cases/' in test_file:
                                test_file_path = Path(test_file)
                            else:
                                test_file_path = Path('test_cases') / test_file_path
                        
                        if test_file_path.exists():
                            with open(test_file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            class_pattern = rf'class\s+{re.escape(test_class)}\s*:\s*"""(.*?)"""'
                            class_match = re.search(class_pattern, content, re.DOTALL)
                            if class_match:
                                class_doc = class_match.group(1).strip()
                                first_line = class_doc.split('\n')[0].strip()
                                chinese_match = re.search(r'([\u4e00-\u9fff][^\n"]*)', first_line)
                                if chinese_match:
                                    class_cn_name = chinese_match.group(1).strip()
                                    class_cn_name = class_cn_name.replace('测试类', '').replace('测试', '').strip()
                                    class_cn_name = class_cn_name.replace('"', '').replace("'", '').strip()
                                    if '--' in class_cn_name:
                                        class_cn_name = class_cn_name.replace('--', '-')
                    except Exception as e:
                        logger.debug(f"[Conftest] 提取类中文名称失败: {e}")
                
                # 构建新的显示名称
                detailed_name = test_nodeid
                cn_info_parts = []
                if module_name:
                    cn_info_parts.append(f"[模块: {module_name}]")
                if class_cn_name:
                    cn_info_parts.append(f"[类: {class_cn_name}]")
                
                if cn_info_parts:
                    detailed_name += " " + " ".join(cn_info_parts)
                    # 更新单元格内容
                    test_cell.string = detailed_name
                    logger.info(f"[Conftest] 在sessionfinish中更新Test列: {detailed_name}")
            
            # 保存修改后的HTML文件
            # 注意：pytest-html使用GB2312编码，但BeautifulSoup默认使用UTF-8
            # 我们需要确保保存时使用正确的编码
            with open(html_report_path, 'w', encoding='utf-8') as f:
                # 确保HTML的charset声明是UTF-8
                if soup.html and soup.html.head:
                    meta_charset = soup.html.head.find('meta', charset=True)
                    if meta_charset:
                        meta_charset['charset'] = 'utf-8'
                    else:
                        # 查找content-type meta标签
                        meta_content = soup.html.head.find('meta', attrs={'http-equiv': 'Content-Type'})
                        if meta_content:
                            meta_content['content'] = 'text/html; charset=utf-8'
                        else:
                            # 添加charset meta标签
                            new_meta = soup.new_tag('meta', charset='utf-8')
                            soup.html.head.insert(0, new_meta)
                
                f.write(str(soup))
            
            logger.info(f"[Conftest] HTML报告文件已更新: {html_report_path}")
        else:
            logger.warning(f"[Conftest] 未找到HTML报告文件，无法更新Test列")
    except Exception as e:
        logger.error(f"[Conftest] 在sessionfinish中修改HTML报告失败: {e}")
        import traceback
        logger.error(traceback.format_exc())

