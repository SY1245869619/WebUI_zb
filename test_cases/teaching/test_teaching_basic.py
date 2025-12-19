"""
授课教学基础测试用例
"""
import pytest
from pages.desktop_page import DesktopPage
from pages.teaching_app import TeachingApp


@pytest.mark.teaching
class TestTeachingBasic:
    """授课教学基础测试类"""
    
    @pytest.mark.asyncio
    async def test_open_teaching_app(self, desktop: DesktopPage, driver):
        """测试打开授课教学应用"""
        try:
            # 点击授课教学图标
            await desktop.click_app_icon("授课教学")
            
            # 创建应用页面对象
            teaching_app = TeachingApp(driver)
            await teaching_app.wait_for_load()
            
            # 验证应用已打开
            assert await teaching_app.is_app_opened(), "授课教学应用未成功打开"
            
        except Exception as e:
            # 如果卡住，可以跳过或重置
            await driver.skip_step(f"打开应用失败: {e}")
            await driver.reset_to_initial_state()
            raise
    
    @pytest.mark.asyncio
    async def test_start_teaching(self, desktop: DesktopPage, driver):
        """测试开始授课"""
        try:
            # 打开应用
            await desktop.click_app_icon("授课教学")
            teaching_app = TeachingApp(driver)
            await teaching_app.wait_for_load()
            
            # 开始授课
            await teaching_app.start_teaching()
            
            # 验证授课已开始（根据实际业务逻辑）
            await driver.page.wait_for_timeout(2000)
            
        except Exception as e:
            await driver.skip_step(f"开始授课失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_select_course(self, desktop: DesktopPage, driver):
        """测试选择课程"""
        try:
            await desktop.click_app_icon("授课教学")
            teaching_app = TeachingApp(driver)
            await teaching_app.wait_for_load()
            
            # 选择课程
            await teaching_app.select_course("测试课程")
            
        except Exception as e:
            await driver.skip_step(f"选择课程失败: {e}")
            raise

