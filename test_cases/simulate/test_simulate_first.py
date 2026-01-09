"""
Simulate模块 - first测试用例
（由录制代码自动转换生成）

@File  : test_simulate_first.py
@Author: auto
"""
import pytest
from pages.desktop_page import DesktopPage
from playwright.async_api import expect


@pytest.mark.teaching
class TestSimulateFirst:
    """first测试类"""
    
    @pytest.mark.asyncio
    async def test_first(self, desktop: DesktopPage, driver):
        """测试first"""
        try:
            page = driver.page
            
            # ========== 自动转换的录制代码 ==========
            await page.get_by_text("仿真场景构建平台").click()
            await expect(page.get_by_role("menu").get_by_role("menuitem", name="拓扑管理")).to_be_visible()
            await page.get_by_text("靶标管理").click()
            await expect(page.get_by_role("menuitem", name="虚拟靶标")).to_be_visible()
            await page.get_by_role("menuitem", name="虚拟靶标").click()
            await expect(page.get_by_role("tab", name="个人模板")).to_be_visible()
            await page.get_by_role("menuitem", name="建模靶标").click()
            await expect(page.get_by_role("tab", name="个人模板")).to_be_visible()
            await page.get_by_text("系统设置").click()
            await expect(page.get_by_role("menuitem", name="镜像管理")).to_be_visible()
            await page.get_by_role("menuitem", name="镜像管理").click()
            await expect(page.get_by_role("tab", name="硬盘镜像文件")).to_be_visible()
            await page.get_by_role("menuitem", name="物理靶标").click()
            await expect(page.get_by_role("menuitem", name="设备管理")).to_be_visible()
            await page.get_by_role("menuitem", name="设备管理").click()
            await page.get_by_role("menuitem", name="策略配置").click()
            await page.get_by_role("menuitem", name="策略配置").click()
            await page.get_by_role("menuitem", name="标签管理").click()
            await page.get_by_text("内容市场-").click()
            await page.get_by_role("menuitem", name="资源更新-").click()



            
        except Exception as e:
            await driver.skip_step(f"测试失败: {e}")
            raise
