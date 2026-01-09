"""
Simulate模块 - create_topo测试用例
（由录制代码自动转换生成）

@File  : test_simulate_create_topo.py
@Author: auto
"""
import pytest
from pages.desktop_page import DesktopPage
from playwright.async_api import expect


@pytest.mark.teaching
class TestSimulateCreatetopo:
    """create_topo测试类"""
    
    @pytest.mark.asyncio
    async def test_create_topo(self, desktop: DesktopPage, driver):
        """测试create_topo"""
        try:
            page = driver.page
            
            # ========== 自动转换的录制代码 ==========
            await page.goto("http://10.70.70.96/Shenyuan_9#/index")
            await page.get_by_text("仿真场景构建平台").dblclick()
            await page.get_by_role("button", name=" 新建").click()
            await page.get_by_text("创建空白拓扑").click()
            await page.get_by_role("textbox", name="* 拓扑名称").click()
            await page.get_by_role("textbox", name="* 拓扑名称").fill("WebUI自动化拓扑")
            await page.get_by_role("textbox", name="* 容量").click()
            await page.get_by_role("listitem").filter(has_text="不限").click()
            await page.locator(".el-form-item__content > .el-select > .select-trigger > .el-select__tags > .el-select__input").click()
            await page.locator("#el-id-1857-269").get_by_text("常见结构").click()
            await page.get_by_role("button", name="确定").click()



            
        except Exception as e:
            await driver.skip_step(f"测试失败: {e}")
            raise
