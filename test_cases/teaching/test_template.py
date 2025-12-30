"""
测试用例模板 - 复制此文件并修改

使用方法：
1. 复制此文件，重命名为 test_xxx.py
2. 修改类名、方法名和描述
3. 粘贴录制的代码到 test_xxx 方法中
4. 按照转换规则修改代码（加await、删除浏览器代码等）

注意：此文件是模板，不会被pytest执行（已添加skip标记）

@File  : test_template.py
@Author: shenyuan
"""
import pytest
from pages.desktop_page import DesktopPage
from playwright.async_api import expect


@pytest.mark.skip(reason="这是模板文件，不会被执行")  # 跳过此文件，避免被pytest执行
@pytest.mark.teaching  # 注意：授课教学用teaching，攻防演练用exercise，考试测评用exam
class TestTeachingTemplate:  # 修改类名，例如：TestTeachingCourseManagement
    """[测试类描述，例如：授课教学-课程管理功能测试]"""
    
    @pytest.mark.asyncio
    async def test_template(self, desktop: DesktopPage, driver):
        """[测试方法描述，例如：测试课程管理导航]"""
        try:
            # 获取页面对象
            page = driver.page
            
            # ========== 在这里粘贴你录制的代码 ==========
            # 
            # 转换规则：
            # 1. 在每行前面加上 await
            #    例如：page.click() → await page.click()
            # 
            # 2. expect 也要加 await
            #    例如：expect(...).to_be_visible() → await expect(...).to_be_visible()
            # 
            # 3. 删除这些代码（项目会自动处理）：
            #    - browser = playwright.chromium.launch(...)
            #    - context = browser.new_context(...)
            #    - context.close()
            #    - browser.close()
            #    - with sync_playwright() as playwright: ...
            #
            # 示例：
            # 录制代码：page.get_by_text("教学管理").click()
            # 修改为：await page.get_by_text("教学管理").click()
            #
            # 录制代码：expect(page.get_by_role("menuitem", name="综合分析")).to_be_visible()
            # 修改为：await expect(page.get_by_role("menuitem", name="综合分析")).to_be_visible()
            
            # 在这里粘贴你的代码并修改
            
        except Exception as e:
            # 异常处理：如果测试失败，会跳过当前步骤
            await driver.skip_step(f"测试失败: {e}")
            raise

