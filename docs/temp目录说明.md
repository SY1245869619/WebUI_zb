# temp 目录说明

## 📁 目录概述

`temp/` 目录用于存储项目的临时文件和运行时数据，这些文件在程序运行过程中自动生成，可以安全删除（程序会重新创建）。

## 📋 目录结构

```
temp/
├── address_info_shown.txt      # 网络地址信息显示标记
├── address_info.lock            # 地址信息显示锁文件
├── recording_cookies.json       # 录制工具登录状态（自动生成）
└── browser_user_data/           # Playwright浏览器用户数据目录
    └── Default/                 # 浏览器配置、缓存、Cookie等
```

## 🔍 文件详细说明

### 1. `address_info_shown.txt`

**用途**：标记网络地址信息是否已显示

**说明**：
- 在 `run.py` 启动时，系统会检测并显示所有可用的网络地址（localhost、局域网IP等）
- 为了避免在多进程环境下重复显示，使用此文件作为标记
- 文件存在表示地址信息已经显示过，不会再次显示

**生成位置**：`run.py` 的 `show_address_info()` 函数

**是否可以删除**：✅ 可以，删除后下次启动会重新显示地址信息

---

### 2. `address_info.lock`

**用途**：线程锁文件，防止多线程同时显示地址信息

**说明**：
- 配合 `address_info_shown.txt` 使用，确保线程安全
- 防止多个线程同时创建标记文件

**是否可以删除**：✅ 可以，程序会自动重新创建

---

### 3. `recording_cookies.json`

**用途**：保存录制工具的登录状态（Cookies 和 Storage State）

**说明**：
- 当使用"启动录制"功能时，系统会：
  1. 先在一个浏览器中自动登录
  2. 保存登录状态（Cookies、LocalStorage等）到此文件
  3. 启动 Playwright Codegen 时加载此文件，实现自动登录

**生成位置**：`utils/recording_auto_login.py` 的 `auto_login_and_start_codegen()` 函数

**文件内容示例**：
```json
{
  "cookies": [
    {
      "name": "session_id",
      "value": "xxx",
      "domain": "10.70.70.96",
      "path": "/"
    }
  ],
  "origins": []
}
```

**是否可以删除**：✅ 可以，但删除后下次录制需要重新登录

**注意事项**：
- 此文件包含登录凭证，请勿提交到版本控制系统
- 如果登录状态过期，可以删除此文件让系统重新登录

---

### 4. `browser_user_data/`

**用途**：Playwright 浏览器的用户数据目录

**说明**：
- 这是 Chromium 浏览器的用户数据目录
- 包含浏览器的配置、缓存、Cookie、历史记录、扩展等数据
- 当使用 `--user-data-dir` 参数启动浏览器时会使用此目录

**目录内容**：
- `Default/`：默认用户配置文件
  - `Cache/`：浏览器缓存
  - `Cookies`：Cookie 数据库
  - `History`：浏览历史
  - `Local Storage/`：本地存储数据
  - `Preferences`：浏览器偏好设置
  - 等等...

**是否可以删除**：✅ 可以，但删除后：
- 浏览器缓存会清空（可能影响性能）
- 已保存的登录状态会丢失
- 浏览器设置会重置

**注意事项**：
- 此目录可能占用较大磁盘空间（几百MB到几GB）
- 如果磁盘空间不足，可以定期清理此目录

---

## 🧹 清理建议

### 定期清理

`temp/` 目录中的文件可以定期清理，不会影响程序功能：

```bash
# 清理所有临时文件（保留目录结构）
rm -rf temp/*

# 或者只清理特定文件
rm temp/address_info_shown.txt
rm temp/recording_cookies.json
rm -rf temp/browser_user_data/
```

### 自动清理脚本

可以创建一个清理脚本 `tools/clean_temp.py`：

```python
"""清理临时文件"""
from pathlib import Path

temp_dir = Path("temp")
if temp_dir.exists():
    # 删除所有文件
    for item in temp_dir.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            import shutil
            shutil.rmtree(item)
    print("✅ 临时文件已清理")
else:
    print("ℹ️ temp 目录不存在")
```

---

## ⚠️ 注意事项

1. **不要提交到 Git**：
   - `temp/` 目录已在 `.gitignore` 中忽略（如果未忽略，请添加）
   - 这些文件包含运行时数据和可能的敏感信息

2. **磁盘空间**：
   - `browser_user_data/` 可能占用较大空间
   - 如果磁盘空间不足，可以删除此目录

3. **登录状态**：
   - 删除 `recording_cookies.json` 后，下次录制需要重新登录
   - 如果登录状态过期，删除此文件可以强制重新登录

4. **多进程环境**：
   - `address_info_shown.txt` 和 `address_info.lock` 用于多进程同步
   - 不要手动修改这些文件

---

## 🔧 相关代码位置

- **地址信息显示**：`run.py` (第 76-120 行)
- **录制工具登录**：`utils/recording_auto_login.py` (第 99-102 行)
- **浏览器用户数据**：Playwright 自动管理

---

## 📝 总结

| 文件/目录 | 用途 | 可删除 | 删除影响 |
|---------|------|--------|---------|
| `address_info_shown.txt` | 地址信息显示标记 | ✅ | 下次启动会重新显示 |
| `address_info.lock` | 线程锁文件 | ✅ | 无影响 |
| `recording_cookies.json` | 录制工具登录状态 | ✅ | 下次录制需重新登录 |
| `browser_user_data/` | 浏览器用户数据 | ✅ | 缓存和设置会重置 |

**建议**：定期清理 `temp/` 目录，特别是 `browser_user_data/` 子目录，以释放磁盘空间。

