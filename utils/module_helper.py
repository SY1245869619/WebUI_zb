"""
模块辅助工具
用于动态获取模块信息，避免硬编码模块名称

@File  : module_helper.py
@Author: shenyuan
"""
import yaml
from pathlib import Path
from typing import Dict, Optional, List


class ModuleHelper:
    """模块辅助类，用于动态获取模块信息"""
    
    _module_config = None
    _module_map = None  # {module_key: module_cn_name}
    _module_map_reverse = None  # {module_cn_name: module_key}
    
    @classmethod
    def _load_config(cls, config_path: str = "config/module_config.yaml") -> dict:
        """加载模块配置文件"""
        if cls._module_config is None:
            config_file = Path(config_path)
            if not config_file.exists():
                # 如果配置文件不存在，返回空配置
                cls._module_config = {"modules": {}}
            else:
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        cls._module_config = yaml.safe_load(f) or {"modules": {}}
                except Exception as e:
                    print(f"[ModuleHelper] 加载配置文件失败: {e}")
                    cls._module_config = {"modules": {}}
        return cls._module_config
    
    @classmethod
    def _build_module_map(cls) -> Dict[str, str]:
        """构建模块映射字典 {module_key: module_cn_name}"""
        if cls._module_map is None:
            config = cls._load_config()
            modules = config.get("modules", {})
            cls._module_map = {}
            for module_key, module_info in modules.items():
                if isinstance(module_info, dict):
                    module_cn_name = module_info.get("name", module_key)
                else:
                    module_cn_name = str(module_info)
                cls._module_map[module_key] = module_cn_name
        return cls._module_map
    
    @classmethod
    def _build_reverse_module_map(cls) -> Dict[str, str]:
        """构建反向模块映射字典 {module_cn_name: module_key}"""
        if cls._module_map_reverse is None:
            module_map = cls._build_module_map()
            cls._module_map_reverse = {v: k for k, v in module_map.items()}
        return cls._module_map_reverse
    
    @classmethod
    def get_module_cn_name(cls, module_key: str) -> str:
        """根据模块key获取中文名称
        
        Args:
            module_key: 模块键名（如 'teaching', 'exercise'）
            
        Returns:
            模块中文名称，如果找不到则返回原key
        """
        module_map = cls._build_module_map()
        return module_map.get(module_key, module_key)
    
    @classmethod
    def get_module_key(cls, module_cn_name: str) -> str:
        """根据模块中文名称获取key
        
        Args:
            module_cn_name: 模块中文名称（如 '授课教学'）
            
        Returns:
            模块key，如果找不到则返回原名称
        """
        reverse_map = cls._build_reverse_module_map()
        return reverse_map.get(module_cn_name, module_cn_name)
    
    @classmethod
    def get_all_modules(cls) -> Dict[str, str]:
        """获取所有模块映射
        
        Returns:
            模块映射字典 {module_key: module_cn_name}
        """
        return cls._build_module_map()
    
    @classmethod
    def extract_module_from_path(cls, test_path: str) -> Optional[str]:
        """从测试文件路径中提取模块名称
        
        Args:
            test_path: 测试文件路径，例如 'test_cases/teaching/test_teaching_first.py::TestClass::test_method'
                      或 'test_teaching_first.py'
            
        Returns:
            模块key（如 'teaching'），如果无法提取则返回None
        """
        # 提取文件路径部分（去除::后面的部分）
        file_path = test_path.split('::')[0] if '::' in test_path else test_path
        
        # 检查路径中是否包含 test_cases/模块名/ 的模式
        if 'test_cases/' in file_path:
            parts = file_path.split('test_cases/')
            if len(parts) > 1:
                module_part = parts[1].split('/')[0].split('\\')[0]
                # 验证这个模块是否在配置中存在
                module_map = cls._build_module_map()
                if module_part in module_map:
                    return module_part
        
        # 如果路径中没有 test_cases/，尝试从文件名中提取
        # 例如 test_teaching_first.py -> teaching
        file_name = Path(file_path).name
        if file_name.startswith('test_'):
            # 移除 test_ 前缀和 .py 后缀
            name_part = file_name[5:].replace('.py', '')
            # 尝试匹配模块名（模块名通常是文件名的前缀）
            module_map = cls._build_module_map()
            for module_key in module_map.keys():
                if name_part.startswith(module_key):
                    return module_key
        
        return None
    
    @classmethod
    def extract_module_cn_name_from_path(cls, test_path: str) -> Optional[str]:
        """从测试文件路径中提取模块中文名称
        
        Args:
            test_path: 测试文件路径
            
        Returns:
            模块中文名称（如 '授课教学'），如果无法提取则返回None
        """
        module_key = cls.extract_module_from_path(test_path)
        if module_key:
            return cls.get_module_cn_name(module_key)
        return None
    
    @classmethod
    def get_all_module_keys(cls) -> List[str]:
        """获取所有模块key列表
        
        Returns:
            模块key列表
        """
        return list(cls._build_module_map().keys())

