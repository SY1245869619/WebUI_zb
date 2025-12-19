# WebUI自动化测试项目

基于 Playwright + pytest + NiceGUI 的WebUI自动化测试框架，专为"Web桌面"式前端应用设计。

## 📋 项目特性

✅ **模块化应用管理** - 每个应用（授课教学、攻防演练、考试测评等）作为独立模块  
✅ **自定义运行** - 支持通过Web界面选择要执行的应用模块  
✅ **MySQL支持** - 集成PyMySQL，支持数据库操作和数据验证  
✅ **钉钉机器人通知** - 支持测试执行结果自动发送到钉钉群  
✅ **邮件通知** - 支持测试报告邮件发送  
✅ **失败处理机制** - 支持步骤跳过和状态重置  
✅ **Web控制界面** - 美观的NiceGUI界面，可视化配置和执行  
✅ **用例录制** - 集成Playwright Codegen，支持可视化录制用例  
✅ **Page Object模式** - 清晰的页面对象封装，易于维护  

## 🏗️ 项目结构

```
WebUI_zb/
├── config/                    # 配置文件目录
│   ├── settings.yaml         # 全局配置（数据库、通知、Playwright）
│   └── module_config.yaml    # 应用模块配置
├── core/                     # 核心模块
│   ├── web_ui_driver.py     # Playwright浏览器驱动封装
│   ├── notification.py      # 钉钉、邮件通知服务
│   └── db_client.py         # MySQL数据库客户端
├── pages/                    # Page Object 页面对象
│   ├── base_page.py         # 页面基类
│   ├── desktop_page.py      # 桌面页面（图标点击等）
│   ├── teaching_app.py      # 授课教学应用页面
│   ├── exam_app.py         # 考试测评应用页面
│   └── exercise_app.py     # 攻防演练应用页面
├── test_cases/              # 测试用例（按应用模块组织）
│   ├── teaching/           # 授课教学模块用例
│   ├── exercise/           # 攻防演练模块用例
│   ├── exam/               # 考试测评模块用例
│   └── conftest.py         # pytest共享夹具
├── web_ui/                  # Web控制界面
│   ├── main.py            # NiceGUI应用主入口
│   └── components/        # 界面组件
│       ├── module_selector.py      # 模块选择器
│       └── notification_config.py # 通知配置组件
├── utils/                   # 工具类
│   └── recording_helper.py # 录制辅助工具
├── logs/                    # 日志目录（自动创建）
├── requirements.txt         # Python依赖
├── pytest.ini              # pytest配置
└── run.py                  # 项目启动入口
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- MySQL 5.7+（可选，如果使用数据库功能）

### 2. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install
```

### 3. 配置项目

编辑 `config/settings.yaml` 配置文件：

```yaml
# 数据库配置（如果使用）
database:
  host: localhost
  port: 3306
  user: root
  password: your_password
  database: test_db
  charset: utf8mb4

# 通知配置
notification:
  dingtalk:
    enabled: false  # 设置为true启用钉钉通知
    webhook: https://oapi.dingtalk.com/robot/send?access_token=your_token
    secret: your_secret  # 可选
  
  email:
    enabled: false  # 设置为true启用邮件通知
    smtp_server: smtp.qq.com
    smtp_port: 587
    sender_email: your_email@qq.com
    sender_password: your_password
    receiver_emails:
      - receiver@example.com

# Playwright配置
playwright:
  headless: false
  slow_mo: 100
  timeout: 30000
  browser: chromium
  viewport:
    width: 1920
    height: 1080
```

编辑 `config/module_config.yaml` 配置目标Web应用：

```yaml
desktop:
  base_url: http://localhost:3000  # 修改为你的Web应用地址
  icon_selector: .desktop-icon
  wait_timeout: 5000
```

### 4. 启动Web控制界面

```bash
python run.py
```

然后在浏览器中打开 `http://localhost:8080` 访问控制界面。

### 5. 使用Web界面

1. **选择应用模块** - 在左侧勾选要执行的应用模块
2. **配置通知** - 配置钉钉机器人和邮箱（可选）
3. **开始执行** - 点击"开始执行"按钮运行测试
4. **查看日志** - 实时查看执行日志

## 📝 编写测试用例

### 使用Playwright Codegen录制用例

1. **通过Web界面启动录制**：
   - 在Web控制界面的"用例录制"面板输入目标URL
   - 点击"启动录制"按钮

2. **命令行方式启动录制**：
```bash
# 直接录制
playwright codegen http://localhost:3000

# 录制并保存到文件
playwright codegen http://localhost:3000 --target python-async --output test_cases/teaching/test_recorded.py
```

3. **将录制的代码整合到测试用例中**：
   - 将录制生成的代码复制到 `test_cases/` 目录下对应的模块文件夹
   - 按照Page Object模式重构代码

### 手动编写测试用例

