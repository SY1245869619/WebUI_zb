"""
通知服务封装
支持钉钉机器人和邮件发送

@File  : notification.py
@Author: shenyuan
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
            # 检查必要字段
            sender_email = email_config.get('sender_email', '').strip()
            receiver_emails = email_config.get('receiver_emails', [])
            
            if not sender_email:
                print("发件人邮箱未配置")
                return False
            
            if not receiver_emails:
                print("收件人邮箱未配置")
                return False
            
            # 创建邮件对象
            msg = MIMEMultipart()
            # QQ邮箱要求From头必须是纯邮箱地址字符串，不能使用Header包装
            msg['From'] = sender_email
            msg['To'] = ','.join(receiver_emails)
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
                    file_path_obj = Path(file_path)
                    if not file_path_obj.exists():
                        print(f"附件文件不存在: {file_path}")
                        continue
                    
                    try:
                        with open(file_path_obj, 'rb') as f:
                            mime = MIMEBase('application', 'octet-stream')
                            mime.set_payload(f.read())
                            encoders.encode_base64(mime)
                            # 使用Header确保中文文件名正确编码（使用顶部导入的Header）
                            filename_header = Header(file_path_obj.name, 'utf-8')
                            mime.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{filename_header.encode()}"'
                            )
                            # 添加Content-Type头
                            mime.add_header('Content-Type', 'text/html; charset=utf-8')
                            msg.attach(mime)
                            print(f"附件已添加: {file_path_obj.name}")
                    except Exception as e:
                        print(f"添加附件失败 {file_path}: {e}")
                        import traceback
                        traceback.print_exc()
            
            # 发送邮件
            smtp = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            smtp.starttls()
            smtp.login(sender_email, email_config['sender_password'])
            smtp.sendmail(
                sender_email,
                receiver_emails,
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
        error_details: Optional[List[Dict[str, Any]]] = None,
        html_report_path: Optional[Path] = None
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
            html_report_path: HTML报告文件路径（可选）
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pass_rate = (passed/total*100) if total > 0 else 0
        
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

**通过率**: {pass_rate:.2f}%
"""
        
        if error_details:
            dingtalk_msg += "\n**失败用例**:\n"
            for error in error_details[:5]:  # 只显示前5个错误
                error_msg = error.get('error', '')[:100]  # 限制长度
                dingtalk_msg += f"- {error.get('name', 'Unknown')}: {error_msg}\n"
        
        # 如果存在HTML报告，在钉钉消息中添加提示
        if html_report_path and html_report_path.exists():
            # 钉钉机器人不支持直接附件，但可以提供相对路径和说明
            report_name = html_report_path.name
            # 使用相对路径（相对于项目根目录）
            try:
                from pathlib import Path
                project_root = Path.cwd()
                relative_path = html_report_path.relative_to(project_root)
                report_path = str(relative_path).replace('\\', '/')  # 统一使用正斜杠
            except:
                report_path = f"reports/{report_name}"
            
            dingtalk_msg += f"\n---\n"
            dingtalk_msg += f"**📄 详细报告**: `{report_path}`\n"
            dingtalk_msg += f"💡 完整HTML报告已通过邮件发送"
        
        # 构建邮件内容（HTML格式）
        email_html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #0096ff; padding-bottom: 10px; }}
        .info {{ margin: 20px 0; }}
        .info-item {{ margin: 10px 0; padding: 8px; background: #f9f9f9; border-left: 4px solid #0096ff; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }}
        .stat-card {{ flex: 1; min-width: 150px; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-total {{ background: #e3f2fd; color: #1976d2; }}
        .stat-passed {{ background: #e8f5e9; color: #388e3c; }}
        .stat-failed {{ background: #ffebee; color: #d32f2f; }}
        .stat-skipped {{ background: #fff3e0; color: #f57c00; }}
        .stat-number {{ font-size: 32px; font-weight: bold; margin: 10px 0; }}
        .stat-label {{ font-size: 14px; }}
        .errors {{ margin-top: 20px; }}
        .error-item {{ margin: 15px 0; padding: 15px; background: #fff3f3; border-left: 4px solid #d32f2f; border-radius: 4px; }}
        .error-name {{ font-weight: bold; color: #d32f2f; margin-bottom: 8px; }}
        .error-msg {{ color: #666; font-size: 12px; white-space: pre-wrap; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 自动化测试报告</h1>
        
        <div class="info">
            <div class="info-item"><strong>执行时间:</strong> {timestamp}</div>
            <div class="info-item"><strong>执行模块:</strong> {', '.join(modules)}</div>
            <div class="info-item"><strong>执行时长:</strong> {duration:.2f}秒</div>
        </div>
        
        <div class="stats">
            <div class="stat-card stat-total">
                <div class="stat-number">{total}</div>
                <div class="stat-label">总用例数</div>
            </div>
            <div class="stat-card stat-passed">
                <div class="stat-number">{passed}</div>
                <div class="stat-label">通过 ✅</div>
            </div>
            <div class="stat-card stat-failed">
                <div class="stat-number">{failed}</div>
                <div class="stat-label">失败 ❌</div>
            </div>
            <div class="stat-card stat-skipped">
                <div class="stat-number">{skipped}</div>
                <div class="stat-label">跳过 ⏭️</div>
            </div>
        </div>
        
        <div class="info-item" style="text-align: center; font-size: 18px; font-weight: bold; color: {'#388e3c' if pass_rate >= 80 else '#d32f2f' if pass_rate < 50 else '#f57c00'};">
            通过率: {pass_rate:.2f}%
        </div>
"""
        
        if error_details:
            email_html_content += """
        <div class="errors">
            <h2>失败用例详情</h2>
"""
            for error in error_details:
                error_name = error.get('name', 'Unknown')
                error_msg = error.get('error', '')
                # HTML转义
                error_msg = error_msg.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                email_html_content += f"""
            <div class="error-item">
                <div class="error-name">{error_name}</div>
                <div class="error-msg">{error_msg}</div>
            </div>
"""
            email_html_content += """
        </div>
"""
        
        email_html_content += f"""
        <div class="footer">
            <p>此报告由 WebUI自动化测试平台自动生成</p>
            <p>报告时间: {timestamp}</p>
        </div>
    </div>
</body>
</html>
"""
        
        # 构建纯文本邮件内容（作为后备）
        email_text_content = f"""
自动化测试报告

执行时间: {timestamp}

执行模块: {', '.join(modules)}

测试统计:
- 总用例数: {total}
- 通过: {passed}
- 失败: {failed}
- 跳过: {skipped}

执行时长: {duration:.2f}秒

通过率: {pass_rate:.2f}%
"""
        
        if error_details:
            email_text_content += "\n失败用例详情:\n"
            for error in error_details:
                email_text_content += f"\n用例: {error.get('name', 'Unknown')}\n"
                email_text_content += f"错误: {error.get('error', '')}\n"
                email_text_content += "-" * 50 + "\n"
        
        # 准备附件列表
        attachments = []
        if html_report_path and html_report_path.exists():
            attachments.append(str(html_report_path))
        
        # 发送通知
        if self.config['notification']['dingtalk'].get('enabled', False):
            self.send_dingtalk_message(dingtalk_msg, "自动化测试报告")
        
        if self.config['notification']['email'].get('enabled', False):
            # 发送HTML格式邮件，包含报告附件
            self.send_email(
                subject=f"自动化测试报告 - {timestamp}",
                content=email_html_content,
                html=True,
                attachments=attachments
            )

