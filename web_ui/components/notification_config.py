"""
通知配置组件（钉钉和邮箱）
"""
from nicegui import ui
import yaml
from pathlib import Path
from typing import Dict


class NotificationConfig:
    """通知配置组件"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """初始化通知配置
        
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
            return {"notification": {"dingtalk": {}, "email": {}}}
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def render(self) -> ui.card:
        """渲染通知配置界面
        
        Returns:
            UI卡片组件
        """
        with ui.card().classes('w-full'):
            ui.label('通知配置').classes('text-lg font-bold mb-4')
            
            # 钉钉配置
            with ui.expansion('钉钉机器人配置', icon='chat').classes('w-full mb-4'):
                self.checkboxes['dingtalk_enabled'] = ui.checkbox(
                    '启用钉钉通知',
                    value=self.config['notification']['dingtalk'].get('enabled', False)
                ).classes('mb-2')
                
                self.inputs['dingtalk_webhook'] = ui.input(
                    'Webhook地址',
                    placeholder='https://oapi.dingtalk.com/robot/send?access_token=xxx',
                    value=self.config['notification']['dingtalk'].get('webhook', '')
                ).classes('w-full mb-2')
                
                self.inputs['dingtalk_secret'] = ui.input(
                    '密钥（可选）',
                    placeholder='如果机器人设置了加签，请填写',
                    value=self.config['notification']['dingtalk'].get('secret', ''),
                    password=True
                ).classes('w-full')
            
            # 邮箱配置
            with ui.expansion('邮箱配置', icon='email').classes('w-full'):
                self.checkboxes['email_enabled'] = ui.checkbox(
                    '启用邮件通知',
                    value=self.config['notification']['email'].get('enabled', False)
                ).classes('mb-2')
                
                self.inputs['email_smtp_server'] = ui.input(
                    'SMTP服务器',
                    placeholder='smtp.qq.com',
                    value=self.config['notification']['email'].get('smtp_server', '')
                ).classes('w-full mb-2')
                
                self.inputs['email_smtp_port'] = ui.input(
                    'SMTP端口',
                    placeholder='587',
                    value=str(self.config['notification']['email'].get('smtp_port', 587))
                ).classes('w-full mb-2')
                
                self.inputs['email_sender'] = ui.input(
                    '发件人邮箱',
                    placeholder='your_email@qq.com',
                    value=self.config['notification']['email'].get('sender_email', '')
                ).classes('w-full mb-2')
                
                self.inputs['email_password'] = ui.input(
                    '发件人密码/授权码',
                    value=self.config['notification']['email'].get('sender_password', ''),
                    password=True
                ).classes('w-full mb-2')
                
                self.inputs['email_receivers'] = ui.textarea(
                    '收件人邮箱（每行一个）',
                    value='\n'.join(self.config['notification']['email'].get('receiver_emails', []))
                ).classes('w-full')
            
            # 保存配置按钮
            ui.button('保存配置', on_click=self.save_config, icon='save').classes('mt-4')
        
        return self
    
    def save_config(self):
        """保存配置到YAML文件"""
        try:
            # 更新配置
            self.config['notification']['dingtalk']['enabled'] = self.checkboxes['dingtalk_enabled'].value
            self.config['notification']['dingtalk']['webhook'] = self.inputs['dingtalk_webhook'].value
            self.config['notification']['dingtalk']['secret'] = self.inputs['dingtalk_secret'].value
            
            self.config['notification']['email']['enabled'] = self.checkboxes['email_enabled'].value
            self.config['notification']['email']['smtp_server'] = self.inputs['email_smtp_server'].value
            self.config['notification']['email']['smtp_port'] = int(self.inputs['email_smtp_port'].value or 587)
            self.config['notification']['email']['sender_email'] = self.inputs['email_sender'].value
            self.config['notification']['email']['sender_password'] = self.inputs['email_password'].value
            
            # 处理收件人列表
            receivers_text = self.inputs['email_receivers'].value
            self.config['notification']['email']['receiver_emails'] = [
                email.strip() for email in receivers_text.split('\n') if email.strip()
            ]
            
            # 保存到文件
            config_file = Path(self.config_path)
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            
            ui.notify('配置保存成功！', type='positive', position='top')
        except Exception as e:
            ui.notify(f'保存配置失败: {e}', type='negative', position='top')
    
    def get_config(self) -> dict:
        """获取当前配置
        
        Returns:
            配置字典
        """
        return {
            'dingtalk': {
                'enabled': self.checkboxes['dingtalk_enabled'].value,
                'webhook': self.inputs['dingtalk_webhook'].value,
                'secret': self.inputs['dingtalk_secret'].value,
            },
            'email': {
                'enabled': self.checkboxes['email_enabled'].value,
                'smtp_server': self.inputs['email_smtp_server'].value,
                'smtp_port': int(self.inputs['email_smtp_port'].value or 587),
                'sender_email': self.inputs['email_sender'].value,
                'sender_password': self.inputs['email_password'].value,
                'receiver_emails': [
                    email.strip() for email in self.inputs['email_receivers'].value.split('\n') if email.strip()
                ],
            }
        }