在 `test_cases/` 目录下创建测试文件，例如：

```python
"""
授课教学测试用例
"""
import pytest
from pages.desktop_page import DesktopPage
from pages.teaching_app import TeachingApp

@pytest.mark.teaching
class TestTeaching:
    """授课教学测试类"""
    
    @pytest.mark.asyncio
    async def test_open_teaching_app(self, desktop: DesktopPage, driver):
        """测试打开授课教学应用"""
        try:
            # 点击应用图标
            await desktop.click_app_icon("授课教学")
            
            # 创建应用页面对象
            teaching_app = TeachingApp(driver)
            await teaching_app.wait_for_load()
            
            # 验证应用已打开
            assert await teaching_app.is_app_opened()
            
        except Exception as e:
            # 失败时跳过步骤并重置状态
            await driver.skip_step(f"打开应用失败: {e}")
            await driver.reset_to_initial_state()
            raise
```

### 运行测试用例

```bash
# 运行所有测试
pytest

# 运行特定模块
pytest -m teaching

# 运行多个模块
pytest -m "teaching or exam"

# 详细输出
pytest -v -s
```

## 🔧 核心功能说明

### 1. 模块化应用管理

每个应用模块对应一个pytest标记（mark），在 `pytest.ini` 中定义：

```ini
markers =
    teaching: 授课教学模块测试
    exercise: 攻防演练模块测试
    exam: 考试测评模块测试
```

### 2. 数据库操作

```python
from core.db_client import DBClient

db = DBClient()
db.connect()

# 查询数据
results = db.execute_query("SELECT * FROM users WHERE id = %s", (1,))

# 更新数据
db.execute_update("UPDATE users SET name = %s WHERE id = %s", ("新名称", 1))

db.disconnect()
```

### 3. 通知服务

```python
from core.notification import NotificationService

notification = NotificationService()

# 发送钉钉消息
notification.send_dingtalk_message("测试完成", "测试通知")

# 发送邮件
notification.send_email("测试报告", "测试内容")

# 发送测试报告
notification.send_test_report(
    modules=["teaching", "exam"],
    total=10,
    passed=8,
    failed=2,
    skipped=0,
    duration=120.5
)
```

### 4. 失败处理机制

测试用例中可以使用以下方法处理失败：

```python
# 跳过当前步骤
await driver.skip_step("步骤跳过原因")

# 重置到初始状态
await driver.reset_to_initial_state()
```

### 5. Page Object模式

每个应用页面都封装为独立的Page Object类，例如：

```python
class TeachingApp(BasePage):
    async def start_teaching(self):
        """开始授课"""
        await self.driver.click('button:has-text("开始授课")')
    
    async def select_course(self, course_name: str):
        """选择课程"""
        await self.driver.click(f'[data-course="{course_name}"]')
```

## 🎯 最佳实践

1. **使用Page Object模式** - 将页面操作封装在Page类中，测试用例只关注业务逻辑
2. **合理使用等待** - 使用Playwright的自动等待机制，避免硬编码sleep
3. **错误处理** - 在关键步骤使用try-except，支持跳过和重置
4. **模块化设计** - 每个应用模块独立，便于维护和扩展
5. **录制+重构** - 使用Codegen录制基础操作，然后重构为Page Object模式

## 📊 测试报告

项目支持多种测试报告格式：

- **pytest-html**: 生成HTML报告
  ```bash
  pytest --html=report.html
  ```

- **Allure**: 生成Allure报告（需安装allure-pytest）
  ```bash
  pytest --alluredir=allure-results
  allure serve allure-results
  ```

## 🔍 常见问题

### Q: 如何定位"Web桌面"中的动态元素？

A: 优先使用Playwright的语义化定位方式：
- `page.get_by_role()` - 通过角色定位
- `page.get_by_text()` - 通过文本定位
- `page.get_by_label()` - 通过标签定位

避免使用不稳定的CSS选择器。

### Q: 如何处理弹窗应用？

A: 使用Page Object模式，为每个应用创建独立的Page类，封装应用内的操作。

### Q: 测试用例卡住怎么办？

A: 使用 `driver.skip_step()` 跳过当前步骤，或使用 `driver.reset_to_initial_state()` 重置状态。

### Q: 如何添加新的应用模块？

1. 在 `config/module_config.yaml` 中添加模块配置
2. 在 `pages/` 目录下创建应用页面类
3. 在 `test_cases/` 目录下创建测试用例
4. 在 `pytest.ini` 中添加模块标记

## 📚 更多资源

- [Playwright文档](https://playwright.dev/python/)
- [pytest文档](https://docs.pytest.org/)
- [NiceGUI文档](https://nicegui.io/)
- [PyMySQL文档](https://pymysql.readthedocs.io/)

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交Issue和Pull Request！

---

**注意**: 这是一个自动化测试框架，请根据实际Web应用的前端技术栈调整元素定位策略。

