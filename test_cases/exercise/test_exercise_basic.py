"""
攻防演练基础测试用例
"""
import pytest
from pages.desktop_page import DesktopPage
from pages.exercise_app import ExerciseApp


@pytest.mark.exercise
class TestExerciseBasic:
    """攻防演练基础测试类"""
    
    @pytest.mark.asyncio
    async def test_open_exercise_app(self, desktop: DesktopPage, driver):
        """测试打开攻防演练应用"""
        try:
            await desktop.click_app_icon("攻防演练")
            exercise_app = ExerciseApp(driver)
            await exercise_app.wait_for_load()
            
            assert await exercise_app.is_app_opened(), "攻防演练应用未成功打开"
            
        except Exception as e:
            await driver.skip_step(f"打开应用失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_start_exercise(self, desktop: DesktopPage, driver):
        """测试开始演练"""
        try:
            await desktop.click_app_icon("攻防演练")
            exercise_app = ExerciseApp(driver)
            await exercise_app.wait_for_load()
            
            await exercise_app.start_exercise()
            
        except Exception as e:
            await driver.skip_step(f"开始演练失败: {e}")
            raise

