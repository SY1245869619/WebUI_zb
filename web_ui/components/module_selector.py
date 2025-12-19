"""
应用模块选择组件
"""
from nicegui import ui
import yaml
from pathlib import Path
from typing import Dict, List, Callable


class ModuleSelector:
    """应用模块选择器组件"""
    
    def __init__(self, config_path: str = "config/module_config.yaml"):
        """初始化模块选择器
        
        Args:
            config_path: 模块配置文件路径
        """
        self.config = self._load_config(config_path)
        self.selected_modules: List[str] = []
        self.checkboxes: Dict[str, ui.checkbox] = {}
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if not config_file.exists():
            return {"modules": {}}
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def render(self) -> ui.card:
        """渲染模块选择器
        
        Returns:
            UI卡片组件
        """
        with ui.card().classes('w-full'):
            ui.label('选择要执行的应用模块').classes('text-lg font-bold mb-4')
            
            modules = self.config.get('modules', {})
            for module_key, module_info in modules.items():
                if module_info.get('enabled', True):
                    checkbox = ui.checkbox(
                        module_info['name'],
                        value=False
                    ).classes('mb-2')
                    
                    # 添加描述
                    with ui.row().classes('ml-8 mb-2'):
                        ui.label(module_info.get('description', '')).classes('text-sm text-gray-600')
                    
                    self.checkboxes[module_key] = checkbox
            
            # 全选/取消全选按钮
            with ui.row().classes('mt-4'):
                ui.button('全选', on_click=self.select_all).classes('mr-2')
                ui.button('取消全选', on_click=self.deselect_all)
        
        return self
    
    def select_all(self):
        """全选所有模块"""
        for checkbox in self.checkboxes.values():
            checkbox.value = True
        self.update_selected()
    
    def deselect_all(self):
        """取消全选"""
        for checkbox in self.checkboxes.values():
            checkbox.value = False
        self.update_selected()
    
    def update_selected(self):
        """更新选中的模块列表"""
        self.selected_modules = []
        for module_key, checkbox in self.checkboxes.items():
            if checkbox.value:
                self.selected_modules.append(module_key)
    
    def get_selected_marks(self) -> str:
        """获取选中的模块标记（用于pytest -m）
        
        Returns:
            pytest标记字符串，如 "teaching or exam"
        """
        self.update_selected()
        if not self.selected_modules:
            return ""
        
        modules = self.config.get('modules', {})
        marks = [modules[module_key].get('mark', module_key) for module_key in self.selected_modules]
        return " or ".join(marks)
    
    def get_selected_module_names(self) -> List[str]:
        """获取选中的模块名称列表
        
        Returns:
            模块名称列表
        """
        self.update_selected()
        modules = self.config.get('modules', {})
        return [modules[module_key]['name'] for module_key in self.selected_modules]

