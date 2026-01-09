"""
NiceGUI Web控制界面主入口

@File  : main.py
@Author: shenyuan
"""
import asyncio
import subprocess
import threading
import os
import re
from datetime import datetime
from pathlib import Path
from nicegui import ui, app
from web_ui.components.module_selector import ModuleSelector
from web_ui.components.notification_config import NotificationConfig
from web_ui.components.login_config import LoginConfig
from web_ui.components.advanced_features import AdvancedFeaturesPanel
from core.notification import NotificationService
import yaml


class WebUIController:
    """WebUI控制器"""
    
    def __init__(self):
        """初始化控制器"""
        self.module_selector = ModuleSelector()
        self.notification_config = NotificationConfig()
        self.login_config = LoginConfig()
        self.advanced_features = AdvancedFeaturesPanel()
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
            /* 确保页面背景始终是深色渐变，不受弹窗影响 */
            html, body {
                background: linear-gradient(135deg, #0a1628 0%, #1a2332 50%, #0f1b2e 100%) !important;
                background-attachment: fixed !important;
            }
            body {
                color: #e0e6ed;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
            }
            
            /* 响应式布局 - 移动端适配 */
            @media (max-width: 768px) {
                .q-card {
                    border-radius: 16px !important;
                    margin-bottom: 16px !important;
                }
                .card-content {
                    padding: 16px !important;
                }
                .section-title {
                    font-size: 1rem !important;
                    margin-bottom: 16px !important;
                }
                .q-btn {
                    min-height: 44px !important;
                    font-size: 14px !important;
                    padding: 10px 16px !important;
                }
                .q-input, .q-textarea {
                    min-height: 44px !important;
                    font-size: 16px !important;
                }
                /* 移动端单列布局 */
                .mobile-layout {
                    flex-direction: column !important;
                }
                /* 移动端按钮全宽 */
                .mobile-full-width {
                    width: 100% !important;
                }
            }
            
            /* 响应式布局 - 移动端自动适配 */
            @media (max-width: 768px) {
                /* 移动端单列布局 */
                .mobile-layout {
                    flex-direction: column !important;
                }
                /* 移动端全宽 */
                .mobile-layout > .flex-1 {
                    flex: 1 1 100% !important;
                    min-width: 100% !important;
                }
                /* 移动端按钮全宽 */
                .mobile-full-width {
                    width: 100% !important;
                }
                /* 移动端字体调整 */
                .title-text {
                    font-size: 1.5rem !important;
                }
                /* 移动端卡片内边距 */
                .card-content {
                    padding: 16px !important;
                }
            }
            
            /* 确保移动端viewport正确 */
            @media (max-width: 768px) {
                html, body {
                    overflow-x: hidden;
                }
            }
            
            /* 优化弹窗滚动条样式，确保文案不被遮挡 */
            .q-dialog .q-card {
                border-radius: 16px !important;
                box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6) !important;
                overflow: hidden !important;
            }
            
            /* 确保弹窗阴影也是圆润的 */
            .q-dialog {
                border-radius: 16px !important;
            }
            
            .q-dialog__inner {
                border-radius: 16px !important;
            }
            
            /* 确保弹窗遮罩层（overlay）保持默认样式，不影响页面背景 */
            .q-overlay,
            .q-dialog__backdrop {
                background: rgba(0, 0, 0, 0.4) !important;
            }
            
            /* 确保弹窗打开时，body 和 html 背景色不变，无论Quasar添加什么类 */
            body.q-body--dialog,
            body.q-body--dialog--active,
            html.q-body--dialog,
            html.q-body--dialog--active,
            body[class*="dialog"],
            html[class*="dialog"] {
                background: linear-gradient(135deg, #0a1628 0%, #1a2332 50%, #0f1b2e 100%) !important;
                background-attachment: fixed !important;
            }
            
            /* 确保页面容器背景也不变 */
            .q-page-container,
            .q-page {
                background: transparent !important;
            }
            
            /* 移除弹窗内卡片元素的阴影，避免长方形阴影 */
            .q-dialog .q-card .q-card {
                box-shadow: none !important;
                border-radius: 8px !important;
            }
            
            /* 确保弹窗中所有label都能正确换行，不会超出容器 */
            .q-dialog .q-card .q-label,
            .q-dialog .q-card label {
                word-break: break-word !important;
                overflow-wrap: break-word !important;
                white-space: normal !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
                display: block !important;
                overflow: hidden !important;
            }
            
            /* 确保弹窗中的column容器不会导致内容溢出 */
            .q-dialog .q-card .q-column {
                min-width: 0 !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
            }
            
            /* 弹窗内容区域滚动优化 */
            .q-dialog .q-card > div {
                scrollbar-width: thin;
                scrollbar-color: rgba(0, 150, 255, 0.6) rgba(10, 22, 40, 0.5);
            }
            
            .q-dialog .q-card > div::-webkit-scrollbar {
                width: 8px;
            }
            
            .q-dialog .q-card > div::-webkit-scrollbar-track {
                background: rgba(10, 22, 40, 0.5);
                border-radius: 4px;
            }
            
            .q-dialog .q-card > div::-webkit-scrollbar-thumb {
                background: rgba(0, 150, 255, 0.6);
                border-radius: 4px;
            }
            
            .q-dialog .q-card > div::-webkit-scrollbar-thumb:hover {
                background: rgba(0, 150, 255, 0.8);
            }
            
            /* 确保弹窗内的文本不会被截断 */
            .q-dialog .q-card label,
            .q-dialog .q-card .q-label {
                word-wrap: break-word;
                word-break: break-word;
                overflow-wrap: break-word;
                white-space: normal !important;
            }
            
            /* 弹窗内长文本自动换行 */
            .q-dialog .q-card {
                overflow: visible !important;
                box-sizing: border-box !important;
            }
            
            .q-dialog .q-card > div {
                overflow-y: auto !important;
                overflow-x: hidden !important;
                box-sizing: border-box !important;
            }
            
            /* 确保弹窗内所有元素不超出边界 */
            .q-dialog .q-card * {
                box-sizing: border-box;
                max-width: 100%;
            }
            
            /* 确保grid布局响应式 */
            .q-dialog .q-grid {
                width: 100% !important;
                max-width: 100% !important;
            }
            
            .q-dialog .q-grid > * {
                min-width: 0 !important;
                max-width: 100% !important;
            }
            
            /* 确保弹窗内所有文本和输入框都在框内 */
            .q-dialog .q-card .q-input,
            .q-dialog .q-card .q-textarea,
            .q-dialog .q-card input,
            .q-dialog .q-card textarea {
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
            }
            
            /* 确保标签和文本不超出 */
            .q-dialog .q-card .q-label,
            .q-dialog .q-card label {
                max-width: 100% !important;
                word-wrap: break-word !important;
                overflow-wrap: break-word !important;
                word-break: break-word !important;
                white-space: normal !important;
                display: block !important;
            }
            
            /* 确保所有容器都有正确的padding，内容不贴边 */
            .q-dialog .q-card > div {
                padding-left: 24px !important;
                padding-right: 24px !important;
            }
            
            /* 确保输入框和表单元素有合适的宽度 */
            .q-dialog .q-card .q-input__wrapper,
            .q-dialog .q-card .q-field__control {
                width: 100% !important;
                max-width: 100% !important;
            }
            
            /* 确保所有文本容器都有合适的边距 */
            .q-dialog .q-card .q-label,
            .q-dialog .q-card label {
                margin-left: 0 !important;
                margin-right: 0 !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
            }
            
            /* 确保卡片内容不超出 */
            .q-dialog .q-card .q-card {
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
            }
            
            /* 确保输入框的label和placeholder完整显示 */
            .q-dialog .q-card .q-field__label,
            .q-dialog .q-card .q-input__label {
                max-width: 100% !important;
                word-break: break-word !important;
                overflow-wrap: break-word !important;
                white-space: normal !important;
                display: block !important;
            }
            
            .q-dialog .q-card .q-field__control,
            .q-dialog .q-card .q-input__control {
                width: 100% !important;
                max-width: 100% !important;
            }
            
            .q-dialog .q-card .q-field__native,
            .q-dialog .q-card .q-input__native {
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
            }
            
            /* 确保输入框的placeholder完整显示 */
            .q-dialog .q-card .q-field__native::placeholder,
            .q-dialog .q-card .q-input__native::placeholder {
                white-space: normal !important;
                word-break: break-word !important;
                overflow-wrap: break-word !important;
            }
            
            /* 确保按钮和操作元素不超出 */
            .q-dialog .q-card .q-btn {
                max-width: 100% !important;
                box-sizing: border-box !important;
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
                    
                    # 高级功能（放在通知配置上面）
                    self.advanced_features.render()
                    
                    # 通知配置
                    self.notification_config.render()
                
                # 右侧：执行控制区域（60%宽度，移动端100%）
                with ui.column().classes('flex-1 desktop-view').style('display: flex; flex-direction: column; gap: 24px; min-width: 0; flex: 0 0 60%; overflow: visible;'):
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
                        self.video_recording_checkbox = ui.checkbox('视频录制', value=False).style('font-size: 12px; flex-shrink: 0;')
                        
                        # 测试报告按钮（放在执行选项同一行）
                        ui.button(
                            '📊 测试报告',
                            on_click=self.show_test_reports,
                            icon='assessment'
                        ).style('min-height: 30px; padding: 4px 12px; font-size: 12px; background: rgba(0, 150, 255, 0.15); border: 1px solid rgba(0, 150, 255, 0.3);')
                        
                        # 初始化重试次数和超时时间的默认值（从高级功能中获取）
                        self.retry_count_input = None
                        self.timeout_input = None
                        self.retry_count = 2  # 默认值
                        self.timeout_seconds = 30  # 默认值
    
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
                <li style="margin-bottom: 8px;">复制生成的代码，点击"代码转换"按钮，选择模块并转换代码，确认后保存</li>
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
        
        # 视频录制控制（通过环境变量传递）
        if self.video_recording_checkbox.value:
            os.environ['ENABLE_VIDEO_RECORDING'] = '1'
        else:
            os.environ['ENABLE_VIDEO_RECORDING'] = '0'
        
        # 分布式/并行执行支持（如果启用）
        # 可以通过环境变量或配置启用
        parallel_workers = os.environ.get('PYTEST_WORKERS', '1')
        if parallel_workers != '1':
            cmd_parts.extend(['-n', str(parallel_workers)])
        
        # 生成自定义中文HTML报告
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 使用中文文件名
        custom_html_report = reports_dir / f"WebUI自动化测试报告_{timestamp}.html"
        
        # 只生成pytest-html报告作为备用（不显示给用户）
        # 使用中文文件名（pytest-html已修复编码问题）
        pytest_html_report = reports_dir / f"pytest自动化测试报告_{timestamp}.html"
        
        # 获取重试次数和超时时间（从高级功能面板获取）
        retry_count = self.advanced_features.get_retry_count()
        timeout_seconds = self.advanced_features.get_timeout_seconds()
        
        cmd_parts.extend([
            '--tb=long',  # 使用long格式显示更详细的错误信息
            '--asyncio-mode=auto',
            '--html', str(pytest_html_report),
            '--self-contained-html',  # pytest-html报告（仅用于数据解析）
            '--capture=sys',  # 捕获sys.stdout和sys.stderr，让pytest-html能捕获日志
            '--log-cli-level=INFO',  # 显示INFO级别的日志
            '--log-cli-format=%(message)s',  # 简化的日志格式，避免解析错误
            '--reruns', str(retry_count),  # 重试次数
            '--reruns-delay', '1'  # 重试延迟（秒）
        ])
        
        # 设置超时时间（通过环境变量传递给测试用例）
        os.environ['PYTEST_TIMEOUT'] = str(timeout_seconds)
        
        # 保存报告路径供后续使用（使用自定义中文报告）
        self.current_report_path = custom_html_report
        self.pytest_html_report_path = pytest_html_report
        
        # 先输出日志信息（在启动线程之前）
        self.log('开始执行测试...')
        self.log(f'执行模块: {", ".join(self.module_selector.get_selected_module_names())}')
        self.log(f'重试次数: {retry_count}, 超时时间: {timeout_seconds}秒')
        # 显示可读的命令格式（对于包含or的表达式，用引号包裹以便阅读）
        cmd_display = ' '.join(cmd_parts)
        if ' or ' in cmd_display:
            # 在显示时用引号包裹标记表达式，便于阅读
            cmd_display = cmd_display.replace(f'-m {selected_marks}', f'-m "{selected_marks}"')
        self.log(f'执行命令: {cmd_display}')
        
        # 在后台线程中执行
        thread = threading.Thread(target=self._run_pytest, args=(cmd_parts,), daemon=True)
        thread.start()
    
    def _run_pytest(self, cmd_parts: list):
        """在后台线程中运行pytest"""
        import sys
        import locale
        start_time = datetime.now()
        
        # 在后台线程开始时输出日志
        self.log('pytest进程已启动，正在执行测试...')
        
        try:
            # 统一使用UTF-8编码，确保中文和特殊字符正确显示
            # 设置环境变量确保子进程使用UTF-8编码
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            self.current_process = subprocess.Popen(
                cmd_parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',  # 使用UTF-8编码，确保中文正确显示
                errors='replace',  # 如果遇到无法解码的字符，用替换字符代替，避免崩溃
                bufsize=1,
                env=env  # 传递环境变量
            )
            
            # 实时读取输出
            for line in iter(self.current_process.stdout.readline, ''):
                if line:
                    # subprocess已经使用UTF-8编码读取，直接使用
                    try:
                        log_line = line.strip()
                        # 处理Unicode转义字符（如 \u2713 应该显示为 ✓，\u540d\u79f0 应该显示为 名称）
                        if '\\u' in log_line:
                            try:
                                # 方法1: 先编码为bytes，再解码为unicode_escape
                                # 注意：unicode_escape需要从latin-1编码的bytes解码
                                log_line = log_line.encode('latin-1', errors='ignore').decode('unicode_escape')
                            except:
                                try:
                                    # 方法2: 如果方法1失败，尝试从utf-8编码的bytes解码
                                    log_line = log_line.encode('utf-8').decode('unicode_escape')
                                except:
                                    pass  # 如果解码失败，保持原样
                    except (UnicodeDecodeError, UnicodeError):
                        # 如果还有编码问题，使用errors='replace'
                        log_line = line.encode('utf-8', errors='replace').decode('utf-8', errors='replace').strip()
                    
                    # 只调用log()方法，它会自动添加到log_content中，避免重复
                    # 注意：log()方法会自动添加时间戳，所以直接传入log_line即可
                    if log_line:  # 只记录非空行
                        # 检查是否已经包含时间戳格式 [HH:MM:SS]，如果包含说明是pytest的输出，已经格式化过了
                        # 这种情况下，pytest的输出会被logger捕获并输出，我们不应该再重复添加
                        # 但是我们需要记录到log_content中以便导出
                        if re.match(r'^\[\d{2}:\d{2}:\d{2}\]', log_line):
                            # 已经包含时间戳，说明是pytest的输出，直接添加到log_content，不调用log()避免重复
                            if log_line not in self.log_content:
                                self.log_content.append(log_line)
                                # 不推送到UI，因为pytest的输出已经通过logger输出了
                        else:
                            # 没有时间戳，调用log()方法添加（这会添加时间戳并推送到UI）
                            self.log(log_line)
                        
                        # 限制日志行数
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
                
                    # 优先从pytest输出中解析测试用例（不依赖HTML报告）
                    # 这样可以避免HTML解析失败的问题
                    test_cases_from_output = []
                    if self.test_output:
                        output_text = '\n'.join(self.test_output)
                        # 直接从pytest输出中解析测试用例
                        lines = output_text.split('\n')
                        test_name_to_info = {}  # {test_name: {'status': 'passed', 'duration': 28.64}}
                        
                        # 匹配测试用例名称（完整路径，包含test_cases/前缀）
                        # 格式：test_cases/teaching/test_teaching_first.py::TestTeachingNavigation::test_teaching_module_navigation
                        # 注意：只匹配完整的测试名称行，避免匹配到日志中的其他内容
                        # 支持两种格式：
                        # 1. 完整路径：test_cases/teaching/test_teaching_first.py::TestTeachingNavigation::test_teaching_module_navigation
                        # 2. 收集阶段：test_cases/teaching/test_teaching_first.py::TestTeachingNavigation::test_teaching_module_navigation（在collecting阶段）
                        test_name_pattern = r'^test_cases/[^:\s]+\.py::[^:\s]+::[^:\s]+(?:\[[^\]]+\])?$'
                        # 也匹配collecting阶段的测试用例（不带test_cases/前缀的）
                        test_name_pattern_collecting = r'^\s*test_cases/[^:\s]+\.py::[^:\s]+::[^:\s]+(?:\[[^\]]+\])?$'
                        # 匹配状态行：PASSED [ 33%] 或 FAILED [ 33%]
                        status_pattern = r'^\s*(PASSED|FAILED|SKIPPED|ERROR|RERUN)\s*\['
                        
                        # 从日志看，pytest输出格式是：
                        # test_cases/teaching/test_teaching_first.py::TestTeachingNavigation::test_teaching_module_navigation
                        # PASSED                                                                   [ 33%]
                        # 时长信息在HTML报告的Duration列中，不在pytest输出中，需要从HTML报告解析时长
                        # 但我们可以先解析测试名称和状态
                        
                        for i, line in enumerate(lines):
                            # 查找测试名称行（完整路径，必须是整行匹配）
                            line_stripped = line.strip()
                            test_name_match = re.match(test_name_pattern, line_stripped)
                            # 如果整行匹配失败，尝试匹配行中的测试名称（可能在行首有空格或其他字符）
                            if not test_name_match:
                                # 使用更精确的正则表达式，避免匹配到带尾随字符的测试名称
                                # 匹配格式：test_cases/xxx.py::Class::method，确保后面跟着空格、换行或行尾
                                # 使用负向前瞻，确保后面不是字母、数字、下划线、单引号、方括号等
                                test_name_match = re.search(r'(test_cases/[^:\s]+\.py::[^:\s]+::[^:\s]+(?:\[[^\]]+\])?)(?![^\s\n\]\',])', line)
                            
                            if test_name_match:
                                # 提取测试名称
                                if isinstance(test_name_match, re.Match):
                                    test_name = test_name_match.group(1) if test_name_match.lastindex else test_name_match.group(0)
                                else:
                                    test_name = test_name_match.group(1) if test_name_match.lastindex else test_name_match.group(0)
                                test_name = test_name.strip()
                                
                                # 立即清理测试名称（去除HTML标签和尾随字符），用于去重判断
                                # 先去除所有尾随的特殊字符（包括']', ',', 单引号等）
                                clean_name_for_key = re.sub(r'<[^>]+>', '', test_name).strip()
                                # 去除尾部的所有非字母数字字符（但保留路径中的斜杠和冒号）
                                clean_name_for_key = re.sub(r'[^\w\s/:\.\-\[\]]+$', '', clean_name_for_key).strip()
                                # 再次清理尾部的特殊字符组合（包括']', ',', 单引号等）
                                clean_name_for_key = re.sub(r'[\]\',]+$', '', clean_name_for_key).strip()
                                clean_name_for_key = re.sub(r'[,</>\']+$', '', clean_name_for_key).strip()
                                clean_name_for_key = re.sub(r"[,']+$", '', clean_name_for_key).strip()
                                
                                # 如果清理后的名称为空，跳过
                                if not clean_name_for_key:
                                    continue
                                
                                # 在后续行中查找状态（最多查找10行，因为可能有重试）
                                status = 'passed'  # 默认状态
                                for j in range(i+1, min(i+11, len(lines))):
                                    next_line = lines[j]
                                    # 查找状态（支持多种格式）
                                    status_match = re.search(status_pattern, next_line)
                                    if status_match:
                                        status = status_match.group(1).lower()
                                        break
                                    # 也检查FAILED/PASSED行（在short test summary info部分）
                                    if re.search(r'^\s*(FAILED|PASSED|SKIPPED|ERROR)\s+', next_line):
                                        status_match = re.search(r'^\s*(FAILED|PASSED|SKIPPED|ERROR)\s+', next_line)
                                        if status_match:
                                            status = status_match.group(1).lower()
                                            break
                                
                                # 在存储之前就进行去重检查（使用清理后的名称）
                                # 如果已经存在相同的清理后的名称，跳过（除非是失败状态需要更新）
                                if clean_name_for_key in test_name_to_info:
                                    # 如果当前状态是passed，且已存在，跳过（避免重复）
                                    if status == 'passed':
                                        continue
                                    # 如果当前状态是failed或error，更新状态
                                    elif status in ['failed', 'error']:
                                        test_name_to_info[clean_name_for_key]['status'] = status
                                        self.log(f'更新测试用例状态: {clean_name_for_key}, 新状态: {status}')
                                        continue
                                    else:
                                        # 其他状态（如rerun），也跳过（避免重复）
                                        continue
                                
                                # 使用清理后的名称作为key进行去重判断
                                # 保存测试用例信息（时长稍后从HTML报告补充，或使用默认值0）
                                # 只保存第一次出现的测试用例，避免重复（除非是失败状态）
                                test_name_to_info[clean_name_for_key] = {
                                    'status': status,
                                    'duration': 0.0,  # 默认时长，稍后从HTML报告补充
                                    'name': clean_name_for_key  # 使用清理后的名称
                                }
                                self.log(f'解析到测试用例: {clean_name_for_key}, 状态: {status}')
                        
                        # 转换为测试用例列表，去重并保留失败和重试的分别条目
                        if test_name_to_info:
                            # 清理测试名称，去重，但保留失败和重试的分别条目
                            cleaned_test_cases = []
                            seen_names = set()  # 用于去重
                            for test_name, test_info in test_name_to_info.items():
                                # 清理测试名称（去除HTML标签和尾随字符）
                                clean_name = re.sub(r'<[^>]+>', '', test_name).strip()
                                # 只去除尾部的特殊字符，不要去除路径中的斜杠
                                clean_name = re.sub(r'[,</>\']+$', '', clean_name).strip()
                                # 去除尾部的逗号和单引号（但保留路径中的斜杠）
                                clean_name = re.sub(r"[,']+$", '', clean_name).strip()
                                
                                if not clean_name:
                                    continue
                                
                                # 提取基础名称（用于去重判断）
                                # 例如：test_cases/teaching/test_teaching_first.py::TestTeachingNavigation::test_teaching_module_navigation
                                # 基础名称就是完整路径，用于判断是否是同一个测试用例
                                base_name = clean_name
                                
                                # 如果已经见过这个测试用例，跳过（去重）
                                if base_name in seen_names:
                                    continue
                                
                                seen_names.add(base_name)
                                cleaned_test_cases.append({
                                    'name': clean_name,
                                    'status': test_info.get('status', 'passed'),
                                    'duration': test_info.get('duration', 0.0)
                                })
                            
                            test_cases_from_output = cleaned_test_cases
                            self.log(f'从pytest输出直接解析到 {len(test_cases_from_output)} 个测试用例（去重后，保留失败和重试分别条目，不依赖HTML报告）')
                            
                            # 尝试从HTML报告补充时长信息（如果HTML报告存在）
                            # 即使Test列为空，我们也可以从Duration列和Result列推断
                            if hasattr(self, 'pytest_html_report_path') and self.pytest_html_report_path and self.pytest_html_report_path.exists():
                                try:
                                    # 直接从HTML文件中解析Duration列，不依赖Test列
                                    from bs4 import BeautifulSoup
                                    with open(self.pytest_html_report_path, 'r', encoding='utf-8', errors='replace') as f:
                                        html_content = f.read()
                                    soup = BeautifulSoup(html_content, 'html.parser')
                                    table = soup.find('table', {'id': 'results-table'}) or soup.find('table', class_='results')
                                    if table:
                                        # 查找所有tbody（可能有多个，每个测试用例一个）
                                        all_tbodies = table.find_all('tbody')
                                        self.log(f'找到 {len(all_tbodies)} 个tbody')
                                        
                                        # 按顺序匹配Duration列和Result列（区分失败和重试）
                                        # 只解析真正的测试行，跳过extra详情行
                                        test_rows_info = []  # 存储每行的信息：{'duration': float, 'result': str, 'test_name': str}
                                        row_count = 0
                                        for tbody_idx, tbody in enumerate(all_tbodies):
                                            rows = tbody.find_all('tr')
                                            self.log(f'tbody {tbody_idx+1} 有 {len(rows)} 行')
                                            for idx, row in enumerate(rows):
                                                row_count += 1
                                                # 检查是否是extra行（详情行）
                                                row_class = row.get('class', [])
                                                if isinstance(row_class, list) and 'extra' in row_class:
                                                    self.log(f'跳过extra行 tbody{tbody_idx+1}-row{idx+1}')
                                                    continue  # 跳过详情行
                                                
                                                cells = row.find_all('td')
                                                if len(cells) > 2:
                                                    # 检查第一个cell是否是Result列（col-result类）
                                                    first_cell = cells[0]
                                                    first_cell_class = first_cell.get('class', [])
                                                    if isinstance(first_cell_class, list) and 'col-result' not in first_cell_class:
                                                        self.log(f'跳过非测试行 tbody{tbody_idx+1}-row{idx+1}，第一个cell类: {first_cell_class}')
                                                        continue  # 跳过非测试行
                                                    
                                                    # 解析Result列（第一个cell）
                                                    result_text = first_cell.get_text(strip=True).lower()
                                                    result_status = 'passed'  # 默认
                                                    if 'failed' in result_text:
                                                        result_status = 'failed'
                                                    elif 'rerun' in result_text:
                                                        result_status = 'rerun'
                                                    elif 'passed' in result_text:
                                                        result_status = 'passed'
                                                    elif 'skipped' in result_text:
                                                        result_status = 'skipped'
                                                    
                                                    # 解析Test列（第二个cell，索引1）
                                                    test_cell = cells[1] if len(cells) > 1 else None
                                                    test_name = ''
                                                    if test_cell:
                                                        test_name = test_cell.get_text(strip=True)
                                                    
                                                    # 解析Duration列（第三个cell，索引2）
                                                    duration_cell = cells[2]  # Duration列
                                                    duration_text = duration_cell.get_text(strip=True)
                                                    duration = 0.0
                                                    # 解析时长 "28.64s" -> 28.64
                                                    if 's' in duration_text.lower():
                                                        try:
                                                            duration = float(re.sub(r'[^\d.]', '', duration_text))
                                                            self.log(f'解析到Duration tbody{tbody_idx+1}-row{idx+1}: {duration}s, Result: {result_status}, Test: {test_name[:50]}...')
                                                        except Exception as e:
                                                            self.log(f'解析Duration失败 tbody{tbody_idx+1}-row{idx+1}: {e}')
                                                            duration = 0.0
                                                    
                                                    test_rows_info.append({
                                                        'duration': duration,
                                                        'result': result_status,
                                                        'test_name': test_name
                                                    })
                                        
                                        self.log(f'最终解析到 {len(test_rows_info)} 个测试行（总行数: {row_count}）')
                                        
                                        # 按顺序更新测试用例的时长和状态（不累加，分别保留失败和重试）
                                        # 重要：HTML报告中的每个条目（rerun、passed、failed）都应该在自定义报告中显示
                                        if len(test_rows_info) > 0:
                                            # 为HTML报告中的每个条目创建测试用例，确保数量一致
                                            new_test_cases = []
                                            for row_info in test_rows_info:
                                                row_test_name = row_info.get('test_name', '').strip()
                                                # 清理测试名称（去除中文信息，只保留原始路径）
                                                clean_row_name = re.sub(r'<[^>]+>', '', row_test_name).strip()
                                                # 去除中文信息部分（[模块:xxx] [类:xxx]）
                                                clean_row_name = re.sub(r'\s*\[模块:[^\]]+\]\s*', '', clean_row_name)
                                                clean_row_name = re.sub(r'\s*\[类:[^\]]+\]\s*', '', clean_row_name)
                                                clean_row_name = re.sub(r"[,']+$", '', clean_row_name).strip()
                                                
                                                # 如果清理后的名称为空，尝试从原始名称提取
                                                if not clean_row_name:
                                                    clean_row_name = row_test_name.strip()
                                                
                                                # 查找是否已存在匹配的测试用例（用于获取基础名称）
                                                base_name = clean_row_name
                                                for case in test_cases_from_output:
                                                    case_name = case.get('name', '')
                                                    # 清理case_name（去除中文信息）
                                                    clean_case_name = re.sub(r'\s*\[模块:[^\]]+\]\s*', '', case_name)
                                                    clean_case_name = re.sub(r'\s*\[类:[^\]]+\]\s*', '', clean_case_name)
                                                    clean_case_name = clean_case_name.strip()
                                                    
                                                    # 如果匹配，使用case_name作为基础名称
                                                    if clean_case_name and clean_row_name and (clean_case_name in clean_row_name or clean_row_name in clean_case_name):
                                                        base_name = case_name.split(' [模块:')[0].split(' [类:')[0].strip()
                                                        break
                                                
                                                # 创建新条目，使用基础名称和HTML报告中的状态、时长
                                                new_case = {
                                                    'name': base_name,
                                                    'status': row_info['result'],
                                                    'duration': row_info['duration']
                                                }
                                                new_test_cases.append(new_case)
                                            
                                            # 替换原有的测试用例列表，确保与HTML报告中的条目数量一致
                                            if new_test_cases:
                                                test_cases_from_output = new_test_cases
                                                self.log(f'从HTML报告创建了 {len(new_test_cases)} 个测试用例条目（与pytest-html报告保持一致，包括rerun、passed、failed等所有状态）')
                                        else:
                                            self.log(f'警告: 未解析到任何测试行信息')
                                except Exception as e:
                                    self.log(f'从HTML报告补充时长信息失败: {e}')
                                    import traceback
                                    self.log(traceback.format_exc())
                            
                            test_stats['test_cases'] = test_cases_from_output
                        
                        # 如果从输出中解析失败，尝试从HTML报告解析（备用方案）
                        if not test_cases_from_output and hasattr(self, 'pytest_html_report_path') and self.pytest_html_report_path and self.pytest_html_report_path.exists():
                            html_stats = parser.parse_html_report(self.pytest_html_report_path)
                            if html_stats:
                                test_stats.update(html_stats)
                            
                            test_cases = parser.parse_test_cases_from_html(self.pytest_html_report_path)
                            if test_cases:
                                test_stats['test_cases'] = test_cases
                                self.log(f'从HTML报告解析到 {len(test_cases)} 个测试用例（备用方案）')
                        elif not test_cases_from_output:
                            self.log(f'警告: 未能从pytest输出中解析到测试用例详情')
                    
                    # 如果HTML解析结果不足或为空，尝试从pytest输出补充
                    # 注意：即使HTML解析到了测试用例，如果数量不足，也需要从pytest输出补充
                    html_test_count = len(test_stats.get('test_cases', []))
                    total_test_count = test_stats.get('total', 0)
                    self.log(f'准备生成报告：HTML解析到 {html_test_count} 个测试用例，总数: {total_test_count}')
                    if html_test_count < total_test_count or html_test_count == 0:
                        if self.test_output:
                            output_text = '\n'.join(self.test_output)
                            # 匹配测试用例名称（例如：test_teaching_first.py::TestTeachingNavigation::test_teaching_module_navigation PASSED）
                            # re模块已在文件顶部导入，不需要重复导入
                            # 更精确的匹配模式：匹配完整的测试路径和状态
                            # 支持多种格式：test_file.py::Class::method PASSED 或 test_file.py::Class::method [PASSED]
                            # 匹配测试用例：test_file.py::Class::method PASSED 格式
                            # 注意：pytest输出中，PASSED/FAILED等可能在同一行或下一行
                            # 改进：匹配所有测试用例，包括带参数化的（如 test_name[param]）
                            test_pattern = r'(test_\S+\.py::\S+::\S+(?:\[[^\]]+\])?)\s+\[?(PASSED|FAILED|SKIPPED|ERROR|RERUN)\]?'
                            matches = re.findall(test_pattern, output_text)
                            self.log(f'第一次匹配（同行模式）找到 {len(matches)} 个测试用例')
                            
                            # 如果没找到或数量不足，尝试匹配更宽松的模式（测试名称和状态可能在不同行）
                            # 从日志看，pytest输出格式是：
                            # test_cases/teaching/test_teaching_first.py::TestTeachingNavigation::test_teaching_module_navigation
                            # PASSED                                                                   [ 33%]
                            # 所以需要按行匹配，并且需要匹配完整路径（包含test_cases/）
                            if not matches or len(matches) < total_test_count:
                                lines = output_text.split('\n')
                                test_name_to_status = {}
                                test_name_to_duration = {}  # 存储每个测试用例的时长
                                # 改进：匹配完整路径，包括test_cases/前缀
                                test_name_pattern = r'(test_cases/[^:\s]+\.py::[^:\s]+::[^:\s]+(?:\[[^\]]+\])?)'
                                # 也匹配不带test_cases/前缀的（备用）
                                test_name_pattern_alt = r'(test_[^:\s]+\.py::[^:\s]+::[^:\s]+(?:\[[^\]]+\])?)'
                                status_pattern = r'^\s*(PASSED|FAILED|SKIPPED|ERROR|RERUN)\s*'
                                # 匹配时长：如 "28.64s" 或 "28.64 s"
                                duration_pattern = r'(\d+\.?\d*)\s*s\s*'
                                
                                for i, line in enumerate(lines):
                                    # 查找测试名称行（优先匹配完整路径）
                                    test_name_match = re.search(test_name_pattern, line)
                                    if not test_name_match:
                                        test_name_match = re.search(test_name_pattern_alt, line)
                                    
                                    if test_name_match:
                                        test_name = test_name_match.group(1)
                                        # 在后续行中查找状态和时长（最多查找5行）
                                        for j in range(i+1, min(i+6, len(lines))):
                                            status_match = re.search(status_pattern, lines[j])
                                            if status_match:
                                                status = status_match.group(1)
                                                # 跳过RERUN状态，只保留最终状态（FAILED > PASSED）
                                                if status != 'RERUN' or test_name not in test_name_to_status:
                                                    # 如果已有状态，优先保留FAILED/ERROR
                                                    if test_name not in test_name_to_status or \
                                                       (status in ['FAILED', 'ERROR'] and test_name_to_status[test_name] not in ['FAILED', 'ERROR']):
                                                        test_name_to_status[test_name] = status
                                                
                                                # 尝试从同一行或下一行提取时长
                                                duration_match = re.search(duration_pattern, lines[j])
                                                if duration_match:
                                                    test_name_to_duration[test_name] = float(duration_match.group(1))
                                                break
                                
                                if test_name_to_status:
                                    matches = [(name, status) for name, status in test_name_to_status.items()]
                                    self.log(f'从pytest输出解析到 {len(matches)} 个测试用例（按行匹配）')
                            
                            if matches:
                                fallback_cases = []
                                for test_name, status in matches:
                                    # 提取执行时长（优先使用从输出中解析到的时长，否则平均分配）
                                    duration = test_name_to_duration.get(test_name, 0.0)
                                    if duration == 0.0:
                                        # 尝试从总结行提取总时长，然后平均分配
                                        summary_match = re.search(r'(\d+)\s+(?:passed|failed|skipped|error).*?in\s+([\d.]+)s', output_text, re.IGNORECASE)
                                        if summary_match:
                                            total_tests = int(summary_match.group(1))
                                            total_duration = float(summary_match.group(2))
                                            if total_tests > 0:
                                                duration = total_duration / total_tests
                                    
                                    fallback_cases.append({
                                        'name': test_name,
                                        'status': status.lower(),
                                        'duration': duration,
                                        'error': ''
                                    })
                                if fallback_cases:
                                    # 如果HTML解析结果存在但数量不足，合并结果
                                    if 'test_cases' in test_stats and test_stats.get('test_cases'):
                                        # 合并HTML解析和pytest输出解析的结果
                                        existing_names = {case['name'] for case in test_stats['test_cases']}
                                        for case in fallback_cases:
                                            if case['name'] not in existing_names:
                                                test_stats['test_cases'].append(case)
                                        self.log(f'合并后共 {len(test_stats["test_cases"])} 个测试用例（HTML: {len(test_stats["test_cases"]) - len(fallback_cases)}, pytest输出: {len(fallback_cases)}）')
                                    else:
                                        test_stats['test_cases'] = fallback_cases
                                        self.log(f'从pytest输出解析到 {len(fallback_cases)} 个测试用例（备用方案）')
                
                # 生成自定义中文HTML报告
                if hasattr(self, 'current_report_path') and self.current_report_path:
                    generator.generate_html_report(
                        test_stats,
                        self.current_report_path,
                        modules=self.module_selector.get_selected_module_names()
                    )
                    self.log(f'自定义中文报告已生成: {self.current_report_path}')
            except Exception as e:
                error_msg = f'生成自定义报告失败: {e}'
                self.log(error_msg)
                import traceback
                tb_str = traceback.format_exc()
                self.log(tb_str)
                # 确保异常信息也被添加到log_content中
                if error_msg not in self.log_content:
                    self.log_content.append(error_msg)
                for line in tb_str.split('\n'):
                    if line.strip() and line.strip() not in self.log_content:
                        self.log_content.append(line.strip())
            
            # 执行完成（不在后台线程中使用UI操作，避免客户端断开连接问题）
            # ui.run_javascript('window.location.reload()')  # 已移除，避免客户端断开连接警告
            
            except Exception as e:
                error_msg = f'执行出错: {e}'
                self.log(error_msg)
                import traceback
                tb_str = traceback.format_exc()
                self.log(tb_str)
                # 确保异常信息也被添加到log_content中
                if error_msg not in self.log_content:
                    self.log_content.append(error_msg)
                for line in tb_str.split('\n'):
                    if line.strip() and line.strip() not in self.log_content:
                        self.log_content.append(line.strip())
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
    
    def _update_mobile_config(self, enabled: bool):
        """更新移动端配置"""
        config_path = Path("config/settings.yaml")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            if 'playwright' not in config:
                config['playwright'] = {}
            if 'device' not in config['playwright']:
                config['playwright']['device'] = {}
            config['playwright']['device']['enabled'] = enabled
            if enabled and 'name' not in config['playwright']['device']:
                config['playwright']['device']['name'] = 'iPhone 12'
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
            
            # 如果pytest-html报告存在，优先从中解析（更准确）
            if hasattr(self, 'pytest_html_report_path') and self.pytest_html_report_path and self.pytest_html_report_path.exists():
                html_stats = parser.parse_html_report(self.pytest_html_report_path)
                if html_stats:
                    # 优先使用pytest-html报告中的统计（更准确）
                    test_stats.update(html_stats)
                    
                # 解析测试用例详情（用于错误详情）
                test_cases = parser.parse_test_cases_from_html(self.pytest_html_report_path)
                if test_cases:
                    # 提取失败用例的详情
                    failed_cases = [case for case in test_cases if case.get('status') == 'failed']
                    if failed_cases:
                        test_stats['error_details'] = [
                            {
                                'name': case.get('name', 'Unknown'),
                                'error': case.get('error', '')
                            }
                            for case in failed_cases[:10]  # 最多10个
                        ]
            
            # 发送测试报告（包含HTML报告附件）
            # 使用自定义报告路径作为附件（更美观的中文报告）
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
            
            # 保存测试结果到趋势分析器
            try:
                from core.test_result_analyzer import TestResultAnalyzer
                from core.db_client import DBClient
                
                try:
                    db_client = DBClient()
                    db_client.connect()
                    analyzer = TestResultAnalyzer(db_client)
                except:
                    analyzer = TestResultAnalyzer()
                
                analyzer.save_result(
                    modules=self.module_selector.get_selected_module_names(),
                    total=test_stats['total'],
                    passed=test_stats['passed'],
                    failed=test_stats['failed'],
                    skipped=test_stats['skipped'],
                    duration=test_stats['duration'],
                    report_path=str(report_path) if report_path else None
                )
                self.log('测试结果已保存到趋势分析器')
            except Exception as e:
                self.log(f'保存测试结果到趋势分析器失败: {e}')
        except Exception as e:
            error_msg = f'发送通知失败: {e}'
            self.log(error_msg)
            import traceback
            tb_str = traceback.format_exc()
            self.log(tb_str)
            # 确保异常信息也被添加到log_content中
            if error_msg not in self.log_content:
                self.log_content.append(error_msg)
            for line in tb_str.split('\n'):
                if line.strip() and line.strip() not in self.log_content:
                    self.log_content.append(line.strip())
    
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
        # 动态获取模块列表
        from utils.module_helper import ModuleHelper
        import yaml
        from pathlib import Path
        
        # 加载模块配置
        config_path = Path("config/module_config.yaml")
        module_options = {}
        default_module = None
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                modules = config.get('modules', {})
                for module_key, module_info in modules.items():
                    if isinstance(module_info, dict) and module_info.get('enabled', True):
                        module_name = module_info.get('name', module_key)
                        module_options[module_key] = module_name
                        if default_module is None:
                            default_module = module_key
        
        # 如果没有找到模块，使用默认值
        if not module_options:
            module_options = {'teaching': '授课教学', 'exercise': '攻防演练', 'exam': '考试测评'}
            default_module = 'teaching'
        elif default_module is None:
            default_module = list(module_options.keys())[0]
        
        with ui.dialog() as dialog, ui.card().style('width: 1000px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5);'):
            with ui.column().classes('w-full').style('padding: 24px; display: flex; flex-direction: column; max-height: 90vh;'):
                ui.label('🔄 代码自动转换工具').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 16px;')
                
                # 更新使用说明，移除固定的模块名称
                module_names_str = '/'.join(module_options.values())
                ui.markdown(f"""
                <div style="color: #d0e4f0; font-size: 13px; margin-bottom: 16px; padding: 12px; background: rgba(0, 150, 255, 0.1); border-radius: 8px;">
                <strong style="color: #ffffff;">使用说明：</strong><br>
                1. 选择模块（{module_names_str}）<br>
                2. 输入测试用例名称（例如：navigation）<br>
                3. 粘贴你录制的代码<br>
                4. 点击"转换"查看转换结果<br>
                5. 确认无误后点击"保存"，完成！✅
                </div>
                """).style('margin-bottom: 16px;')
                
                # 模块选择（动态获取）
                with ui.row().classes('w-full gap-4').style('margin-bottom: 16px;'):
                    module_select = ui.select(
                        module_options,
                        label='选择模块',
                        value=default_module
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
                        '测试用例名称 *',
                        placeholder='例如：navigation、course_management（必填）',
                        value=''
                    ).style('flex: 1; color: #ffffff !important;')
                
                # 代码输入区域（自动调整大小）
                ui.label('粘贴录制的代码：').style('color: #e0e6ed; margin-bottom: 8px; font-size: 14px; font-weight: 500;')
                code_textarea = ui.textarea(
                    label='',
                    placeholder='在这里粘贴Playwright录制的代码...\n\n提示：直接粘贴完整代码即可，工具会自动处理',
                ).style('width: 100%; min-height: 200px; font-family: monospace; font-size: 12px;')
                
                # 添加自动调整大小的JavaScript
                ui.add_head_html(f'''
                <script>
                    (function() {{
                        // 等待DOM加载完成
                        setTimeout(function() {{
                            const textarea = document.querySelector('textarea[placeholder*="粘贴Playwright录制的代码"]');
                            if (textarea) {{
                                // 自动调整高度函数
                                function autoResize() {{
                                    textarea.style.height = 'auto';
                                    const scrollHeight = textarea.scrollHeight;
                                    // 设置最小高度200px，最大高度600px
                                    const minHeight = 200;
                                    const maxHeight = 600;
                                    const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
                                    textarea.style.height = newHeight + 'px';
                                    textarea.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
                                }}
                                
                                // 监听输入事件
                                textarea.addEventListener('input', autoResize);
                                textarea.addEventListener('paste', function() {{
                                    setTimeout(autoResize, 10);
                                }});
                                
                                // 初始调整
                                autoResize();
                            }}
                        }}, 100);
                    }})();
                </script>
                ''')
                
                # 按钮区域
                with ui.row().classes('w-full justify-between').style('margin-top: 16px;'):
                    ui.button('关闭', on_click=dialog.close, icon='close').style('min-height: 36px; padding: 6px 20px;')
                    
                    def convert_code():
                        """转换代码并打开结果弹窗"""
                        try:
                            original_code = code_textarea.value.strip()
                            if not original_code:
                                ui.notify('请先粘贴录制的代码！', type='warning')
                                return
                            
                            module = module_select.value
                            test_name = test_name_input.value.strip()
                            # 检查测试用例名称是否为空
                            if not test_name:
                                ui.notify('请输入测试用例名称！', type='warning')
                                test_name_input.focus()
                                return
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
                            
                            # 生成测试文件
                            test_file_content = generate_test_file(module, test_name, indented_code, "auto")
                            
                            # 直接打开转换结果弹窗（包含保存功能）
                            self._show_conversion_result(test_file_content, module, test_name, dialog)
                            
                        except Exception as e:
                            ui.notify(f'❌ 转换失败: {e}', type='negative')
                            self.log(f'代码转换失败: {e}')
                    
                    ui.button(
                        '转换',
                        on_click=convert_code,
                        icon='autorenew',
                        color='primary'
                    ).style('min-height: 36px; padding: 6px 20px;')
        
        dialog.open()
    
    def _show_conversion_result(self, converted_code: str, module: str, test_name: str, parent_dialog=None):
        """显示转换结果弹窗（包含保存功能）"""
        # 获取模块中文名称
        from utils.module_helper import ModuleHelper
        module_cn_name = ModuleHelper.get_module_cn_name(module) or module
        
        # 计算文件路径（使用正斜杠，跨平台兼容）
        filepath_str = f"test_cases/{module}/test_{module}_{test_name}.py"
        filepath = Path(filepath_str)
        
        # 使用唯一ID来标识这个textarea
        import time
        textarea_id = f'conversion-result-textarea-{int(time.time() * 1000)}'
        
        # 缩小弹窗：1600px * 0.8 = 1280px
        with ui.dialog() as result_dialog, ui.card().style('width: 1280px; max-width: 98vw; height: 95vh; max-height: 95vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5); display: flex; flex-direction: column; box-sizing: border-box;'):
            with ui.column().classes('w-full').style('padding: 20px; display: flex; flex-direction: column; height: 100%; max-height: 100%; box-sizing: border-box; overflow: hidden;'):
                # 标题和文件信息（固定高度，不收缩）
                with ui.column().style('flex-shrink: 0; margin-bottom: 16px;'):
                    ui.label('📋 转换后的代码').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 8px;')
                    # 显示测试用例名称和保存文件名
                    display_test_name = test_name.replace('test_', '') if test_name.startswith('test_') else test_name
                    filename = f"test_{module}_{test_name}.py"
                    ui.label(f'模块: {module_cn_name} | 测试用例: {display_test_name} | 保存文件名: {filename}').style('color: #b0c4de; font-size: 13px; margin-bottom: 4px;')
                    # 显示保存路径（使用正斜杠）
                    ui.label(f'保存路径: {filepath_str}').style('color: #80a4de; font-size: 12px; font-family: monospace;')
                
                # 代码编辑区域
                code_textarea = ui.textarea(
                    value=converted_code,
                    label=''
                ).classes('w-full').style(
                    'font-family: "Consolas", "Monaco", "Courier New", monospace; '
                    'font-size: 13px; '
                    'background: rgba(10, 20, 35, 0.8); '
                    'color: #e0e6ed; '
                    'border: 1px solid rgba(0, 150, 255, 0.3); '
                    'border-radius: 4px; '
                    'padding: 12px;'
                )
                
                with ui.row().classes('w-full justify-end gap-3').style('flex-shrink: 0; margin-top: 16px;'):
                    def save_file():
                        """保存转换后的代码为文件"""
                        try:
                            # 直接获取textarea的值（简单直接，无需同步）
                            edited_code = code_textarea.value
                            
                            # 确保是字符串类型
                            if not isinstance(edited_code, str):
                                edited_code = str(edited_code) if edited_code else converted_code
                            
                            # 如果为空，使用原始代码
                            if not edited_code:
                                edited_code = converted_code
                            
                            # 保存文件
                            test_dir = Path(f"test_cases/{module}")
                            test_dir.mkdir(parents=True, exist_ok=True)
                            
                            filename = f"test_{module}_{test_name}.py"
                            filepath = test_dir / filename
                            
                            filepath.write_text(edited_code, encoding='utf-8')
                            
                            ui.notify(f'✅ 文件已保存到: {filepath}', type='positive', timeout=5000)
                            self.log(f'代码转换成功: {filepath}')
                            
                            # 保存后关闭弹窗
                            result_dialog.close()
                            # 如果提供了父对话框，也关闭它
                            if parent_dialog:
                                parent_dialog.close()
                            
                        except Exception as e:
                            ui.notify(f'❌ 保存失败: {e}', type='negative')
                            self.log(f'代码保存失败: {e}')
                    
                    ui.button('关闭', on_click=result_dialog.close, icon='close', color='negative').style('min-height: 36px; padding: 6px 20px;')
                    ui.button('保存', on_click=save_file, icon='save', color='positive').style('min-height: 36px; padding: 6px 20px;')
        
        result_dialog.open()
    
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
        # 确保日志也被添加到log_content中，以便导出
        if log_message not in self.log_content:
            self.log_content.append(log_message)
        if len(self.log_content) > self.max_log_lines:
            self.log_content.pop(0)
    
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
        # 支持两种报告类型：WebUI自动化测试报告_*.html 和 pytest自动化测试报告_*.html
        html_reports = sorted(
            list(reports_dir.glob("WebUI自动化测试报告_*.html")) + list(reports_dir.glob("pytest自动化测试报告_*.html")),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # 添加滚动条样式
        ui.add_head_html('''
        <style>
            .report-list-container {
                max-height: 500px;
                overflow-y: auto;
                overflow-x: hidden;
                padding-right: 8px;
            }
            .report-list-container::-webkit-scrollbar {
                width: 8px;
            }
            .report-list-container::-webkit-scrollbar-track {
                background: rgba(10, 22, 40, 0.3);
                border-radius: 4px;
            }
            .report-list-container::-webkit-scrollbar-thumb {
                background: rgba(0, 150, 255, 0.5);
                border-radius: 4px;
            }
            .report-list-container::-webkit-scrollbar-thumb:hover {
                background: rgba(0, 150, 255, 0.7);
            }
        </style>
        ''')
        
        # 存储报告列表容器，用于动态更新
        report_list_container = None
        
        def refresh_report_list():
            """刷新报告列表"""
            nonlocal html_reports
            # 重新获取报告列表
            html_reports = sorted(
                list(reports_dir.glob("WebUI自动化测试报告_*.html")) + list(reports_dir.glob("pytest自动化测试报告_*.html")),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            # 清空并重新填充列表
            if report_list_container:
                report_list_container.clear()
                with report_list_container:
                    if not html_reports:
                        with ui.column().classes('w-full items-center').style('padding: 40px;'):
                            ui.icon('description', size=64).style('color: #90caf9; opacity: 0.5; margin-bottom: 16px;')
                            ui.label('暂无测试报告').style('color: #90caf9; font-size: 16px; margin-bottom: 8px;')
                            ui.label('执行测试后会自动生成报告').style('color: #b0c4de; font-size: 12px;')
                    else:
                        for report_file in html_reports:
                            # 获取文件信息
                            file_stat = report_file.stat()
                            file_size = file_stat.st_size / 1024  # KB
                            file_time = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                            
                            # 判断报告类型
                            if "WebUI自动化测试报告" in report_file.name:
                                report_type = "📊 WebUI报告"
                            elif "pytest自动化测试报告" in report_file.name or "pytest_report" in report_file.name:
                                report_type = "🔧 pytest报告"
                            else:
                                report_type = "📄 其他报告"
                            
                            with ui.card().classes('w-full').style('background: rgba(10, 22, 40, 0.6); border: 1px solid rgba(0, 150, 255, 0.3); padding: 16px; transition: all 0.3s;'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    with ui.column().classes('flex-1').style('min-width: 0;'):
                                        with ui.row().classes('gap-2 items-center').style('margin-bottom: 4px;'):
                                            ui.label(report_type).style('color: #4fc3f7; font-size: 11px; padding: 2px 8px; background: rgba(0, 150, 255, 0.2); border-radius: 4px;')
                                            ui.label(report_file.name).style('color: #e0e6ed; font-size: 14px; font-weight: 500;')
                                        with ui.row().classes('gap-4').style('font-size: 12px;'):
                                            ui.label(f'📅 {file_time}').style('color: #90caf9;')
                                            ui.label(f'📦 {file_size:.1f} KB').style('color: #90caf9;')
                                    
                                    with ui.row().classes('gap-2'):
                                        ui.button('打开', icon='open_in_new', on_click=lambda rf=report_file: self._open_report(rf)).style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
                                        ui.button('删除', icon='delete', color='red', on_click=lambda rf=report_file: self._delete_report(rf, refresh_report_list)).style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
        
        with ui.dialog() as dialog, ui.card().style('width: 1000px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5);'):
            with ui.column().classes('w-full').style('padding: 24px; display: flex; flex-direction: column; max-height: 90vh;'):
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
                    with ui.column().classes('w-full report-list-container').style('flex: 1; min-height: 0; gap: 12px;') as container:
                        report_list_container = container
                        for report_file in html_reports:
                            # 获取文件信息
                            file_stat = report_file.stat()
                            file_size = file_stat.st_size / 1024  # KB
                            file_time = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                            
                            # 判断报告类型
                            if "WebUI自动化测试报告" in report_file.name:
                                report_type = "📊 WebUI报告"
                            elif "pytest自动化测试报告" in report_file.name or "pytest_report" in report_file.name:
                                report_type = "🔧 pytest报告"
                            else:
                                report_type = "📄 其他报告"
                            
                            with ui.card().classes('w-full').style('background: rgba(10, 22, 40, 0.6); border: 1px solid rgba(0, 150, 255, 0.3); padding: 16px; transition: all 0.3s;'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    with ui.column().classes('flex-1').style('min-width: 0;'):
                                        with ui.row().classes('gap-2 items-center').style('margin-bottom: 4px;'):
                                            ui.label(report_type).style('color: #4fc3f7; font-size: 11px; padding: 2px 8px; background: rgba(0, 150, 255, 0.2); border-radius: 4px;')
                                            ui.label(report_file.name).style('color: #e0e6ed; font-size: 14px; font-weight: 500;')
                                        with ui.row().classes('gap-4').style('font-size: 12px;'):
                                            ui.label(f'📅 {file_time}').style('color: #90caf9;')
                                            ui.label(f'📦 {file_size:.1f} KB').style('color: #90caf9;')
                                    
                                    with ui.row().classes('gap-2'):
                                        ui.button('打开', icon='open_in_new', on_click=lambda rf=report_file: self._open_report(rf)).style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
                                        ui.button('删除', icon='delete', color='red', on_click=lambda rf=report_file: self._delete_report(rf, refresh_report_list)).style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
                
                # 底部操作按钮
                with ui.row().classes('w-full justify-between').style('margin-top: 20px; padding-top: 16px; border-top: 1px solid rgba(0, 150, 255, 0.2); flex-shrink: 0;'):
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
    
    def _delete_report(self, report_file: Path, refresh_callback):
        """删除测试报告
        
        Args:
            report_file: 报告文件路径
            refresh_callback: 刷新列表的回调函数
        """
        try:
            report_file.unlink()
            ui.notify(f'已删除报告: {report_file.name}', type='positive')
            # 调用刷新回调，不关闭弹窗
            if refresh_callback:
                refresh_callback()
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


