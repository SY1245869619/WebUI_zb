"""
录制工具自动登录脚本
在启动 Playwright Codegen 前自动登录，保存登录状态，然后启动 Codegen

@File  : recording_auto_login.py
@Author: shenyuan
"""
import asyncio
import yaml
import json
import subprocess
import sys
from pathlib import Path
from playwright.async_api import async_playwright


async def login_in_browser(page, login_url: str, username: str, password: str, target_url: str):
    """在浏览器中执行登录
    
    Args:
        page: Playwright Page 对象
        login_url: 登录URL
        username: 用户名
        password: 密码
        target_url: 目标URL
    """
    # 导航到登录页面
    print(f"[自动登录] 导航到登录页面: {login_url}")
    await page.goto(login_url)
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(1)
    
    # 执行登录
    print("[自动登录] 正在输入用户名和密码...")
    try:
        await page.get_by_role("textbox", name="请输入账号").click()
        await page.get_by_role("textbox", name="请输入账号").fill(username)
        await page.get_by_role("textbox", name="请输入密码").click()
        await page.get_by_role("textbox", name="请输入密码").fill(password)
        await page.get_by_role("button", name="登录").click()
    except Exception as e:
        print(f"[自动登录] 登录操作失败，尝试备用方法: {e}")
        # 备用方法：使用更通用的选择器
        await page.fill('input[type="text"], input[name="username"], input[placeholder*="账号"]', username)
        await page.fill('input[type="password"], input[name="password"]', password)
        await page.click('button:has-text("登录"), button[type="submit"]')
    
    # 等待登录完成
    await asyncio.sleep(2)
    
    # 检查是否已登录（等待跳转到桌面）
    try:
        await page.wait_for_url("**/index", timeout=10000)
        print("[自动登录] 登录成功，已跳转到桌面")
    except:
        print("[自动登录] 警告: 可能未成功跳转到桌面，继续执行...")
    
    # 导航到目标URL（如果与当前URL不同）
    current_url = page.url
    if target_url not in current_url:
        print(f"[自动登录] 导航到目标URL: {target_url}")
        await page.goto(target_url)
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(1)
    
    print("[自动登录] ✅ 登录完成")


async def auto_login_and_start_codegen(target_url: str = None):
    """自动登录并启动录制工具
    
    流程：
    1. 先在一个浏览器中登录并保存状态
    2. 启动 Codegen，使用保存的状态
    """
    # 读取配置
    config_path = Path("config/settings.yaml")
    if not config_path.exists():
        print("错误: 配置文件不存在: config/settings.yaml")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    login_config = config.get('login', {})
    login_url = login_config.get('url', 'http://10.70.70.96/Shenyuan_9#/login')
    username = login_config.get('username', 'Shenyuan_9')
    password = login_config.get('password', 'Shenyuan_9')
    
    # 如果未提供目标URL，使用桌面地址
    if target_url is None:
        target_url = login_config.get('desktop_url', 'http://10.70.70.96/Shenyuan_9#/index')
    
    print(f"[自动登录] 启动录制工具")
    print(f"[自动登录] 登录URL: {login_url}")
    print(f"[自动登录] 目标URL: {target_url}")
    print(f"[自动登录] 用户名: {username}")
    
    # 创建临时目录保存 cookies
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    cookies_file = temp_dir / "recording_cookies.json"
    
    # 步骤1: 先在一个浏览器中登录并保存状态
    print("[自动登录] 步骤1: 先登录并保存状态...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        try:
            # 执行登录
            await login_in_browser(page, login_url, username, password, target_url)
            
            # 保存 cookies 和 storage state
            print("[自动登录] 保存登录状态...")
            storage_state = await context.storage_state()
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(storage_state, f, indent=2)
            
            print("[自动登录] ✅ 登录状态已保存")
        except Exception as e:
            print(f"[自动登录] 登录失败: {e}")
            await browser.close()
            if cookies_file.exists():
                cookies_file.unlink()
            raise
        finally:
            await browser.close()
    
    # 步骤2: 启动 Codegen，使用保存的状态
    print("[自动登录] 步骤2: 启动 Codegen 并加载登录状态...")
    codegen_cmd = [
        'playwright', 'codegen',
        '--viewport-size', '1920,1080',
        '--load-storage', str(cookies_file),
        target_url
    ]
    
    try:
        # 启动 Codegen（这会打开录制界面）
        print("[自动登录] Codegen 正在启动...")
        print("[自动登录] 💡 Codegen 浏览器应该已经自动登录")
        
        # 启动 Codegen 进程（阻塞等待）
        subprocess.run(codegen_cmd, check=True)
        print("[自动登录] 录制工具已关闭")
        
    except FileNotFoundError:
        print("错误: 未找到 playwright 命令，请先安装:")
        print("  pip install playwright")
        print("  playwright install")
    except KeyboardInterrupt:
        print("\n[自动登录] 用户中断录制")
    except Exception as e:
        print(f"[自动登录] 启动录制工具失败: {e}")
    finally:
        # 清理临时文件
        if cookies_file.exists():
            cookies_file.unlink()
            print("[自动登录] 已清理临时文件")


if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(auto_login_and_start_codegen(target_url))
