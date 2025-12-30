"""
NiceGUI Web控制界面主入口

@File  : main.py
@Author: shenyuan
"""
import asyncio
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from nicegui import ui, app
from web_ui.components.module_selector import ModuleSelector
from web_ui.components.notification_config import NotificationConfig
from web_ui.components.login_config import LoginConfig
from core.notification import NotificationService
import yaml


class WebUIController:
    """WebUI控制器"""
    
    def __init__(self):
        """初始化控制器"""
        self.module_selector = ModuleSelector()
        self.notification_config = NotificationConfig()
        self.login_config = LoginConfig()
        self.is_running = False
        self.current_process = None
        self.log_content = []
        self.max_log_lines = 1000
        self.test_duration = 0
        self.test_output = []
        self.current_report_path = None
        
    def render(self):
        """渲染主界面"""
        # 设置页面标题和样式
        ui.page_title('WebUI自动化测试控制台')
        
        # 添加静态文件服务（用于加载logo、视频等资源）
        # NiceGUI会自动处理 assets/ 目录，但需要确保路径正确
        try:
            app.add_static_files('/assets', Path('assets'))
        except:
            pass  # 如果已经添加过，忽略错误
        
        # 确保视频目录存在
        video_dir = Path('assets/videos')
        video_dir.mkdir(parents=True, exist_ok=True)
        
        # 添加全屏功能（手动控制，点击按钮全屏）
        ui.add_head_html('''
        <script>
            // 监听全屏状态变化，更新按钮文字
            function updateFullscreenButton() {
                const isFullscreen = !!(document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement);
                const btn = document.getElementById('fullscreen-toggle-btn');
                if (btn) {
                    const icon = isFullscreen ? 'fullscreen_exit' : 'fullscreen';
                    const text = isFullscreen ? '退出全屏' : '全屏';
                    // 使用inline-flex确保图标和文字在同一行，不换行
                    btn.innerHTML = '<span style="display: inline-flex; align-items: center; white-space: nowrap;"><i class="material-icons" style="font-size: 18px; vertical-align: middle; margin-right: 4px; flex-shrink: 0;">' + icon + '</i><span style="white-space: nowrap;">' + text + '</span></span>';
                    btn.setAttribute('data-fullscreen', isFullscreen);
                    // 确保按钮样式保持不换行
                    btn.style.whiteSpace = 'nowrap';
                }
            }
            
            // 监听全屏状态变化事件
            document.addEventListener('fullscreenchange', updateFullscreenButton);
            document.addEventListener('webkitfullscreenchange', updateFullscreenButton);
            document.addEventListener('msfullscreenchange', updateFullscreenButton);
            
            // 全屏切换函数
            function toggleFullscreen() {
                if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
                    // 进入全屏
                    if (document.documentElement.requestFullscreen) {
                        document.documentElement.requestFullscreen().catch(err => {
                            console.log('全屏请求失败:', err);
                        });
                    } else if (document.documentElement.webkitRequestFullscreen) {
                        document.documentElement.webkitRequestFullscreen();
                    } else if (document.documentElement.msRequestFullscreen) {
                        document.documentElement.msRequestFullscreen();
                    }
                } else {
                    // 退出全屏
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.webkitExitFullscreen) {
                        document.webkitExitFullscreen();
                    } else if (document.msExitFullscreen) {
                        document.msExitFullscreen();
                    }
                }
            }
        </script>
        ''')
        
        # 添加华为/苹果风格的CSS样式 - 简洁优雅，高可读性
        ui.add_head_html('''
        <style>
            /* 美化滚动条 */
            ::-webkit-scrollbar {
                width: 10px;
                height: 10px;
            }
            ::-webkit-scrollbar-track {
                background: rgba(10, 22, 40, 0.5);
                border-radius: 10px;
            }
            ::-webkit-scrollbar-thumb {
                background: linear-gradient(135deg, rgba(0, 150, 255, 0.6) 0%, rgba(0, 200, 255, 0.6) 100%);
                border-radius: 10px;
                border: 2px solid rgba(10, 22, 40, 0.5);
            }
            ::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(135deg, rgba(0, 150, 255, 0.8) 0%, rgba(0, 200, 255, 0.8) 100%);
            }
            /* Firefox滚动条 */
            * {
                scrollbar-width: thin;
                scrollbar-color: rgba(0, 150, 255, 0.6) rgba(10, 22, 40, 0.5);
            }
            body {
                background: linear-gradient(135deg, #0a1628 0%, #1a2332 50%, #0f1b2e 100%);
                color: #e0e6ed;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
            }
            .q-page {
                padding: 0 !important;
            }
            .q-page {
                background: transparent !important;
            }
            .q-card {
                background: rgba(26, 35, 50, 0.8) !important;
                border: 1px solid rgba(0, 150, 255, 0.2) !important;
                border-radius: 24px !important;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 
                           0 4px 16px rgba(0, 150, 255, 0.2) !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                margin-bottom: 0 !important;
                padding: 0 !important;
                overflow: hidden;
                backdrop-filter: blur(10px);
            }
            .q-card:hover {
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), 
                           0 6px 20px rgba(0, 150, 255, 0.3) !important;
                transform: translateY(-3px);
                border-color: rgba(0, 150, 255, 0.4) !important;
            }
            .card-spacing {
                margin-bottom: 24px !important;
            }
            .q-btn--unelevated {
                background: linear-gradient(135deg, #0096ff 0%, #00b4ff 100%) !important;
                border: none !important;
                border-radius: 16px !important;
                box-shadow: 0 4px 16px rgba(0, 150, 255, 0.4) !important;
                transition: all 0.3s ease !important;
                color: #ffffff !important;
                font-weight: 600 !important;
                padding: 14px 28px !important;
                min-height: 52px !important;
            }
            .q-btn--unelevated:hover {
                background: linear-gradient(135deg, #00b4ff 0%, #00d4ff 100%) !important;
                box-shadow: 0 6px 20px rgba(0, 150, 255, 0.5) !important;
                transform: translateY(-2px);
            }
            .q-btn--outline {
                border: 1.5px solid #0096ff !important;
                color: #0096ff !important;
                background: transparent !important;
                border-radius: 16px !important;
                padding: 14px 28px !important;
                min-height: 52px !important;
            }
            .q-btn--outline:hover {
                background: rgba(0, 150, 255, 0.15) !important;
                border-color: #00b4ff !important;
            }
            .q-field__label {
                color: #a0a8b0 !important;
                font-weight: 500 !important;
            }
            .q-input, .q-textarea {
                background: rgba(255, 255, 255, 0.08) !important;
                border: 1.5px solid rgba(0, 150, 255, 0.3) !important;
                border-radius: 16px !important;
                color: #e0e6ed !important;
                font-size: 15px !important;
                margin-bottom: 20px !important;
                padding: 16px 20px !important;
                min-height: 52px !important;
                transition: all 0.3s ease !important;
            }
            .q-input:focus, .q-textarea:focus {
                background: rgba(255, 255, 255, 0.12) !important;
                border-color: #0096ff !important;
                box-shadow: 0 0 0 4px rgba(0, 150, 255, 0.2), 0 4px 12px rgba(0, 150, 255, 0.3) !important;
            }
            .q-field {
                margin-bottom: 20px !important;
            }
            .q-btn {
                margin: 6px !important;
                padding: 14px 28px !important;
                min-height: 52px !important;
                cursor: pointer !important;
                border-radius: 16px !important;
            }
            .q-input input, .q-textarea textarea {
                color: #e0e6ed !important;
            }
            .q-checkbox__label {
                color: #e0e6ed !important;
            }
            .title-header {
                background: linear-gradient(135deg, rgba(0, 150, 255, 0.2) 0%, rgba(0, 100, 200, 0.1) 100%);
                border-left: 4px solid #0096ff;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 24px;
                box-shadow: 0 4px 15px rgba(0, 150, 255, 0.2);
            }
            .title-text {
                font-size: 2.5rem;
                font-weight: 700;
                background: linear-gradient(135deg, #0096ff 0%, #00d4ff 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-shadow: 0 0 30px rgba(0, 150, 255, 0.5);
                letter-spacing: 2px;
            }
            .section-title {
                font-size: 1.25rem;
                font-weight: 600;
                color: #e0e6ed;
                margin-bottom: 24px;
                padding-bottom: 16px;
                border-bottom: 2px solid rgba(0, 150, 255, 0.3);
            }
            .config-section {
                margin-bottom: 32px;
            }
            .card-content {
                padding: 32px 40px;
            }
            .module-item-card {
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                border: 1.5px solid rgba(0, 150, 255, 0.3) !important;
                background: rgba(26, 35, 50, 0.9) !important;
                backdrop-filter: blur(10px);
            }
            .module-item-card:hover {
                background: rgba(0, 150, 255, 0.15) !important;
                transform: translateY(-4px) scale(1.05);
                box-shadow: 0 8px 24px rgba(0, 150, 255, 0.4), 
                           0 4px 12px rgba(0, 150, 255, 0.2) !important;
                border-color: #0096ff !important;
            }
            .module-checkbox .q-checkbox__label {
                color: #e0e6ed !important;
                font-weight: 600 !important;
                font-size: 14px !important;
            }
            .module-description {
                color: #a0a8b0 !important;
                font-size: 11px !important;
            }
            .module-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
                gap: 16px;
                width: 100%;
            }
            .status-ready {
                color: #00ff88;
                font-weight: 600;
            }
            .status-running {
                color: #ffaa00;
                font-weight: 600;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.6; }
            }
            /* ========== 日志区域样式 ========== */
            /* 【可调整参数】日志区域外观、颜色、字体 */
            /* - background: 背景色（rgba(10, 22, 40, 0.7)可调整透明度，0.7改为0.6、0.8等） */
            /* - border: 边框（1.5px可改为1px、2px等，rgba(0, 150, 255, 0.4)可调整颜色和透明度） */
            /* - border-radius: 圆角（16px可改为12px、20px等） */
            /* - font-size: 字体大小（14px可改为12px、13px、15px等） */
            /* - color: 文字颜色（#b0c4de浅蓝色，#e0e6ed白色，#ffffff纯白色等） */
            /* - padding: 内边距（24px可改为16px、20px、28px等） */
            .log-area {
                background: rgba(10, 22, 40, 0.7) !important;
                border: 1.5px solid rgba(0, 150, 255, 0.4) !important;
                border-radius: 16px;
                font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
                font-size: 12px;
                color: #b0c4de;
                padding: 10px !important;
                overflow-y: auto !important;
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
                margin: 0 !important;
            }
            .log-area::-webkit-scrollbar {
                width: 8px;
            }
            .log-area::-webkit-scrollbar-track {
                background: rgba(10, 22, 40, 0.3);
                border-radius: 8px;
            }
            .log-area::-webkit-scrollbar-thumb {
                background: linear-gradient(135deg, rgba(0, 150, 255, 0.7) 0%, rgba(0, 200, 255, 0.7) 100%);
                border-radius: 8px;
            }
            .log-area::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(135deg, rgba(0, 150, 255, 0.9) 0%, rgba(0, 200, 255, 0.9) 100%);
            }
            .cyber-grid {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-image: 
                    linear-gradient(rgba(0, 150, 255, 0.08) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(0, 150, 255, 0.08) 1px, transparent 1px);
                background-size: 50px 50px;
                pointer-events: none;
                z-index: -1;
            }
        </style>
        ''')
        
        # 添加网格背景
        ui.html('<div class="cyber-grid"></div>', sanitize=False)
        
        # 主容器 - 占满整个页面（修复滚动bug - 移除max-height限制，允许正常滚动）
        with ui.column().classes('w-full h-full').style('min-height: 100vh; padding: 32px 40px; box-sizing: border-box; position: relative;'):
            # ========== 全屏切换按钮 ==========
            # 【可调整参数】位置、大小、颜色、样式
            # - top/right: 按钮位置（距离顶部和右侧的距离）
            # - padding: 按钮内边距（控制按钮大小）
            # - font-size: 文字大小
            # - background: 背景颜色（rgba格式，可调整透明度）
            # - border-radius: 圆角大小
            ui.button('全屏', icon='fullscreen', on_click=lambda: ui.run_javascript('toggleFullscreen()')).classes('fixed').style('top: 1px; right: 1px; z-index: 10000; background: rgba(0, 150, 255, 0.85); border: 1px solid rgba(0, 200, 255, 0.5); border-radius: 8px; padding: 6px 12px; font-size: 11px; font-weight: 500; color: #ffffff; box-shadow: 0 2px 8px rgba(0, 150, 255, 0.4); white-space: nowrap; min-width: 80px; display: inline-flex; align-items: center; justify-content: center;').props('id=fullscreen-toggle-btn')
            
            # ========== Banner区域 ==========
            # 【可调整参数】高度、背景色、边框、阴影、内边距
            # - mb-8: Banner底部外边距（可改为mb-6、mb-4等降低高度）
            # - p-10: Banner内边距（可改为p-8、p-6等降低高度）
            # - background: 渐变背景色（可调整rgba值改变颜色和透明度）
            # - border: 边框样式（可调整颜色、粗细）
            # - box-shadow: 阴影效果（可调整颜色、模糊度、扩散范围）
            # - font-size: 标题字体大小（3.5rem可改为2.5rem、2rem等降低高度）
            # - gap-3/mb-6: 标题区域间距（可减小以降低高度）
            with ui.card().classes('w-full mb-6').style('background: linear-gradient(135deg, rgba(0, 150, 255, 0.4) 0%, rgba(0, 200, 255, 0.3) 50%, rgba(100, 50, 255, 0.3) 100%); border: 2px solid rgba(0, 200, 255, 0.5); box-shadow: 0 12px 48px rgba(0, 150, 255, 0.4), inset 0 0 60px rgba(0, 200, 255, 0.1); position: relative; overflow: hidden;'):
                # 动态背景效果
                ui.html('''
                <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: 
                    radial-gradient(circle at 20% 50%, rgba(0, 200, 255, 0.3) 0%, transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(100, 50, 255, 0.2) 0%, transparent 50%);
                    pointer-events: none; z-index: 0;"></div>
                ''', sanitize=False)
                
                # 【可调整参数】内边距：p-4进一步降低高度，让登录模块完全显示
                with ui.column().classes('w-full p-4').style('position: relative; z-index: 1;'):
                    # 主标题：WebUI自动化测试控制台（居中突出显示，压缩高度）
                    # 【可调整参数】标题大小、间距、颜色
                    # - font-size: 标题字体大小（2.2rem可改为2rem、1.8rem等进一步降低高度）
                    # - gap-1: 标题区域间距（可改为gap-0.5）
                    # - mb-2: 标题底部间距（可改为mb-1）
                    # - color: 文字颜色（#ffffff白色，#b0d4ff浅蓝色等）
                    with ui.column().classes('items-center gap-1 mb-2'):
                        # 使用用户提供的logo替换盾牌emoji
                        # 请将logo文件放在 assets/images/company_logo.png
                        logo_path = Path("assets/images/company_logo.png")
                        
                        # 使用ui.row来包含logo和标题，确保logo能正常显示
                        with ui.row().classes('items-center justify-center gap-3'):
                            # Logo显示（如果存在）- 使用base64编码确保显示
                            if logo_path.exists():
                                try:
                                    # 使用base64编码，确保图片能正常显示
                                    import base64
                                    with open(logo_path, 'rb') as f:
                                        logo_data = base64.b64encode(f.read()).decode()
                                        logo_ext = logo_path.suffix.lower()
                                        mime_type = 'image/png' if logo_ext == '.png' else 'image/jpeg' if logo_ext in ['.jpg', '.jpeg'] else 'image/svg+xml' if logo_ext == '.svg' else 'image/png'
                                        ui.html(f'<img src="data:{mime_type};base64,{logo_data}" style="width: 80px; height: 80px; display: inline-block; margin-right: 12px; vertical-align: middle; filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.9)); object-fit: contain;" alt="Logo">', sanitize=False)
                                except Exception as e:
                                    # 如果base64编码失败，尝试使用ui.image
                                    try:
                                        ui.image(str(logo_path)).style('width: 80px; height: 80px; object-fit: contain; filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.9));')
                                    except:
                                        # 最后尝试使用HTML路径方式
                                        ui.html(f'<img src="/assets/images/company_logo.png" style="width: 80px; height: 80px; display: inline-block; margin-right: 12px; vertical-align: middle; filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.9)); object-fit: contain;" alt="Logo">', sanitize=False)
                            else:
                                # 如果logo不存在，使用占位符盾牌
                                ui.html('<span style="font-size: 3.5rem; filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.9)); display: inline-block; margin-right: 10px; vertical-align: middle;">🛡️</span>', sanitize=False)
                            
                            # 标题文字（压缩字体大小，降低高度）
                            ui.html('''
                            <div style="text-align: center;">
                                <h1 style="font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #ffffff 0%, #00d4ff 50%, #ffffff 100%); 
                                    -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                                    background-clip: text; text-shadow: 0 0 40px rgba(0, 212, 255, 0.6), 0 0 80px rgba(0, 150, 255, 0.4);
                                    letter-spacing: 2px; margin: 0; animation: glow 3s ease-in-out infinite alternate;">
                                    WebUI自动化测试控制台
                                </h1>
                            </div>
                            <style>
                            @keyframes glow {
                                from { filter: brightness(1); }
                                to { filter: brightness(1.2); }
                            }
                            </style>
                            ''', sanitize=False)
                        
                        # 副标题（压缩字体大小）
                        ui.html('''
                        <p style="font-size: 0.85rem; color: #b0d4ff; font-weight: 500; letter-spacing: 1px; margin: 2px 0 0 0;">
                            网络安全自动化测试平台 | Network Security Automation Testing Platform
                        </p>
                        ''', sanitize=False)
                    
                    # 公司名称（放在右下角，去掉图标）
                    # 【可调整参数】位置、大小、颜色
                    # - bottom-3/right-6: 位置（可改为bottom-2/right-4等）
                    # - color: 文字颜色（#a0c4ff、#80a4d4等）
                    with ui.row().classes('absolute bottom-3 right-6 items-end').style('position: absolute; bottom: 12px; right: 24px; z-index: 2;'):
                        with ui.column().classes('gap-0 items-end'):
                            ui.label('北京丈八网安网络科技有限公司').classes('text-xs font-medium').style('color: #a0c4ff; line-height: 1.2; opacity: 0.9;')
                            ui.label('Zeta Byte Network Security').classes('text-xs').style('color: #80a4d4; opacity: 0.8;')
            
            # 使用两列布局，让卡片更分散美观，占满页面（修复滚动bug）
            with ui.row().classes('w-full gap-8 items-start').style('width: 100%; flex-wrap: nowrap; align-items: stretch;'):
                # 左侧：配置区域（40%宽度）
                with ui.column().classes('flex-1').style('display: flex; flex-direction: column; gap: 24px; min-width: 0; flex: 0 0 40%;'):
                    # 登录配置（最重要，放在最前面）
                    self.login_config.render()
                    
                    # 模块选择
                    self.module_selector.render()
                    
                    # 通知配置
                    self.notification_config.render()
                
                # 右侧：执行控制区域（60%宽度，恢复原来的大小，修复滚动bug）
                with ui.column().classes('flex-1').style('display: flex; flex-direction: column; gap: 24px; min-width: 0; flex: 0 0 60%; overflow: visible;'):
                    self._render_execution_panel()  # 执行控制高度变小
                    self._render_log_panel()  # 执行日志高度变高，恢复原来的大小
                    self._render_recording_panel()
    
    def _render_execution_panel(self):
        """渲染执行控制面板（压缩布局，所有内容在一行，降低高度，修复滚动bug）
        
        【可调整参数】整体布局、间距、高度、颜色
        - padding: 卡片内边距（8px 20px可改为6px 16px等进一步降低高度）
        - margin-bottom: 各元素间距（mb-2、mb-3等）
        - font-size: 文字大小（12px、13px、14px等）
        - color: 文字颜色（#e0e6ed白色，#b0c4de浅蓝色等）
        """
        with ui.card().classes('w-full config-section').style('flex: 0 0 auto; overflow: hidden;'):
            # 【可调整参数】内边距：padding: 8px 20px（压缩高度），添加overflow: hidden防止滚动
            with ui.column().classes('card-content').style('padding: 8px 20px; overflow: hidden;'):
                # 【可调整参数】标题样式 - 压缩布局
                # - margin-bottom: 标题底部间距（6px可改为4px、8px等）
                # - font-size: 标题字体大小（0.95rem可改为0.9rem、1rem等）
                ui.label('⚡ 执行控制').classes('section-title').style('color: #e0e6ed; margin-bottom: 6px; font-size: 0.95rem; padding-bottom: 4px;')
                
                # 压缩布局：所有内容在一行（状态、按钮、选项都在一行，不换行）
                # 添加overflow: hidden和固定高度防止滚动bug
                with ui.row().classes('w-full items-center').style('display: flex; justify-content: space-between; align-items: center; width: 100%; gap: 12px; flex-wrap: nowrap; overflow: hidden; min-height: 40px; max-height: 50px;'):
                    # 状态显示在左侧（限制宽度防止溢出）
                    with ui.column().classes('items-start').style('flex: 0 0 auto; min-width: 80px; max-width: 120px; overflow: hidden;'):
                        self.status_label = ui.label('状态: 就绪').classes('status-ready').style('font-size: 12px; margin: 0; padding: 0; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;')
                        self.progress_bar = ui.linear_progress(0).classes('w-full mt-1').style('height: 3px; width: 100px; max-width: 100px;')
                        self.progress_bar.set_visibility(False)
                    
                    # 执行按钮在中间（压缩尺寸，限制宽度）
                    with ui.row().classes('gap-2').style('flex: 0 0 auto; display: flex; overflow: hidden;'):
                        self.start_btn = ui.button(
                            '开始执行',
                            on_click=self.start_execution,
                            icon='play_arrow'
                        ).style('min-height: 30px; padding: 4px 10px; font-size: 12px; flex-shrink: 0;')
                        
                        self.stop_btn = ui.button(
                            '停止执行',
                            on_click=self.stop_execution,
                            icon='stop',
                            color='red'
                        ).style('min-height: 30px; padding: 4px 10px; font-size: 12px; flex-shrink: 0;')
                        self.stop_btn.set_enabled(False)
                    
                    # 执行选项在右侧（压缩尺寸，在一行，不换行，限制宽度）
                    with ui.row().classes('gap-3').style('flex: 0 0 auto; display: flex; align-items: center; flex-wrap: nowrap; overflow: hidden;'):
                        self.headless_checkbox = ui.checkbox('无头模式', value=False).style('font-size: 12px; flex-shrink: 0;')
                        self.verbose_checkbox = ui.checkbox('详细输出', value=True).style('font-size: 12px; flex-shrink: 0;')
                        # 测试报告按钮（放在执行选项同一行）
                        ui.button(
                            '📊 测试报告',
                            on_click=self.show_test_reports,
                            icon='assessment'
                        ).style('min-height: 30px; padding: 4px 12px; font-size: 12px; background: rgba(0, 150, 255, 0.15); border: 1px solid rgba(0, 150, 255, 0.3);')
    
    def _render_log_panel(self):
        """渲染日志面板（增大输出框长度/宽度，占模块大部分，减少padding让日志区域更宽）
        
        【可调整参数】日志区域大小、颜色、字体
        - padding: 卡片内边距（10px 12px可改为8px 10px等，减少内边距可增大日志区域）
        - min-height: 日志区域最小高度（400px可改为350px、450px等）
        - font-size: 日志文字大小（12px可改为11px、13px等，减小可显示更多内容）
        - color: 日志文字颜色（#b0c4de浅蓝色，#e0e6ed白色等）
        - background: 日志背景色（rgba(10, 22, 40, 0.6)可调整透明度）
        - border: 日志边框（1.5px可改为1px、2px等，颜色可调整）
        """
        with ui.card().classes('w-full config-section').style('flex: 1 1 auto; display: flex; flex-direction: column; width: 100%; overflow: hidden;'):
            # 减少padding，让日志区域更宽（从16px 20px改为10px 12px）
            with ui.column().classes('card-content').style('padding: 10px 12px; display: flex; flex-direction: column; flex: 1; min-height: 0; width: 100%; box-sizing: border-box; height: 100%; overflow: hidden;'):
                # 【可调整参数】标题样式（压缩）
                # - margin-bottom: 标题底部间距（6px可改为4px、8px等，减少可增大日志区域）
                ui.label('📋 执行日志').classes('section-title').style('color: #e0e6ed; margin-bottom: 6px; padding-bottom: 4px; font-size: 0.95rem; flex-shrink: 0;')
                
                # 【可调整参数】日志显示区域大小 - 增大输出框长度（占模块大部分，确保100%宽度，固定高度不受其他模块影响）
                # - min-height: 最小高度（400px可改为350px、450px等）
                # - height: 固定高度，不受其他模块影响（使用calc计算，减去标题和按钮的高度）
                # - padding: 日志内边距（10px可改为8px、12px等，减少可显示更多内容）
                # - width: 确保100%宽度，使用calc减去可能的边距
                self.log_area = ui.log().classes('w-full log-area').style('flex: 1; min-height: 400px; height: calc(100% - 80px); max-height: none; overflow-y: auto; width: 100%; max-width: 100%; box-sizing: border-box; margin: 0;')
                
                # 【可调整参数】日志控制按钮样式（压缩，固定位置，不受其他模块影响）
                # - margin-top: 按钮顶部间距（mt-2可改为mt-1、mt-3等，减少可增大日志区域）
                with ui.row().classes('w-full mt-2').style('flex-shrink: 0;'):
                    ui.button('清空日志', on_click=self.clear_log, icon='clear').classes('mr-2').style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
                    ui.button('导出日志', on_click=self.export_log, icon='download').style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
    
    def _render_recording_panel(self):
        """渲染录制面板"""
        with ui.card().classes('w-full config-section'):
            with ui.column().classes('card-content').style('padding: 32px 40px; position: relative;'):
                # 标题和按钮（右上角，同一行）
                with ui.row().classes('w-full items-center justify-between').style('display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px;'):
                    ui.label('🎬 用例录制').classes('section-title').style('color: #e0e6ed; margin: 0;')
                    # 按钮组（教程视频和代码转换在同一行）
                    with ui.row().classes('gap-2'):
                        ui.button(
                            '代码转换',
                            on_click=self.show_code_converter,
                            icon='code'
                        ).style('min-height: 36px; padding: 6px 14px; font-size: 13px;')
                        ui.button(
                            '教程视频',
                            on_click=self.show_tutorial_video,
                            icon='play_circle'
                        ).style('min-height: 36px; padding: 6px 14px; font-size: 13px;')
                
                # 使用更好的文字样式，增加内边距
                ui.markdown("""
                <div style="padding: 0 8px; line-height: 1.8;">
                <p style="font-size: 15px; font-weight: 600; color: #e0e6ed; margin-bottom: 16px;">使用Playwright Codegen录制用例：</p>
                
                <ol style="color: #b0c4de; font-size: 14px; line-height: 2; padding-left: 24px; margin-bottom: 20px;">
                <li style="margin-bottom: 8px;">点击下方"启动录制"按钮打开录制工具</li>
                <li style="margin-bottom: 8px;">在浏览器中操作目标Web应用</li>
                <li style="margin-bottom: 8px;">录制工具会自动生成Python代码</li>
                <li style="margin-bottom: 8px;">复制生成的代码，点击"代码转换"按钮自动转换为测试用例</li>
                </ol>
                
                <p style="font-size: 15px; font-weight: 600; color: #e0e6ed; margin-bottom: 12px;">录制命令：</p>
                <pre style="background: rgba(0, 150, 255, 0.15); border: 1px solid rgba(0, 150, 255, 0.3); border-radius: 8px; padding: 12px 16px; color: #00d4ff; font-family: 'SF Mono', 'Monaco', 'Consolas', monospace; font-size: 13px; margin: 0;">playwright codegen &lt;目标URL&gt;</pre>
                </div>
                """).style('color: #b0c4de;')
            
            with ui.row().classes('w-full gap-2').style('display: flex; align-items: center;'):
                # 从配置文件读取默认URL
                config_path = Path("config/settings.yaml")
                default_url = 'http://10.70.70.96/Shenyuan_9#/login'
                if config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = yaml.safe_load(f)
                            if config.get('login', {}).get('url'):
                                default_url = config['login']['url']
                    except:
                        pass
                
                # 目标URL输入框（设置固定高度，与按钮一致）
                self.record_url_input = ui.input(
                    '目标URL',
                    placeholder='http://10.70.70.96/Shenyuan_9#/login',
                    value=default_url
                ).classes('flex-1').style('min-height: 40px;')
                
                # 启动录制按钮（设置固定高度，与输入框一致）
                ui.button(
                    '启动录制',
                    on_click=self.start_recording,
                    icon='videocam'
                ).style('min-height: 40px; padding: 8px 16px;')
    
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
        self.status_label.classes('mb-4 status-running')
        self.start_btn.set_enabled(False)
        self.stop_btn.set_enabled(True)
        self.progress_bar.set_visibility(True)
        self.progress_bar.value = 0.1
        
        # 保存通知配置
        self.notification_config.save_config()
        
        # 构建pytest命令
        # 优先使用选中的具体测试用例，如果没有则使用模块标记
        import sys
        
        # 获取选中的测试用例
        selected_test_cases = self.module_selector.get_selected_test_cases()
        
        if selected_test_cases:
            # 如果有选中的具体用例，使用用例路径执行
            test_paths = []
            for module_key, paths in selected_test_cases.items():
                test_paths.extend(paths)
            
            if test_paths:
                # 执行选中的具体用例
                cmd_parts = ['pytest'] + test_paths + ['-v']
            elif selected_marks:
                # 如果没有具体用例但选中了模块，使用模块标记
                cmd_parts = ['pytest', '-m', selected_marks, '-v']
            else:
                cmd_parts = ['pytest', '-v']
        elif selected_marks:
            # 如果没有选中具体用例，使用模块标记
            cmd_parts = ['pytest', '-m', selected_marks, '-v']
        else:
            cmd_parts = ['pytest', '-v']
        
        if self.headless_checkbox.value:
            self._update_headless_config(True)
        
        if self.verbose_checkbox.value:
            cmd_parts.append('-s')
        
        # 生成自定义中文HTML报告
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        custom_html_report = reports_dir / f"report_{timestamp}.html"
        
        # 只生成pytest-html报告作为备用（不显示给用户）
        pytest_html_report = reports_dir / f"report_pytest_{timestamp}.html"
        
        cmd_parts.extend([
            '--tb=short',
            '--asyncio-mode=auto',
            '--html', str(pytest_html_report),
            '--self-contained-html'  # pytest-html报告（仅用于数据解析）
        ])
        
        # 保存报告路径供后续使用（使用自定义中文报告）
        self.current_report_path = custom_html_report
        self.pytest_html_report_path = pytest_html_report
        
        # 在后台线程中执行
        thread = threading.Thread(target=self._run_pytest, args=(cmd_parts,), daemon=True)
        thread.start()
        
        self.log('开始执行测试...')
        self.log(f'执行模块: {", ".join(self.module_selector.get_selected_module_names())}')
        # 显示可读的命令格式（对于包含or的表达式，用引号包裹以便阅读）
        cmd_display = ' '.join(cmd_parts)
        if ' or ' in cmd_display:
            # 在显示时用引号包裹标记表达式，便于阅读
            cmd_display = cmd_display.replace(f'-m {selected_marks}', f'-m "{selected_marks}"')
        self.log(f'执行命令: {cmd_display}')
    
    def _run_pytest(self, cmd_parts: list):
        """在后台线程中运行pytest"""
        import sys
        import locale
        start_time = datetime.now()
        
        try:
            # 检测系统编码：Windows默认使用GBK，Linux/Mac使用UTF-8
            # 获取系统默认编码
            if sys.platform == 'win32':
                # Windows: 尝试使用GBK编码，如果失败则使用系统默认编码
                try:
                    system_encoding = locale.getpreferredencoding() or 'gbk'
                except:
                    system_encoding = 'gbk'
            else:
                # Linux/Mac: 使用UTF-8
                system_encoding = 'utf-8'
            
            # subprocess.Popen使用列表格式时，会将每个元素作为单独的参数传递
            # 所以 ['pytest', '-m', 'teaching or exam', '-v'] 会正确传递
            # 'teaching or exam' 会作为一个完整的字符串参数传递给pytest
            self.current_process = subprocess.Popen(
                cmd_parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding=system_encoding,
                errors='replace',  # 如果遇到无法解码的字符，用替换字符代替，避免崩溃
                bufsize=1
            )
            
            # 实时读取输出
            for line in iter(self.current_process.stdout.readline, ''):
                if line:
                    # 确保输出是UTF-8编码的字符串（用于日志显示）
                    try:
                        # 如果line已经是字符串（text=True），直接使用
                        log_line = line.strip()
                    except UnicodeDecodeError:
                        # 如果还有编码问题，使用errors='replace'
                        log_line = line.encode(system_encoding, errors='replace').decode('utf-8', errors='replace').strip()
                    
                    self.log(log_line)
                    self.log_content.append(log_line)
                    if len(self.log_content) > self.max_log_lines:
                        self.log_content.pop(0)
            
            self.current_process.wait()
            
            # 计算执行时长
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 保存执行时长和输出用于报告生成
            self.test_duration = duration
            self.test_output = self.log_content.copy()
            
            # 生成自定义中文HTML报告
            try:
                from utils.custom_report_generator import CustomReportGenerator
                from utils.report_parser import ReportParser
                
                parser = ReportParser()
                generator = CustomReportGenerator()
                
                # 解析测试结果
                test_stats = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'skipped': 0,
                    'duration': duration,
                    'test_cases': []
                }
                
                # 从pytest输出中解析
                if self.test_output:
                    parsed = parser.parse_pytest_output(self.test_output)
                    test_stats.update(parsed)
                
                # 从pytest-html报告中解析测试用例详情
                if hasattr(self, 'pytest_html_report_path') and self.pytest_html_report_path and self.pytest_html_report_path.exists():
                    html_stats = parser.parse_html_report(self.pytest_html_report_path)
                    if html_stats:
                        test_stats.update(html_stats)
                    
                    # 解析HTML报告中的测试用例列表
                    test_cases = parser.parse_test_cases_from_html(self.pytest_html_report_path)
                    if test_cases:
                        test_stats['test_cases'] = test_cases
                
                # 生成自定义中文HTML报告
                if hasattr(self, 'current_report_path') and self.current_report_path:
                    generator.generate_html_report(
                        test_stats,
                        self.current_report_path,
                        modules=self.module_selector.get_selected_module_names()
                    )
                    self.log(f'自定义中文报告已生成: {self.current_report_path}')
            except Exception as e:
                self.log(f'生成自定义报告失败: {e}')
                import traceback
                self.log(traceback.format_exc())
            
            # 执行完成（不在后台线程中使用UI操作，避免客户端断开连接问题）
            # ui.run_javascript('window.location.reload()')  # 已移除，避免客户端断开连接警告
            
        except Exception as e:
            self.log(f'执行出错: {e}')
            self.test_duration = 0
            self.test_output = []
        finally:
            self.is_running = False
            self.status_label.text = '状态: 执行完成'
            self.status_label.classes('mb-4 status-ready')
            self.start_btn.set_enabled(True)
            self.stop_btn.set_enabled(False)
            self.progress_bar.set_visibility(False)
            
            # 发送通知（包含报告）
            self._send_notification()
    
    def stop_execution(self):
        """停止执行"""
        if self.current_process:
            self.current_process.terminate()
            self.log('测试执行已停止')
            self.is_running = False
            self.status_label.text = '状态: 已停止'
            self.status_label.classes('mb-4 status-ready')
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
            from utils.report_parser import ReportParser
            
            notification = NotificationService()
            parser = ReportParser()
            
            # 解析测试结果
            test_stats = {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'duration': getattr(self, 'test_duration', 0),
                'error_details': []
            }
            
            # 从pytest输出中解析统计信息
            if hasattr(self, 'test_output') and self.test_output:
                parsed = parser.parse_pytest_output(self.test_output)
                test_stats.update(parsed)
            
            # 如果HTML报告存在，也尝试从中解析（更准确）
            if hasattr(self, 'current_report_path') and self.current_report_path:
                html_stats = parser.parse_html_report(self.current_report_path)
                if html_stats:
                    # 优先使用HTML报告中的统计（更准确）
                    test_stats.update(html_stats)
            
            # 发送测试报告（包含HTML报告附件）
            report_path = getattr(self, 'current_report_path', None)
            notification.send_test_report(
                modules=self.module_selector.get_selected_module_names(),
                total=test_stats['total'],
                passed=test_stats['passed'],
                failed=test_stats['failed'],
                skipped=test_stats['skipped'],
                duration=test_stats['duration'],
                error_details=test_stats['error_details'],
                html_report_path=report_path
            )
            
            # 记录报告生成信息
            if report_path and report_path.exists():
                self.log(f'测试报告已生成: {report_path}')
        except Exception as e:
            self.log(f'发送通知失败: {e}')
            import traceback
            self.log(traceback.format_exc())
    
    def show_tutorial_video(self):
        """显示教程视频对话框"""
        import urllib.parse
        
        # 查找所有视频文件
        video_dir = Path('assets/videos')
        mp4_files = []
        
        if video_dir.exists():
            mp4_files = sorted(list(video_dir.glob('*.mp4')), key=lambda x: x.name)
        
        # 如果找不到视频文件，显示提示
        if not mp4_files:
            with ui.dialog() as dialog, ui.card().style('width: 500px; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(255, 100, 100, 0.5);'):
                with ui.column().classes('w-full').style('padding: 24px;'):
                    ui.label('⚠️ 未找到视频文件').classes('text-lg font-bold').style('color: #ff6b6b; margin-bottom: 16px;')
                    ui.label(f'请将视频文件（.mp4格式）放置在以下目录：').style('color: #e0e6ed; margin-bottom: 8px;')
                    ui.label(f'{video_dir.absolute()}').style('color: #4fc3f7; font-family: monospace; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px;')
                    with ui.row().classes('w-full justify-end').style('margin-top: 20px;'):
                        ui.button('关闭', on_click=dialog.close, icon='close').style('min-height: 36px; padding: 6px 20px;')
            dialog.open()
            return
        
        # 准备视频文件列表（用于下拉菜单）
        video_options = {f.name: f for f in mp4_files}
        video_names = list(video_options.keys())
        
        # 默认选择第一个视频
        current_video = mp4_files[0]
        current_video_url = f"/assets/videos/{urllib.parse.quote(current_video.name)}"
        
        with ui.dialog() as dialog, ui.card().style('width: 900px; max-width: 90vw; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5);'):
            with ui.column().classes('w-full').style('padding: 24px;'):
                ui.label('📹 录制教程视频').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 20px;')
                
                # 视频播放器容器
                video_id = 'recording-tutorial-video-dialog'
                
                # 显示当前视频文件名
                video_name_label = ui.label(f'当前播放: {current_video.name}').style('color: #90caf9; font-size: 12px; margin-bottom: 12px;')
                
                def update_video(selected_name: str):
                    """更新视频播放器"""
                    selected_file = video_options[selected_name]
                    selected_url = f"/assets/videos/{urllib.parse.quote(selected_file.name)}"
                    
                    # 更新文件名显示
                    video_name_label.text = f'当前播放: {selected_file.name}'
                    
                    # 更新视频源
                    ui.run_javascript(f'''
                        const video = document.getElementById('{video_id}');
                        if (video) {{
                            const source = video.querySelector('source');
                            if (source) {{
                                source.src = '{selected_url}';
                                video.load(); // 重新加载视频
                                video.play().catch(err => {{
                                    console.log('视频播放失败:', err);
                                }});
                            }}
                        }}
                    ''')
                
                # 视频选择下拉菜单（如果有多个视频）
                if len(mp4_files) > 1:
                    # 添加下拉菜单样式（使用更强的选择器和优先级）
                    ui.add_head_html('''
                    <style>
                        /* 视频选择下拉菜单样式 - 输入框部分 */
                        .video-select-dropdown .q-field__label {
                            color: #90caf9 !important;
                            font-weight: 500 !important;
                        }
                        .video-select-dropdown .q-field__native {
                            color: #e0e6ed !important;
                            font-size: 14px !important;
                        }
                        .video-select-dropdown .q-field__control {
                            color: #e0e6ed !important;
                            border: 1px solid rgba(0, 150, 255, 0.3) !important;
                            border-radius: 8px !important;
                            background: rgba(10, 22, 40, 0.6) !important;
                        }
                        .video-select-dropdown .q-field__control:hover {
                            border-color: rgba(0, 150, 255, 0.6) !important;
                            background: rgba(10, 22, 40, 0.8) !important;
                        }
                        .video-select-dropdown .q-field--focused .q-field__control {
                            border-color: rgba(0, 150, 255, 0.8) !important;
                            box-shadow: 0 0 0 2px rgba(0, 150, 255, 0.2) !important;
                        }
                        
                        /* 下拉菜单选项样式 - 使用通用选择器确保覆盖所有下拉菜单 */
                        .q-menu {
                            background: rgba(20, 30, 50, 0.98) !important;
                            border: 1px solid rgba(0, 150, 255, 0.4) !important;
                            border-radius: 8px !important;
                            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.7) !important;
                            backdrop-filter: blur(10px) !important;
                        }
                        .q-menu .q-list {
                            background: rgba(20, 30, 50, 0.98) !important;
                        }
                        .q-menu .q-item {
                            color: #e0e6ed !important;
                            background: rgba(20, 30, 50, 0.98) !important;
                            padding: 12px 16px !important;
                            font-size: 14px !important;
                            min-height: 44px !important;
                        }
                        .q-menu .q-item:hover {
                            background: rgba(0, 150, 255, 0.4) !important;
                            color: #ffffff !important;
                        }
                        .q-menu .q-item--active,
                        .q-menu .q-item[aria-selected="true"] {
                            background: rgba(0, 150, 255, 0.5) !important;
                            color: #ffffff !important;
                            font-weight: 500 !important;
                        }
                        .q-menu .q-item__label {
                            color: inherit !important;
                        }
                        /* 确保下拉菜单中的文字可见 */
                        .q-menu * {
                            color: #e0e6ed !important;
                        }
                        .q-menu .q-item:hover *,
                        .q-menu .q-item--active *,
                        .q-menu .q-item[aria-selected="true"] * {
                            color: #ffffff !important;
                        }
                    </style>
                    ''')
                    
                    with ui.row().classes('w-full').style('margin-bottom: 16px; align-items: center;'):
                        ui.label('选择视频：').style('color: #90caf9; margin-right: 12px; white-space: nowrap;')
                        video_select = ui.select(
                            options=video_names,
                            value=video_names[0],
                            label='视频文件',
                            on_change=lambda e: update_video(e.value)
                        ).classes('video-select-dropdown').style('flex: 1; min-width: 200px;')
                        ui.label(f'（共 {len(mp4_files)} 个视频）').style('color: #90caf9; font-size: 12px; margin-left: 12px;')
                
                # 视频播放器
                with ui.column().classes('w-full').style('background: rgba(10, 22, 40, 0.5); border-radius: 12px; padding: 16px; margin-bottom: 16px;'):
                    ui.html(f'''
                    <video id="{video_id}" 
                           style="width: 100%; max-height: 500px; border-radius: 8px;"
                           controls
                           preload="metadata">
                        <source src="{current_video_url}" type="video/mp4">
                        您的浏览器不支持视频播放。
                    </video>
                    ''', sanitize=False)
                
                # 关闭按钮
                with ui.row().classes('w-full justify-end'):
                    ui.button('关闭', on_click=dialog.close, icon='close').style('min-height: 36px; padding: 6px 20px;')
        
        dialog.open()
        
        # 对话框打开后自动播放视频
        ui.timer(0.3, lambda: ui.run_javascript(f'''
            const video = document.getElementById('{video_id}');
            if (video) {{
                video.play().catch(err => {{
                    console.log('视频播放失败:', err);
                }});
            }}
        '''), once=True)
    
    def show_code_converter(self):
        """显示代码转换对话框"""
        with ui.dialog() as dialog, ui.card().style('width: 1000px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5);'):
            with ui.column().classes('w-full').style('padding: 24px; display: flex; flex-direction: column; max-height: 90vh;'):
                ui.label('🔄 代码自动转换工具').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 16px;')
                
                ui.markdown("""
                <div style="color: #d0e4f0; font-size: 13px; margin-bottom: 16px; padding: 12px; background: rgba(0, 150, 255, 0.1); border-radius: 8px;">
                <strong style="color: #ffffff;">使用说明：</strong><br>
                1. 选择模块（授课教学/攻防演练/考试测评）<br>
                2. 输入测试用例名称（例如：navigation）<br>
                3. 粘贴你录制的代码<br>
                4. 点击"转换并保存"，完成！✅
                </div>
                """).style('margin-bottom: 16px;')
                
                # 模块选择（增强颜色和可见性）
                with ui.row().classes('w-full gap-4').style('margin-bottom: 16px;'):
                    module_select = ui.select(
                        {'teaching': '授课教学', 'exercise': '攻防演练', 'exam': '考试测评'},
                        label='选择模块',
                        value='teaching'
                    ).style('flex: 1; color: #ffffff !important;')
                    
                    # 添加CSS样式增强下拉框可见性
                    ui.add_head_html('''
                    <style>
                        .q-select .q-field__label {
                            color: #e0e6ed !important;
                            font-weight: 500 !important;
                        }
                        .q-select .q-field__native {
                            color: #ffffff !important;
                        }
                        .q-select .q-field__control {
                            color: #ffffff !important;
                        }
                        .q-menu {
                            background: rgba(20, 30, 50, 0.98) !important;
                        }
                        .q-item {
                            color: #ffffff !important;
                        }
                        .q-item:hover {
                            background: rgba(0, 150, 255, 0.3) !important;
                        }
                    </style>
                    ''')
                    
                    test_name_input = ui.input(
                        '测试用例名称',
                        placeholder='例如：navigation、course_management',
                        value='test_case'
                    ).style('flex: 1; color: #ffffff !important;')
                
                # 代码输入区域
                ui.label('粘贴录制的代码：').style('color: #e0e6ed; margin-bottom: 8px; font-size: 14px; font-weight: 500;')
                code_textarea = ui.textarea(
                    label='',
                    placeholder='在这里粘贴Playwright录制的代码...\n\n提示：直接粘贴完整代码即可，工具会自动处理',
                ).style('width: 100%; min-height: 300px; font-family: monospace; font-size: 12px;')
                
                # 转换结果区域（初始隐藏）
                result_label = ui.label('转换后的代码：').style('color: #e0e6ed; margin-top: 16px; margin-bottom: 8px; font-size: 14px;')
                result_label.set_visibility(False)
                
                result_textarea = ui.textarea(
                    label='',
                    placeholder='转换后的代码将显示在这里...'
                ).style('width: 100%; min-height: 200px; font-family: monospace; font-size: 12px;')
                result_textarea.set_visibility(False)
                
                # 按钮区域
                with ui.row().classes('w-full justify-between').style('margin-top: 16px;'):
                    ui.button('关闭', on_click=dialog.close, icon='close').style('min-height: 36px; padding: 6px 20px;')
                    
                    def convert_and_save():
                        """转换代码并保存"""
                        try:
                            original_code = code_textarea.value.strip()
                            if not original_code:
                                ui.notify('请先粘贴录制的代码！', type='warning')
                                return
                            
                            module = module_select.value
                            test_name = test_name_input.value.strip() or 'test_case'
                            # 移除可能的test_前缀
                            test_name = test_name.replace('test_', '')
                            
                            # 调用转换工具
                            from tools.convert_recording import convert_sync_to_async, generate_test_file
                            
                            # 提取核心代码（更严格的清理）
                            core_code = original_code
                            
                            # 如果包含def run函数，提取函数体
                            if 'def run(' in original_code:
                                # 找到函数定义
                                start_idx = original_code.find('def run(')
                                if start_idx != -1:
                                    # 找到函数体的开始（冒号后）
                                    brace_start = original_code.find(':', start_idx)
                                    if brace_start != -1:
                                        function_body = original_code[brace_start + 1:]
                                        lines = function_body.split('\n')
                                        non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
                                        
                                        if non_empty_lines:
                                            # 找到最小缩进
                                            min_indent = min(len(l) - len(l.lstrip()) for l in non_empty_lines)
                                            converted_lines = []
                                            
                                            for line in lines:
                                                stripped = line.strip()
                                                
                                                # 跳过空行和注释（保留有用的注释）
                                                if not stripped:
                                                    converted_lines.append('')
                                                    continue
                                                
                                                if stripped.startswith('#'):
                                                    # 跳过分隔符注释
                                                    if stripped in ['#', '# ---', '# ---------------------']:
                                                        continue
                                                    converted_lines.append(line)
                                                    continue
                                                
                                                # 删除函数定义、浏览器相关代码
                                                if any(keyword in stripped for keyword in [
                                                    'def run(', 'Playwright)', '-> None:',
                                                    'with sync_playwright()', 'run(playwright)',
                                                    'browser = playwright', 'context = browser',
                                                    'context.close()', 'browser.close()',
                                                    'import re', 'from playwright.sync_api import'
                                                ]):
                                                    continue
                                                
                                                # 处理缩进
                                                if len(line) - len(line.lstrip()) >= min_indent:
                                                    converted_lines.append(line[min_indent:])
                                                else:
                                                    converted_lines.append(line)
                                            
                                            core_code = '\n'.join(converted_lines)
                            
                            # 转换代码
                            converted_code = convert_sync_to_async(core_code)
                            
                            # 二次清理：删除所有残留的错误代码
                            cleaned_lines = []
                            for line in converted_code.split('\n'):
                                stripped = line.strip()
                                
                                # 删除残留的错误代码行
                                if any(keyword in stripped for keyword in [
                                    'Playwright)', '-> None:', 'run(playwright)',
                                    'def run(', 'with sync_playwright()',
                                    'browser =', 'context =', 'context.close()', 'browser.close()',
                                    'import re'
                                ]):
                                    continue
                                
                                # 删除只有分隔符的注释行
                                if stripped in ['#', '# ---', '# ---------------------']:
                                    continue
                                
                                cleaned_lines.append(line)
                            
                            cleaned_code = '\n'.join(cleaned_lines)
                            
                            # 添加正确的缩进（12个空格，在try块内）
                            indented_lines = []
                            for line in cleaned_code.split('\n'):
                                if line.strip():
                                    # 移除原有缩进，统一使用12个空格
                                    stripped = line.lstrip()
                                    indented_lines.append('            ' + stripped)
                                else:
                                    indented_lines.append('')
                            
                            indented_code = '\n'.join(indented_lines)
                            
                            # 生成测试文件（去掉"实习生"文案）
                            test_file_content = generate_test_file(module, test_name, indented_code, "auto")
                            
                            # 显示转换结果
                            result_textarea.value = test_file_content
                            result_label.set_visibility(True)
                            result_textarea.set_visibility(True)
                            
                            # 保存文件
                            test_dir = Path(f"test_cases/{module}")
                            test_dir.mkdir(parents=True, exist_ok=True)
                            
                            filename = f"test_{module}_{test_name}.py"
                            filepath = test_dir / filename
                            
                            filepath.write_text(test_file_content, encoding='utf-8')
                            
                            ui.notify(f'✅ 转换完成！文件已保存到: {filepath}', type='positive', timeout=5000)
                            self.log(f'代码转换成功: {filepath}')
                            
                        except Exception as e:
                            ui.notify(f'❌ 转换失败: {e}', type='negative')
                            self.log(f'代码转换失败: {e}')
                    
                    ui.button(
                        '转换并保存',
                        on_click=convert_and_save,
                        icon='save',
                        color='primary'
                    ).style('min-height: 36px; padding: 6px 20px;')
        
        dialog.open()
    
    def start_recording(self):
        """启动录制工具（自动登录版本）"""
        url = self.record_url_input.value
        if not url:
            ui.notify('请输入目标URL', type='warning')
            return
        
        try:
            import sys
            import os
            # 使用自动登录脚本启动录制
            # 这会先自动登录，然后保持浏览器打开，用户可以在其中操作并录制
            script_path = os.path.join(os.getcwd(), 'utils', 'recording_auto_login.py')
            
            if sys.platform == 'win32':
                # Windows系统：使用CREATE_NEW_CONSOLE创建新控制台窗口
                subprocess.Popen(
                    [sys.executable, script_path, url],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    cwd=os.getcwd()
                )
            else:
                # Linux/Mac系统
                subprocess.Popen(
                    [sys.executable, script_path, url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=os.getcwd()
                )
            ui.notify('✅ 录制工具已启动（已自动登录），请查看新打开的浏览器窗口', type='positive')
            ui.notify('💡 提示：浏览器已自动登录，您可以直接开始操作并录制', type='info')
        except FileNotFoundError:
            ui.notify('❌ 未找到Python或脚本文件', type='negative')
        except Exception as e:
            ui.notify(f'❌ 启动录制工具失败: {e}', type='negative')
    
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
    
    def show_test_reports(self):
        """显示测试报告列表弹窗"""
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # 获取所有HTML报告文件，按时间倒序排列
        html_reports = sorted(
            reports_dir.glob("report_*.html"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        with ui.dialog() as dialog, ui.card().style('width: 1000px; max-width: 95vw; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5);'):
            with ui.column().classes('w-full').style('padding: 24px;'):
                ui.label('📊 测试报告列表').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 20px;')
                
                if not html_reports:
                    # 没有报告时显示提示
                    with ui.column().classes('w-full items-center').style('padding: 40px;'):
                        ui.icon('description', size=64).style('color: #90caf9; opacity: 0.5; margin-bottom: 16px;')
                        ui.label('暂无测试报告').style('color: #90caf9; font-size: 16px; margin-bottom: 8px;')
                        ui.label('执行测试后会自动生成报告').style('color: #b0c4de; font-size: 12px;')
                else:
                    # 显示报告列表
                    ui.label(f'共找到 {len(html_reports)} 个测试报告（按时间倒序）').style('color: #90caf9; font-size: 12px; margin-bottom: 16px;')
                    
                    # 报告列表容器（可滚动）
                    with ui.column().classes('w-full').style('max-height: 500px; overflow-y: auto; gap: 12px;'):
                        for report_file in html_reports:
                            # 获取文件信息
                            file_stat = report_file.stat()
                            file_size = file_stat.st_size / 1024  # KB
                            file_time = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                            
                            with ui.card().classes('w-full').style('background: rgba(10, 22, 40, 0.6); border: 1px solid rgba(0, 150, 255, 0.3); padding: 16px; transition: all 0.3s;'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    with ui.column().classes('flex-1').style('min-width: 0;'):
                                        ui.label(report_file.name).style('color: #e0e6ed; font-size: 14px; font-weight: 500; margin-bottom: 4px;')
                                        with ui.row().classes('gap-4').style('font-size: 12px;'):
                                            ui.label(f'📅 {file_time}').style('color: #90caf9;')
                                            ui.label(f'📦 {file_size:.1f} KB').style('color: #90caf9;')
                                    
                                    with ui.row().classes('gap-2'):
                                        ui.button('打开', icon='open_in_new', on_click=lambda rf=report_file: self._open_report(rf)).style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
                                        ui.button('删除', icon='delete', color='red', on_click=lambda rf=report_file: self._delete_report(rf, dialog)).style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
                    
                    # 底部操作按钮
                    with ui.row().classes('w-full justify-between').style('margin-top: 20px; padding-top: 16px; border-top: 1px solid rgba(0, 150, 255, 0.2);'):
                        ui.button('打开报告目录', icon='folder_open', on_click=lambda: self._open_reports_folder()).style('min-height: 36px; padding: 6px 16px; font-size: 12px;')
                        ui.button('关闭', on_click=dialog.close, icon='close').style('min-height: 36px; padding: 6px 20px; font-size: 12px;')
        
        dialog.open()
    
    def _open_report(self, report_file: Path):
        """打开测试报告
        
        Args:
            report_file: 报告文件路径
        """
        try:
            import webbrowser
            import os
            
            if not report_file.exists():
                ui.notify(f'报告文件不存在: {report_file.name}', type='negative')
                return
            
            # 使用绝对路径打开文件
            abs_path = report_file.absolute()
            # Windows上使用file://协议
            file_url = f"file:///{abs_path.as_posix()}"
            # 使用new=2参数，避免打开多个标签
            webbrowser.open(file_url, new=2)
            ui.notify(f'正在打开报告: {report_file.name}', type='positive')
        except Exception as e:
            ui.notify(f'打开报告失败: {e}', type='negative')
    
    def _delete_report(self, report_file: Path, dialog):
        """删除测试报告
        
        Args:
            report_file: 报告文件路径
            dialog: 对话框对象（用于刷新列表）
        """
        try:
            report_file.unlink()
            ui.notify(f'已删除报告: {report_file.name}', type='positive')
            # 关闭并重新打开对话框以刷新列表
            dialog.close()
            ui.timer(0.3, lambda: self.show_test_reports(), once=True)
        except Exception as e:
            ui.notify(f'删除报告失败: {e}', type='negative')
    
    def _open_reports_folder(self):
        """打开报告目录"""
        try:
            import os
            import platform
            
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            abs_path = reports_dir.absolute()
            
            # 根据操作系统打开文件夹
            if platform.system() == 'Windows':
                os.startfile(str(abs_path))
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{abs_path}"')
            else:  # Linux
                os.system(f'xdg-open "{abs_path}"')
            
            ui.notify('已打开报告目录', type='positive')
        except Exception as e:
            ui.notify(f'打开目录失败: {e}', type='negative')


# 如果直接运行此文件，也支持
if __name__ in {"__main__", "__mp_main__"}:
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
        title = web_config.get('title', 'WebUI自动化测试控制台')
    else:
        host = '0.0.0.0'
        port = 8080
        title = 'WebUI自动化测试控制台'
    
    ui.run(host=host, port=port, title=title)


