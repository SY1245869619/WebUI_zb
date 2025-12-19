"""
考试测评基础测试用例
"""
import pytest
from pages.desktop_page import DesktopPage
from pages.exam_app import ExamApp


@pytest.mark.exam
class TestExamBasic:
    """考试测评基础测试类"""
    
    @pytest.mark.asyncio
    async def test_open_exam_app(self, desktop: DesktopPage, driver):
        """测试打开考试测评应用"""
        try:
            await desktop.click_app_icon("考试测评")
            exam_app = ExamApp(driver)
            await exam_app.wait_for_load()
            
            assert await exam_app.is_app_opened(), "考试测评应用未成功打开"
            
        except Exception as e:
            await driver.skip_step(f"打开应用失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_create_exam(self, desktop: DesktopPage, driver):
        """测试创建考试"""
        try:
            await desktop.click_app_icon("考试测评")
            exam_app = ExamApp(driver)
            await exam_app.wait_for_load()
            
            await exam_app.create_exam("自动化测试考试")
            
        except Exception as e:
            await driver.skip_step(f"创建考试失败: {e}")
            raise

