"""
元素库管理器
集中管理页面元素定位器

@File  : element_library.py
@Author: shenyuan
"""
import yaml
import json
from pathlib import Path
from typing import Dict, Optional, List


class ElementLibrary:
    """元素库管理器"""
    
    def __init__(self, library_dir: str = "element_library"):
        """初始化元素库
        
        Args:
            library_dir: 元素库目录
        """
        self.library_dir = Path(library_dir)
        self.library_dir.mkdir(exist_ok=True)
        self.elements: Dict[str, Dict] = {}
        self._load_library()
    
    def _load_library(self):
        """加载元素库"""
        library_file = self.library_dir / "elements.yaml"
        if library_file.exists():
            with open(library_file, 'r', encoding='utf-8') as f:
                self.elements = yaml.safe_load(f) or {}
        else:
            # 创建默认元素库文件
            self.elements = {}
            self._save_library()
    
    def add_element(self, page: str, name: str, selector: str, description: str = ""):
        """添加元素
        
        Args:
            page: 页面名称
            name: 元素名称
            selector: 元素选择器
            description: 元素描述
        """
        if page not in self.elements:
            self.elements[page] = {}
        
        self.elements[page][name] = {
            'selector': selector,
            'description': description
        }
        self._save_library()
    
    def get_element(self, page: str, name: str) -> Optional[str]:
        """获取元素选择器
        
        Args:
            page: 页面名称
            name: 元素名称
            
        Returns:
            元素选择器，如果不存在返回None
        """
        return self.elements.get(page, {}).get(name, {}).get('selector')
    
    def get_page_elements(self, page: str) -> Dict[str, Dict]:
        """获取页面的所有元素
        
        Args:
            page: 页面名称
            
        Returns:
            元素字典
        """
        return self.elements.get(page, {})
    
    def remove_element(self, page: str, name: str) -> bool:
        """删除元素
        
        Args:
            page: 页面名称
            name: 元素名称
            
        Returns:
            是否删除成功
        """
        if page in self.elements and name in self.elements[page]:
            del self.elements[page][name]
            self._save_library()
            return True
        return False
    
    def get_all_pages(self) -> List[str]:
        """获取所有页面名称
        
        Returns:
            页面名称列表
        """
        return list(self.elements.keys())
    
    def export_to_json(self, output_path: str):
        """导出为JSON格式
        
        Args:
            output_path: 输出路径
        """
        output_path = Path(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.elements, f, ensure_ascii=False, indent=2)
    
    def import_from_json(self, input_path: str):
        """从JSON导入
        
        Args:
            input_path: 输入路径
        """
        input_path = Path(input_path)
        with open(input_path, 'r', encoding='utf-8') as f:
            self.elements = json.load(f)
        self._save_library()
    
    def _save_library(self):
        """保存元素库到文件"""
        library_file = self.library_dir / "elements.yaml"
        with open(library_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.elements, f, allow_unicode=True, default_flow_style=False)

