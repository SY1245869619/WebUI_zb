"""
通知服务封装
支持钉钉机器人和邮件发送
"""
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import hmac
import hashlib
import base64
import urllib.parse
import time
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


class NotificationService:
    """通知服务类，支持钉钉和邮件"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """初始化通知服务
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _generate_dingtalk_sign(self, secret: str, timestamp: str) -> str:
        """生成钉钉签名
        
        Args:
            secret: 机器人密钥
            timestamp: 时间戳
            
        Returns:
            签名字符串
        """
        string_to_sign = f'{timestamp}\n{secret}'
        hmac_code = hmac.new(
            secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign
    
    def send_dingtalk_message(
        self, 
        message: str, 
        title: Optional[str] = None,
        at_mobiles: Optional[List[str]] = None,
        at_all: bool = False
    ) -> bool:
        """发送钉钉消息
        
        Args:
            message: 消息内容
            title: 消息标题
            at_mobiles: @的手机号列表
            at_all: 是否@所有人
            
        Returns:
            是否发送成功
        """
        dingtalk_config = self.config['notification']['dingtalk']
        
        if not dingtalk_config.get('enabled', False):
            print("钉钉通知未启用")
            return False
        
        webhook = dingtalk_config['webhook']
        secret = dingtalk_config.get('secret', '')
        
        # 生成签名
        timestamp = str(round(time.time() * 1000))
        if secret:
            sign = self._generate_dingtalk_sign(secret, timestamp)
            webhook = f"{webhook}&timestamp={timestamp}&sign={sign}"
        
        # 构建消息体
        msg_data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title or "自动化测试通知",
                "text": message
            }
        }
        
        if at_mobiles or at_all:
            msg_data["at"] = {
                "atMobiles": at_mobiles or [],
                "isAtAll": at_all
            }
        
        try:
            response = requests.post(webhook, json=msg_data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('errcode') == 0:
                print("钉钉消息发送成功")
                return True
            else:
                print(f"钉钉消息发送失败: {result.get('errmsg')}")
                return False
        except Exception as e:
            print(f"发送钉钉消息时出错: {e}")
            return False
    
    def send_email(
        self,
        subject: str,
        content: str,
        html: bool = False,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """发送邮件
        
        Args:
            subject: 邮件主题
            content: 邮件内容
            html: 是否为HTML格式
            attachments: 附件路径列表
            
        Returns:
            是否发送成功
        """
        email_config = self.config['notification']['email']
        
        if not email_config.get('enabled', False):
            print("邮件通知未启用")
            return False
        
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = Header(email_config['sender_email'], 'utf-8')
            msg['To'] = Header(','.join(email_config['receiver_emails']), 'utf-8')
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 添加正文
            if html:
                msg.attach(MIMEText(content, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # 添加附件
            if attachments:
                from email.mime.base import MIMEBase
                from email import encoders
                
                for file_path in attachments:
                    with open(file_path, 'rb') as f:
                        mime = MIMEBase('application', 'octet-stream')
                        mime.set_payload(f.read())
                        encoders.encode_base64(mime)
                        mime.add_header(
                            'Content-Disposition',
                            f'attachment; filename={Path(file_path).name}'
                        )
                        msg.attach(mime)
            
            # 发送邮件
            smtp = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            smtp.starttls()
            smtp.login(email_config['sender_email'], email_config['sender_password'])
            smtp.sendmail(
                email_config['sender_email'],
                email_config['receiver_emails'],
                msg.as_string()
            )
            smtp.quit()
            
            print("邮件发送成功")
            return True
        except Exception as e:
            print(f"发送邮件时出错: {e}")
            return False
    
    def send_test_report(
        self,
        modules: List[str],
        total: int,
        passed: int,
        failed: int,
        skipped: int,
        duration: float,
        error_details: Optional[List[Dict[str, Any]]] = None
    ):
        """发送测试报告
        
        Args:
            modules: 执行的模块列表
            total: 总用例数
            passed: 通过数
            failed: 失败数
            skipped: 跳过数
            duration: 执行时长（秒）
            error_details: 错误详情列表
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建钉钉消息
        dingtalk_msg = f"""# 自动化测试报告
        
**执行时间**: {timestamp}

**执行模块**: {', '.join(modules)}

**测试统计**:
- 总用例数: {total}
- 通过: {passed} ✅
- 失败: {failed} ❌
- 跳过: {skipped} ⏭️

**执行时长**: {duration:.2f}秒

**通过率**: {(passed/total*100) if total > 0 else 0:.2f}%
"""
        
        if error_details:
            dingtalk_msg += "\n**失败用例**:\n"
            for error in error_details[:5]:  # 只显示前5个错误
                dingtalk_msg += f"- {error.get('name', 'Unknown')}: {error.get('error', '')}\n"
        
        # 构建邮件内容
        email_content = f"""
自动化测试报告

执行时间: {timestamp}

执行模块: {', '.join(modules)}

测试统计:
- 总用例数: {total}
- 通过: {passed}
- 失败: {failed}
- 跳过: {skipped}

执行时长: {duration:.2f}秒

通过率: {(passed/total*100) if total > 0 else 0:.2f}%
"""
        
        if error_details:
            email_content += "\n失败用例详情:\n"
            for error in error_details:
                email_content += f"\n用例: {error.get('name', 'Unknown')}\n"
                email_content += f"错误: {error.get('error', '')}\n"
                email_content += "-" * 50 + "\n"
        
        # 发送通知
        if self.config['notification']['dingtalk'].get('enabled', False):
            self.send_dingtalk_message(dingtalk_msg, "自动化测试报告")
        
        if self.config['notification']['email'].get('enabled', False):
            self.send_email("自动化测试报告", email_content)

