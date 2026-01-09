"""
测试环境管理器
支持多环境切换和管理

@File  : environment_manager.py
@Author: shenyuan
"""
import yaml
from pathlib import Path
from typing import Dict, Optional


class EnvironmentManager:
    """环境管理器"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """初始化环境管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.current_env = None
        self.environments = {}
        self._load_environments()
    
    def _load_environments(self):
        """加载环境配置"""
        if not self.config_path.exists():
            return
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 加载环境列表
        self.environments = config.get('environments', {})
        self.current_env = config.get('current_environment', 'default')
        
        # 如果没有environments配置，创建默认环境
        if not self.environments:
            self.environments = {
                'default': {
                    'name': '默认环境',
                    'base_url': config.get('login', {}).get('url', '').replace('#/login', ''),
                    'login_url': config.get('login', {}).get('url', ''),
                    'username': config.get('login', {}).get('username', ''),
                    'password': config.get('login', {}).get('password', ''),
                    'database': config.get('database', {})
                }
            }
    
    def get_current_environment(self) -> Dict:
        """获取当前环境配置
        
        Returns:
            环境配置字典
        """
        return self.environments.get(self.current_env, {})
    
    def set_environment(self, env_name: str) -> bool:
        """切换环境
        
        Args:
            env_name: 环境名称
            
        Returns:
            是否切换成功
        """
        if env_name not in self.environments:
            return False
        
        self.current_env = env_name
        
        # 保存到配置文件
        self._save_current_environment()
        return True
    
    def add_environment(self, env_name: str, config: Dict) -> bool:
        """添加新环境
        
        Args:
            env_name: 环境名称
            config: 环境配置
            
        Returns:
            是否添加成功
        """
        self.environments[env_name] = config
        self._save_environments()
        return True
    
    def remove_environment(self, env_name: str) -> bool:
        """删除环境
        
        Args:
            env_name: 环境名称
            
        Returns:
            是否删除成功
        """
        if env_name == 'default':
            return False  # 不能删除默认环境
        
        if env_name in self.environments:
            del self.environments[env_name]
            self._save_environments()
            
            # 如果删除的是当前环境，切换到默认环境
            if self.current_env == env_name:
                self.current_env = 'default'
                self._save_current_environment()
            
            return True
        return False
    
    def get_all_environments(self) -> Dict[str, Dict]:
        """获取所有环境
        
        Returns:
            环境字典
        """
        return self.environments
    
    def _save_current_environment(self):
        """保存当前环境到配置文件"""
        if not self.config_path.exists():
            return
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        config['current_environment'] = self.current_env
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    def _save_environments(self):
        """保存所有环境到配置文件"""
        if not self.config_path.exists():
            return
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        config['environments'] = self.environments
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

