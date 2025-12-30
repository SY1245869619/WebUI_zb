"""
登录配置组件
用于在Web界面中配置登录信息

@File  : login_config.py
@Author: shenyuan
"""
from nicegui import ui
import yaml
from pathlib import Path
from typing import Dict


class LoginConfig:
    """登录配置组件"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """初始化登录配置
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.inputs: Dict[str, ui.input] = {}
        self.checkboxes: Dict[str, ui.checkbox] = {}
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if not config_file.exists():
            return {"login": {}}
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def render(self) -> ui.card:
        """渲染登录配置界面
        
        Returns:
            UI卡片组件
        """
        with ui.card().classes('w-full config-section'):
            with ui.column().classes('card-content'):
                ui.label('🔐 登录配置').classes('section-title').style('color: #e0e6ed;')
            
            # 登录URL
            self.inputs['login_url'] = ui.input(
                '登录页面URL',
                placeholder='http://10.70.70.96/Shenyuan_9#/login',
                value=self.config.get('login', {}).get('url', 'http://10.70.70.96/Shenyuan_9#/login')
            ).classes('w-full mb-2')
            
            # 用户名
            self.inputs['username'] = ui.input(
                '用户名',
                placeholder='Shenyuan_9',
                value=self.config.get('login', {}).get('username', 'Shenyuan_9')
            ).classes('w-full mb-2')
            
            # 密码
            self.inputs['password'] = ui.input(
                '密码',
                placeholder='请输入密码',
                value=self.config.get('login', {}).get('password', ''),
                password=True
            ).classes('w-full mb-2')
            
            # 自动登录开关
            self.checkboxes['auto_login'] = ui.checkbox(
                '自动登录',
                value=self.config.get('login', {}).get('auto_login', True)
            ).classes('mb-4')
            
            # 元素选择器配置（高级选项）
            with ui.expansion('高级选项 - 元素选择器', icon='settings').classes('w-full mb-4'):
                ui.markdown("""
                **说明**: 如果默认选择器无法定位元素，可以在这里自定义选择器。
                多个选择器用逗号分隔，系统会依次尝试。
                """).classes('mb-2')
                
                self.inputs['username_selector'] = ui.textarea(
                    '用户名输入框选择器',
                    value=self.config.get('login', {}).get('username_selector', 
                        'input[name="username"], input[type="text"], input[placeholder*="用户名"], input[placeholder*="账号"]')
                ).classes('w-full mb-2').style('min-height: 60px')
                
                self.inputs['password_selector'] = ui.textarea(
                    '密码输入框选择器',
                    value=self.config.get('login', {}).get('password_selector',
                        'input[name="password"], input[type="password"]')
                ).classes('w-full mb-2').style('min-height: 60px')
                
                self.inputs['login_button_selector'] = ui.textarea(
                    '登录按钮选择器',
                    value=self.config.get('login', {}).get('login_button_selector',
                        'button:has-text("登录"), button[type="submit"], .login-btn, [class*="login-button"]')
                ).classes('w-full').style('min-height: 60px')
            
            # 保存配置按钮
            ui.button('保存登录配置', on_click=self.save_config, icon='save').classes('mt-2')
        
        return self
    
    def save_config(self):
        """保存配置到YAML文件"""
        try:
            # 确保login配置存在
            if 'login' not in self.config:
                self.config['login'] = {}
            
            # 更新配置
            self.config['login']['url'] = self.inputs['login_url'].value
            self.config['login']['username'] = self.inputs['username'].value
            self.config['login']['password'] = self.inputs['password'].value
            self.config['login']['auto_login'] = self.checkboxes['auto_login'].value
            self.config['login']['username_selector'] = self.inputs['username_selector'].value
            self.config['login']['password_selector'] = self.inputs['password_selector'].value
            self.config['login']['login_button_selector'] = self.inputs['login_button_selector'].value
            
            # 保存到文件
            config_file = Path(self.config_path)
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            
            ui.notify('登录配置保存成功！', type='positive', position='top')
        except Exception as e:
            ui.notify(f'保存登录配置失败: {e}', type='negative', position='top')
    
    def get_config(self) -> dict:
        """获取当前配置
        
        Returns:
            配置字典
        """
        return {
            'url': self.inputs['login_url'].value,
            'username': self.inputs['username'].value,
            'password': self.inputs['password'].value,
            'auto_login': self.checkboxes['auto_login'].value,
            'username_selector': self.inputs['username_selector'].value,
            'password_selector': self.inputs['password_selector'].value,
            'login_button_selector': self.inputs['login_button_selector'].value,
        }

