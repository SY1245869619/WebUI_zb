"""
Exercise模块 - case测试用例
（由录制代码自动转换生成）

@File  : test_exercise_first.py
@Author: auto
"""
import pytest
from pages.desktop_page import DesktopPage
from playwright.async_api import expect


@pytest.mark.exercise
class TestExerciseCase:
    """攻防演练-导航功能测试类"""
    
    @pytest.mark.asyncio
    async def test_case(self, desktop: DesktopPage, driver):
        """测试攻防演练模块导航流程"""
        try:
            page = driver.page
            
            # ========== 自动转换的录制代码 ==========
            await page.get_by_text("攻防演练").dblclick()
            await expect(page.get_by_role("menuitem", name="统计分析")).to_be_visible()
            await page.get_by_text("演练管理").click()
            await expect(page.get_by_role("menuitem", name="剧本管理")).to_be_visible()
            await page.get_by_role("menuitem", name="剧本管理").click()
            await expect(page.get_by_role("tab", name="个人剧本")).to_be_visible()
            await page.get_by_role("menuitem", name="活动管理").click()
            await expect(page.get_by_role("button", name=" 新建演练活动")).to_be_visible()
            await page.get_by_text("内容市场").click()
            await page.get_by_role("menuitem", name="资源安装--").click()
            await expect(page.get_by_text("名称")).to_be_visible()
            await page.locator("span").nth(4).click()
            
        except Exception as e:
            await driver.skip_step(f"测试失败: {e}")
            raise
