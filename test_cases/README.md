# 测试用例编写指南（实习生版 - 超简单！）

## 🚀 最简单的方法（推荐）⭐

### 在WebUI中直接转换（2步搞定！）

1. **录制代码**
   - 在WebUI控制台点击"启动录制"按钮
   - 操作完成后，复制Playwright生成的代码

2. **一键转换**
   - 在WebUI控制台点击"代码转换"按钮
   - 选择模块（授课教学/攻防演练/考试测评）
   - 输入测试名称（例如：navigation）
   - 粘贴代码
   - 点击"转换并保存"
   - **完成！✅ 文件自动生成！**

**就这么简单！** 工具会自动：
- ✅ 添加 await
- ✅ 删除浏览器代码
- ✅ 生成测试文件
- ✅ 放到正确的位置
- ✅ 无需手动操作！

---

## 📝 命令行方式（备选）

如果WebUI方式不能用，可以使用命令行工具：

```bash
python tools/convert_recording.py
```

然后按提示操作即可。

---

## 📝 手动方法（如果工具不能用）

如果自动转换工具不能用，可以手动转换：

### 转换规则（只需要记住3条）

1. **所有 `page.` 前面加 `await`**
   ```python
   # 录制代码
   page.get_by_text("教学管理").click()
   
   # 修改后
   await page.get_by_text("教学管理").click()
   ```

2. **所有 `expect(...)` 前面加 `await`**
   ```python
   # 录制代码
   expect(page.get_by_role("menuitem", name="综合分析")).to_be_visible()
   
   # 修改后
   await expect(page.get_by_role("menuitem", name="综合分析")).to_be_visible()
   ```

3. **删除这些代码**（项目会自动处理）
   ```python
   # 删除这些
   browser = playwright.chromium.launch(...)
   context = browser.new_context(...)
   context.close()
   browser.close()
   with sync_playwright() as playwright: ...
   ```

### 使用模板

1. 复制模板文件：
   ```bash
   cp test_cases/teaching/test_template.py test_cases/teaching/test_我的测试.py
   ```

2. 修改模板中的：
   - 类名
   - 测试方法名
   - 粘贴并修改代码

---

## 🎯 完整示例

### 录制生成的代码：
```python
def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width":1920,"height":1080})
    page = context.new_page()
    
    page.get_by_text("教学管理").click()
    expect(page.get_by_role("menuitem", name="综合分析")).to_be_visible()
    page.get_by_role("menuitem", name="课程库管理").click()
    
    context.close()
    browser.close()
```

### 转换后的代码（使用工具自动生成）：
```python
@pytest.mark.teaching
class TestTeachingNavigation:
    @pytest.mark.asyncio
    async def test_navigation(self, desktop: DesktopPage, driver):
        try:
            page = driver.page
            
            await page.get_by_text("教学管理").click()
            await expect(page.get_by_role("menuitem", name="综合分析")).to_be_visible()
            await page.get_by_role("menuitem", name="课程库管理").click()
            
        except Exception as e:
            await driver.skip_step(f"测试失败: {e}")
            raise
```

---

## ❓ 常见问题

### Q: 工具在哪里？
**A:** `tools/convert_recording.py`，直接运行即可

### Q: 如果工具报错怎么办？
**A:** 
1. 检查Python版本（需要3.7+）
2. 检查是否在项目根目录运行
3. 如果还是不行，使用手动方法

### Q: 如何运行测试？
**A:** 
```bash
# 运行单个测试
pytest test_cases/teaching/test_teaching_navigation.py -v

# 或在WebUI中选择模块执行
```

### Q: 测试失败了怎么办？
**A:** 代码中已经有异常处理，会自动跳过失败的步骤。如果需要调试，可以：
- 查看执行日志
- 检查元素定位是否正确
- 添加等待时间：`await page.wait_for_timeout(2000)`

---

## 📚 参考

- **模板文件**：`test_cases/teaching/test_template.py`
- **示例文件**：`test_cases/teaching/test_teaching_basic.py`
- **转换工具**：`tools/convert_recording.py`

---

## ✅ 检查清单

提交代码前确认：
- [ ] 使用了自动转换工具（推荐）或手动转换
- [ ] 文件放在正确的模块文件夹下
- [ ] 测试方法有清晰的描述
- [ ] 代码可以正常运行

**就这么简单！有问题随时问导师！** 🎉
