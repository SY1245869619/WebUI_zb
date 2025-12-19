"""
NiceGUI Web控制界面主入口
"""
import asyncio
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from nicegui import ui, app
from web_ui.components.module_selector import ModuleSelector
from web_ui.components.notification_config import NotificationConfig
from core.notification import NotificationService
import yaml


class WebUIController:
    """WebUI控制器"""
    
    def __init__(self):
        """初始化控制器"""
        self.module_selector = ModuleSelector()
        self.notification_config = NotificationConfig()
        self.is_running = False
        self.current_process = None
        self.log_content = []
        self.max_log_lines = 1000
        
    def render(self):
        """渲染主界面"""
        # 设置页面标题和样式
        ui.page_title('WebUI自动化测试控制台')
        
        # 主容器
        with ui.column().classes('w-full max-w-7xl mx-auto p-6 gap-4'):
            # 标题
            ui.label('WebUI自动化测试控制台').classes('text-3xl font-bold mb-6')
            
            # 左侧：配置区域
            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('w-1/2 gap-4'):
                    # 模块选择
                    self.module_selector.render()
                    
                    # 通知配置
                    self.notification_config.render()
                
                # 右侧：执行控制区域
                with ui.column().classes('w-1/2 gap-4'):
                    self._render_execution_panel()
                    self._render_log_panel()
                    self._render_recording_panel()
    
    def _render_execution_panel(self):
        """渲染执行控制面板"""
        with ui.card().classes('w-full'):
            ui.label('执行控制').classes('text-lg font-bold mb-4')
            
            # 状态显示
            self.status_label = ui.label('状态: 就绪').classes('mb-4')
            self.progress_bar = ui.linear_progress(0).classes('w-full mb-4').set_visibility(False)
            
            # 执行按钮
            with ui.row().classes('w-full gap-2'):
                self.start_btn = ui.button(
                    '开始执行',
                    on_click=self.start_execution,
                    icon='play_arrow'
                ).classes('flex-1')
                
                self.stop_btn = ui.button(
                    '停止执行',
                    on_click=self.stop_execution,
                    icon='stop',
                    color='red'
                ).classes('flex-1').set_enabled(False)
            
            # 执行选项
            with ui.row().classes('w-full mt-4'):
                self.headless_checkbox = ui.checkbox('无头模式', value=False)
                self.verbose_checkbox = ui.checkbox('详细输出', value=True)
    
    def _render_log_panel(self):
        """渲染日志面板"""
        with ui.card().classes('w-full'):
            ui.label('执行日志').classes('text-lg font-bold mb-4')
            
            # 日志显示区域
            self.log_area = ui.log().classes('w-full h-64')
            
            # 日志控制按钮
            with ui.row().classes('w-full mt-2'):
                ui.button('清空日志', on_click=self.clear_log, icon='clear').classes('mr-2')
                ui.button('导出日志', on_click=self.export_log, icon='download')
    
    def _render_recording_panel(self):
        """渲染录制面板"""
        with ui.card().classes('w-full'):
            ui.label('用例录制').classes('text-lg font-bold mb-4')
            
            ui.markdown("""
            **使用Playwright Codegen录制用例：**
            
            1. 点击下方按钮打开录制工具
            2. 在浏览器中操作目标Web应用
            3. 录制工具会自动生成Python代码
            4. 将生成的代码保存到 `test_cases/` 目录下对应的模块文件夹中
            
            **录制命令：**
            ```bash
            playwright codegen <目标URL>
            ```
            """).classes('mb-4')
            
            with ui.row().classes('w-full gap-2'):
                self.record_url_input = ui.input(
                    '目标URL',
                    placeholder='http://localhost:3000',
                    value='http://localhost:3000'
                ).classes('flex-1')
                
                ui.button(
                    '启动录制',
                    on_click=self.start_recording,
                    icon='videocam'
                )
    
    def start_execution(self):
        """开始执行测试"""
        if self.is_running:
            ui.notify('测试正在运行中，请先停止', type='warning')
            return
        
        # 获取选中的模块
        selected_marks = self.module_selector.get_selected_marks()
        if not selected_marks:
            ui.notify('请至少选择一个应用模块', type='warning')
            return
        
        # 更新状态
        self.is_running = True
        self.status_label.text = '状态: 运行中...'
        self.start_btn.set_enabled(False)
        self.stop_btn.set_enabled(True)
        self.progress_bar.set_visibility(True)
        self.progress_bar.value = 0.1
        
        # 保存通知配置
        self.notification_config.save_config()
        
        # 构建pytest命令
        cmd = ['pytest', '-m', selected_marks, '-v']
        
        if self.headless_checkbox.value:
            # 如果选择无头模式，需要更新配置文件
            self._update_headless_config(True)
        
        if self.verbose_checkbox.value:
            cmd.append('-s')
        
        # 添加其他pytest选项
        cmd.extend(['--tb=short', '--asyncio-mode=auto'])
        
        # 在后台线程中执行
        thread = threading.Thread(target=self._run_pytest, args=(cmd,), daemon=True)
        thread.start()
        
        self.log('开始执行测试...')
        self.log(f'执行模块: {", ".join(self.module_selector.get_selected_module_names())}')
        self.log(f'执行命令: {" ".join(cmd)}')
    
    def _run_pytest(self, cmd: list):
        """在后台线程中运行pytest"""
        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                bufsize=1
            )
            
            # 实时读取输出
            for line in iter(self.current_process.stdout.readline, ''):
                if line:
                    self.log(line.strip())
                    self.log_content.append(line.strip())
                    if len(self.log_content) > self.max_log_lines:
                        self.log_content.pop(0)
            
            self.current_process.wait()
            
            # 执行完成
            ui.run_javascript('window.location.reload()')  # 刷新页面以更新状态
            
        except Exception as e:
            self.log(f'执行出错: {e}')
        finally:
            self.is_running = False
            self.status_label.text = '状态: 执行完成'
            self.start_btn.set_enabled(True)
            self.stop_btn.set_enabled(False)
            self.progress_bar.set_visibility(False)
            
            # 发送通知
            self._send_notification()
    
    def stop_execution(self):
        """停止执行"""
        if self.current_process:
            self.current_process.terminate()
            self.log('测试执行已停止')
            self.is_running = False
            self.status_label.text = '状态: 已停止'
            self.start_btn.set_enabled(True)
            self.stop_btn.set_enabled(False)
            self.progress_bar.set_visibility(False)
    
    def _update_headless_config(self, headless: bool):
        """更新无头模式配置"""
        config_path = Path("config/settings.yaml")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            config['playwright']['headless'] = headless
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    def _send_notification(self):
        """发送执行完成通知"""
        try:
            notification = NotificationService()
            # 这里可以解析日志获取测试结果
            # 简化处理，实际应该解析pytest输出
            notification.send_test_report(
                modules=self.module_selector.get_selected_module_names(),
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                duration=0,
                error_details=[]
            )
        except Exception as e:
            self.log(f'发送通知失败: {e}')
    
    def start_recording(self):
        """启动录制工具"""
        url = self.record_url_input.value
        if not url:
            ui.notify('请输入目标URL', type='warning')
            return
        
        try:
            # 启动Playwright Codegen
            subprocess.Popen(
                ['playwright', 'codegen', url],
                shell=True
            )
            ui.notify('录制工具已启动', type='positive')
        except Exception as e:
            ui.notify(f'启动录制工具失败: {e}', type='negative')
    
    def log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_area.push(log_message)
    
    def clear_log(self):
        """清空日志"""
        self.log_area.clear()
        self.log_content.clear()
    
    def export_log(self):
        """导出日志"""
        if not self.log_content:
            ui.notify('没有日志可导出', type='warning')
            return
        
        log_file = Path(f"logs/execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.log_content))
        
        ui.notify(f'日志已导出到: {log_file}', type='positive')


def main():
    """主函数"""
    controller = WebUIController()
    controller.render()
    
    # 加载配置
    config_path = Path("config/settings.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        web_config = config.get('web_ui', {})
        host = web_config.get('host', '0.0.0.0')
        port = web_config.get('port', 8080)
    else:
        host = '0.0.0.0'
        port = 8080
    
    ui.run(host=host, port=port, title='WebUI自动化测试控制台')


if __name__ in {"__main__", "__mp_main__"}:
    main()

