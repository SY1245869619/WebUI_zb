"""
Exam模块 - first测试用例
（由录制代码自动转换生成）

@File  : test_exam_first.py
@Author: auto
"""
import pytest
from pages.desktop_page import DesktopPage
from playwright.async_api import expect


@pytest.mark.exam
class TestExamFirst:
    """考试测评--导航功能测试类"""
    
    @pytest.mark.asyncio
    async def test_first(self, desktop: DesktopPage, driver):
        """测试考试测评模块的完整导航流程
        
        测试步骤：
        1. 验证桌面应用图标存在
        2. 双击启动考试测评应用
        3. 验证应用启动成功（检查菜单可见）
        4. 测试测评管理模块下的各个子功能导航
        5. 测试考试管理模块下的各个子功能导航
        6. 测试练习管理模块下的各个子功能导航
        7. 测试系统管理模块下的各个子功能导航
        8. 测试内容市场模块导航
        """
        try:
            page = driver.page
            
            # ========== 自动转换的录制代码 ==========
            await page.get_by_text("考试测评").dblclick()
            await expect(page.get_by_role("menuitem", name="统计分析")).to_be_visible()
            await page.get_by_text("测评管理").click()
            await expect(page.get_by_role("menuitem", name="试卷管理")).to_be_visible()
            await page.get_by_role("menuitem", name="试卷管理").click()
            await expect(page.get_by_role("tab", name="个人试卷")).to_be_visible()
            await page.get_by_role("menuitem", name="考试管理").click()
            await expect(page.get_by_role("button", name=" 创建考试")).to_be_visible()
            await page.get_by_role("menuitem", name="练习管理").click()
            await expect(page.get_by_role("button", name=" 创建练习")).to_be_visible()
            await page.get_by_text("系统管理").click()
            await expect(page.get_by_role("menuitem", name="靶标管理")).to_be_visible()
            await page.get_by_text("内容市场").click()
            await expect(page.get_by_role("menuitem", name="资源安装")).to_be_visible()
            await page.get_by_role("menuitem", name="资源安装").click()
            await expect(page.get_by_text("名称")).to_be_visible()
            await page.locator("span").nth(4).click()
            
        except Exception as e:
            await driver.skip_step(f"测试失败: {e}")
            raise
