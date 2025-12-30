"""
Teaching模块 - 导航功能测试用例
测试授课教学应用的各个功能模块导航是否正常

@File  : test_teaching_first.py
@Author: auto
"""
import pytest
import asyncio
from pages.desktop_page import DesktopPage
from playwright.async_api import expect


@pytest.mark.teaching
class TestTeachingNavigation:
    """授课教学-导航功能测试类
    
    测试目标：验证授课教学应用的各个功能模块导航是否正常工作
    测试范围：
    - 应用启动和入口验证
    - 教学管理模块导航
    - 系统管理模块导航
    - 内容市场模块导航
    """
    
    @pytest.mark.asyncio
    async def test_teaching_module_navigation(self, desktop: DesktopPage, driver):
        """测试授课教学模块的完整导航流程
        
        测试步骤：
        1. 验证桌面应用图标存在
        2. 双击启动授课教学应用
        3. 验证应用启动成功（检查菜单可见）
        4. 测试教学管理模块下的各个子功能导航
        5. 测试系统管理模块下的各个子功能导航
        6. 测试内容市场模块导航
        """
        try:
            page = driver.page
            
            # ========== 步骤1: 启动应用 ==========
            # 验证桌面上的应用图标存在
            await expect(page.locator("#app-container")).to_contain_text("实验实践教学平台")
            
            # 双击启动应用
            await page.get_by_text("实验实践教学平台").dblclick()
            await asyncio.sleep(1)  # 等待应用加载
            
            # 验证应用启动成功：检查主菜单是否可见
            await expect(page.get_by_role("menuitem", name="统计分析")).to_be_visible()
            
            # ========== 步骤2: 测试教学管理模块 ==========
            # 展开教学管理菜单
            await page.get_by_text("教学管理").click()
            await expect(page.get_by_role("menuitem", name="课程库管理")).to_be_visible()
            
            # 测试课程库管理
            await page.get_by_role("menuitem", name="课程库管理").click()
            await expect(page.get_by_role("tab", name="个人课程")).to_be_visible()
            
            # 测试排课管理
            await page.get_by_role("menuitem", name="排课管理").click()
            # 注意：按钮名称包含图标字符，使用原始录制时的名称
            await expect(page.get_by_role("button", name="新建排课")).to_be_visible()
            
            # 测试自由学习管理
            await page.get_by_role("menuitem", name="自由学习管理").click()
            # 注意：按钮名称包含图标字符
            await expect(page.get_by_role("button", name="添加课程")).to_be_visible()
            
            # 测试学习地图管理
            await page.get_by_role("menuitem", name="学习地图管理").click()
            # 注意：按钮名称包含图标字符
            await expect(page.get_by_role("button", name="创建学习地图")).to_be_visible()
            
            # ========== 步骤3: 测试系统管理模块 ==========
            # 展开系统管理菜单
            await page.get_by_text("系统管理").click()
            await expect(page.get_by_role("menuitem", name="课程分类管理")).to_be_visible()
            
            # 测试课程分类管理
            await page.get_by_role("menuitem", name="课程分类管理").click()
            # 注意：按钮名称包含图标字符
            await expect(page.get_by_role("button", name="创建分类")).to_be_visible()
            
            # 测试课程关键字管理
            await page.get_by_role("menuitem", name="课程关键字管理").click()
            # 注意：按钮名称包含图标字符
            await expect(page.get_by_role("button", name="新建")).to_be_visible()
            
            # ========== 步骤4: 测试内容市场模块 ==========
            await page.get_by_text("内容市场").click()
            await page.get_by_role("menuitem", name="资源安装--").click()
            # 验证资源列表页面加载成功
            await expect(page.get_by_text("名称")).to_be_visible()
            
            # 关闭应用（点击关闭按钮）
            await page.locator("span").nth(4).click()
            
        except Exception as e:
            await driver.skip_step(f"测试失败: {e}")
            raise
