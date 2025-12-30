"""
应用模块选择组件
支持图标显示，网格布局，用例级别选择

@File  : module_selector.py
@Author: shenyuan
"""
from nicegui import ui
import yaml
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


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
        # 存储每个模块选中的测试文件: {module_key: [test_files]}
        self.selected_test_files: Dict[str, List[str]] = {}
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if not config_file.exists():
            return {"modules": {}}
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def render(self) -> ui.card:
        """渲染模块选择器（支持图标显示）
        
        Returns:
            UI卡片组件
        """
        with ui.card().classes('w-full config-section'):
            with ui.column().classes('card-content'):
                ui.label('📦 选择要执行的应用模块').classes('section-title').style('color: #e0e6ed;')
                
                # 使用网格布局显示应用模块（支持图标）
                modules = self.config.get('modules', {})
                
                # 使用响应式网格布局显示应用模块（支持图标，自动换行，兼容更多模块，每行4-5个）
                with ui.column().classes('w-full'):
                    # 使用flex布局，自动换行（兼容更多模块，每行显示4-5个）
                    with ui.row().classes('w-full').style('display: flex; flex-wrap: wrap; gap: 16px;'):
                        for module_key, module_info in modules.items():
                            if module_info.get('enabled', True):
                                # 每个模块作为一个卡片（响应式宽度，每行4-5个，自动换行）
                                # 添加点击事件：点击卡片打开用例选择弹窗
                                # 使用标志防止重复打开
                                dialog_opening = {'value': False}
                                
                                def open_test_case_dialog(module_key=module_key, module_name=module_info['name']):
                                    # 防止重复打开
                                    if dialog_opening['value']:
                                        return
                                    dialog_opening['value'] = True
                                    self._show_test_case_dialog(module_key, module_name)
                                    # 延迟重置标志
                                    ui.timer(0.3, lambda: dialog_opening.update({'value': False}), once=True)
                                
                                with ui.card().classes('module-item-card').style('cursor: pointer; padding: 20px; min-height: 140px; width: calc(20% - 13px); min-width: 140px; max-width: 160px; flex: 0 0 auto; display: flex; flex-direction: column; justify-content: center; position: relative;').on('click', open_test_case_dialog):
                                    with ui.column().classes('items-center gap-3 w-full').style('position: relative;'):
                                        # 图标区域（包含图标和设置按钮）
                                        with ui.column().classes('items-center').style('position: relative;'):
                                            # 图标（优先使用配置文件中的路径，如果不存在则使用占位符）- 支持替换图标
                                            icon_path = module_info.get('icon', '')
                                            if icon_path and Path(icon_path).exists():
                                                ui.image(icon_path).classes('rounded-lg').style('width: 56px; height: 56px; object-fit: contain;')
                                            else:
                                                # 默认图标占位：使用模块名称首字符
                                                first_char = module_info['name'][0] if module_info['name'] else '?'
                                                ui.html(f'<div style="width: 56px; height: 56px; background: linear-gradient(135deg, #0096ff 0%, #00b4ff 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; font-weight: bold; box-shadow: 0 4px 12px rgba(0, 150, 255, 0.4);">{first_char}</div>', sanitize=False)
                                            
                                            # 设置按钮（融合在图标右上角，悬停时显示）
                                            settings_btn = ui.button(
                                                '',
                                                on_click=open_test_case_dialog,
                                                icon='list'
                                            ).style('position: absolute; top: -4px; right: -4px; min-height: 24px; width: 24px; padding: 0; opacity: 0; transition: opacity 0.3s; background: rgba(0, 150, 255, 0.9); border: 1px solid rgba(0, 200, 255, 0.5); z-index: 10;').props('flat dense round')
                                            
                                            # 悬停时显示设置按钮
                                            ui.add_head_html(f'''
                                            <style>
                                                .module-item-card:hover .q-btn[data-module-settings="{module_key}"] {{
                                                    opacity: 1 !important;
                                                }}
                                            </style>
                                            ''')
                                            settings_btn.props(f'data-module-settings="{module_key}"')
                                        
                                        # 模块名称和复选框（默认全选）
                                        with ui.column().classes('items-center gap-2 w-full').style('position: relative; z-index: 2;'):
                                            # 复选框（默认全选）
                                            checkbox = ui.checkbox(
                                                module_info['name'],
                                                value=True  # 默认全选
                                            ).classes('module-checkbox')
                                            
                                            # 为复选框添加点击事件（更新状态）
                                            # 使用默认参数捕获module_key的值，避免闭包问题
                                            def on_checkbox_change(mk=module_key):
                                                """处理模块复选框状态变化"""
                                                # 获取复选框的当前值
                                                cb = self.checkboxes.get(mk)
                                                if not cb:
                                                    return
                                                checkbox_value = cb.value
                                                
                                                # 根据复选框状态更新selected_test_files
                                                all_test_files = self._get_test_files_from_module(mk)
                                                if checkbox_value:
                                                    # 如果选中，全选所有文件
                                                    self.selected_test_files[mk] = all_test_files.copy()
                                                else:
                                                    # 如果取消选中，清空选中的文件
                                                    self.selected_test_files[mk] = []
                                                
                                                # 更新复选框颜色（不改变值，只更新颜色，避免覆盖用户操作）
                                                self._update_module_checkbox_state(mk, update_value=False)
                                            
                                            # 使用默认参数捕获module_key，确保每个处理器绑定正确的模块
                                            checkbox.on('update:modelValue', lambda mk=module_key: on_checkbox_change(mk))
                                            
                                            # 模块描述
                                            ui.label(module_info.get('description', '')).classes('text-xs text-center module-description').style('color: #b0c4de; line-height: 1.4; padding: 0 4px;')
                                            
                                            self.checkboxes[module_key] = checkbox
                                            
                                            # 初始化模块的测试文件选择（默认全选）
                                            if module_key not in self.selected_test_files:
                                                self.selected_test_files[module_key] = []
                                            
                                            # 初始化时设置复选框颜色（默认全选，绿色）
                                            # 使用默认参数捕获module_key的值，避免闭包问题
                                            ui.timer(0.1, lambda mk=module_key: self._update_module_checkbox_state(mk), once=True)
                
                # 全选/取消全选按钮
                with ui.row().classes('w-full mt-6 justify-center'):
                    ui.button('全选', on_click=self.select_all, icon='check_box').classes('mr-2')
                    ui.button('取消全选', on_click=self.deselect_all, icon='check_box_outline_blank')
                
                # 初始化时更新选中状态（默认全选）
                self.update_selected()
                
                # 初始化所有模块的测试文件选择（默认全选）
                for module_key in self.checkboxes.keys():
                    all_test_files = self._get_test_files_from_module(module_key)
                    if module_key not in self.selected_test_files:
                        self.selected_test_files[module_key] = []
                    
                    # 默认全选所有文件
                    if not self.selected_test_files[module_key]:
                        self.selected_test_files[module_key] = all_test_files.copy()
                    
                    # 更新复选框颜色
                    self._update_module_checkbox_state(module_key)
        
        return self
    
    def select_all(self):
        """全选所有模块"""
        for module_key, checkbox in self.checkboxes.items():
            # 同步更新selected_test_files
            all_test_files = self._get_test_files_from_module(module_key)
            self.selected_test_files[module_key] = all_test_files.copy()
            # 设置复选框值并更新颜色
            checkbox.value = True
            # 更新复选框颜色（不改变值，因为已经设置了）
            self._update_module_checkbox_state(module_key, update_value=False)
        self.update_selected()
    
    def deselect_all(self):
        """取消全选"""
        for module_key, checkbox in self.checkboxes.items():
            # 同步更新selected_test_files
            self.selected_test_files[module_key] = []
            # 设置复选框值并更新颜色
            checkbox.value = False
            # 更新复选框颜色（不改变值，因为已经设置了）
            self._update_module_checkbox_state(module_key, update_value=False)
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
    
    def _get_test_files_from_module(self, module_key: str) -> List[str]:
        """获取模块下的所有测试文件（排除模板文件）
        
        Args:
            module_key: 模块键名
        
        Returns:
            测试文件列表，例如 ['test_teaching_basic.py', 'test_teaching_first.py']
        """
        test_files = []
        module_dir = Path(f"test_cases/{module_key}")
        
        if not module_dir.exists():
            return test_files
        
        # 扫描所有 test_*.py 文件，排除模板文件
        for test_file in sorted(module_dir.glob("test_*.py")):
            if test_file.name == "__init__.py":
                continue
            # 排除模板文件
            if test_file.name == "test_template.py":
                continue
            
            # 检查文件是否包含测试用例（简单检查：是否有@pytest.mark标记）
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 如果文件包含@pytest.mark.skip，跳过（模板文件通常有这个标记）
                    if '@pytest.mark.skip' in content and '模板' in content:
                        continue
                    # 如果文件包含测试标记，则认为是有效的测试文件
                    if '@pytest.mark.' in content:
                        test_files.append(test_file.name)
            except Exception:
                # 如果读取失败，也跳过
                continue
        
        return test_files
    
    def _get_file_display_name(self, module_key: str, test_file: str) -> str:
        """从测试文件的类文档字符串中提取中文显示名称
        
        Args:
            module_key: 模块键名
            test_file: 测试文件名
        
        Returns:
            中文显示名称，如果找不到则使用文件名转换
        """
        module_dir = Path(f"test_cases/{module_key}")
        file_path = module_dir / test_file
        
        if not file_path.exists():
            # 如果文件不存在，使用文件名转换
            return self._convert_filename_to_cn(test_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                import re
                
                # 只从类的文档字符串中提取，例如：class TestTeachingBasic: """授课教学基础测试类"""
                class_match = re.search(r'class\s+Test\w+.*?:\s*"""([^"""]+)"""', content, re.DOTALL)
                if class_match:
                    class_doc = class_match.group(1).strip()
                    # 提取中文部分
                    chinese_match = re.search(r'[\u4e00-\u9fff]+[^"""\n]*', class_doc)
                    if chinese_match:
                        chinese_name = chinese_match.group(0).strip()
                        # 清理常见的后缀
                        chinese_name = chinese_name.replace('测试类', '').replace('测试', '').strip()
                        if chinese_name:
                            return chinese_name
        except Exception:
            pass
        
        # 如果找不到，使用文件名转换作为后备方案
        return self._convert_filename_to_cn(test_file)
    
    def _convert_filename_to_cn(self, test_file: str) -> str:
        """将文件名转换为中文（后备方案）
        
        Args:
            test_file: 测试文件名
        
        Returns:
            转换后的中文名称
        """
        file_name_cn = test_file.replace('test_', '').replace('.py', '').replace('_', ' ').title()
        # 如果文件名包含teaching/exercise/exam，替换为中文
        file_name_cn = file_name_cn.replace('Teaching', '授课教学').replace('Exercise', '攻防演练').replace('Exam', '考试测评')
        file_name_cn = file_name_cn.replace('Basic', '基础').replace('First', '首次').replace('Template', '模板')
        return file_name_cn
    
    def _update_module_checkbox_state(self, module_key: str, update_value: bool = True):
        """更新模块复选框状态（根据选中的文件数量）
        
        Args:
            module_key: 模块键名
            update_value: 是否更新复选框的值（默认True，在用户操作时设为False避免覆盖）
        """
        checkbox = self.checkboxes.get(module_key)
        if not checkbox:
            return
        
        # 获取该模块的所有测试文件
        all_test_files = self._get_test_files_from_module(module_key)
        total_count = len(all_test_files)
        
        # 计算选中的文件数量
        selected_count = len(self.selected_test_files.get(module_key, []))
        
        # 更新复选框颜色和状态
        if total_count == 0:
            # 没有测试文件，保持默认状态
            if update_value:
                checkbox.value = False
            try:
                checkbox.props('color="primary"')
            except:
                pass
        elif selected_count == 0:
            # 没有选中任何文件
            if update_value:
                checkbox.value = False
            try:
                checkbox.props('color="primary"')
            except:
                pass
        elif selected_count == total_count:
            # 全部选中 - 绿色
            if update_value:
                checkbox.value = True
            try:
                checkbox.props('color="positive"')
            except:
                pass
        else:
            # 部分选中 - 蓝色
            if update_value:
                checkbox.value = True
            try:
                checkbox.props('color="info"')
            except:
                pass
    
    def _show_test_case_dialog(self, module_key: str, module_name: str):
        """显示测试文件选择对话框（简化版：只显示文件，不显示具体用例）"""
        # 获取该模块的所有测试文件（已排除模板文件）
        all_test_files = self._get_test_files_from_module(module_key)
        
        if not all_test_files:
            # 优雅处理：显示友好的提示对话框
            with ui.dialog() as dialog, ui.card().style('width: 500px; max-width: 90vw; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5);'):
                with ui.column().classes('w-full').style('padding: 24px; text-align: center;'):
                    ui.icon('info', size='48px').style('color: #00d4ff; margin-bottom: 16px;')
                    ui.label(f'{module_name}模块').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 8px;')
                    ui.label('暂无测试文件').classes('text-sm').style('color: #b0c4de; margin-bottom: 20px;')
                    ui.label('请先在该模块目录下创建测试用例文件（test_*.py）').classes('text-xs').style('color: #80a4d4; margin-bottom: 24px;')
                    ui.button('知道了', on_click=dialog.close, color='primary').style('min-height: 36px; padding: 6px 20px;')
            dialog.open()
            return
        
        # 初始化选中状态（如果未初始化，默认全选）
        if module_key not in self.selected_test_files:
            self.selected_test_files[module_key] = all_test_files.copy()
        
        # 使用一个标志来防止重复打开弹窗
        dialog_opening = {'value': True}
        
        with ui.dialog() as dialog, ui.card().style('width: 800px; max-width: 90vw; max-height: 85vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5);'):
            # 外层容器：固定头部，可滚动内容区
            with ui.column().classes('w-full').style('height: 85vh; display: flex; flex-direction: column;'):
                # 固定头部区域
                with ui.column().classes('w-full').style('flex-shrink: 0; padding: 20px; border-bottom: 1px solid rgba(0, 150, 255, 0.3);'):
                    ui.label(f'📋 {module_name} - 选择测试文件').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 12px;')
                    
                    # 说明文字
                    ui.label(f'💡 提示：以下显示的是 {module_name} 模块（test_cases/{module_key}/）下的测试文件，每个文件包含多个测试用例').classes('text-xs').style('color: #80a4de; margin-bottom: 16px;')
                    
                    # 全选/取消全选按钮和确定按钮
                    with ui.row().classes('w-full justify-between items-center'):
                        with ui.row().classes('gap-2'):
                            def select_all_files():
                                """全选所有文件"""
                                self.selected_test_files[module_key] = all_test_files.copy()
                                _update_all_checkboxes()
                                # 直接调用实例方法更新模块复选框状态
                                self._update_module_checkbox_state(module_key)
                            
                            def deselect_all_files():
                                """取消全选所有文件"""
                                self.selected_test_files[module_key] = []
                                _update_all_checkboxes()
                                # 直接调用实例方法更新模块复选框状态
                                self._update_module_checkbox_state(module_key)
                            
                            ui.button('全选', on_click=select_all_files, icon='check_box').style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
                            ui.button('取消全选', on_click=deselect_all_files, icon='check_box_outline_blank').style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
                        
                        def close_dialog_safely():
                            """安全关闭对话框，防止事件冒泡，并更新模块复选框状态"""
                            dialog_opening['value'] = False
                            # 关闭弹窗前，根据弹窗内复选框的实际状态同步到selected_test_files
                            # 确保数据一致性
                            actual_selected = []
                            for test_file, checkbox in file_checkboxes.items():
                                if checkbox.value:
                                    actual_selected.append(test_file)
                            self.selected_test_files[module_key] = actual_selected
                            # 更新模块复选框状态
                            self._update_module_checkbox_state(module_key)
                            ui.timer(0.1, lambda: dialog.close(), once=True)
                        
                        ui.button('确定', on_click=close_dialog_safely, icon='check', color='primary').style('min-height: 32px; padding: 4px 16px; font-size: 12px;')
                
                # 可滚动内容区域
                scroll_container = ui.column().classes('w-full').style(
                    'flex: 1; '
                    'overflow-y: auto; '
                    'overflow-x: hidden; '
                    'padding: 16px 20px; '
                    'overscroll-behavior: contain; '
                    'min-height: 0;'
                )
                
                # 存储所有复选框引用
                file_checkboxes: Dict[str, ui.checkbox] = {}
                
                # 在滚动容器中显示每个测试文件
                with scroll_container:
                    for test_file in sorted(all_test_files):
                        # 从文件中提取中文显示名称
                        file_name_cn = self._get_file_display_name(module_key, test_file)
                        
                        # 检查是否已选中（默认全选）
                        is_selected = test_file in self.selected_test_files.get(module_key, [])
                        
                        def toggle_file(test_file=test_file, checkbox_value=None):
                            """切换文件选中状态"""
                            # 如果传入了checkbox_value，使用它；否则根据当前状态切换
                            if checkbox_value is not None:
                                # 从on_change事件传入的值
                                if checkbox_value:
                                    if test_file not in self.selected_test_files[module_key]:
                                        self.selected_test_files[module_key].append(test_file)
                                else:
                                    if test_file in self.selected_test_files[module_key]:
                                        self.selected_test_files[module_key].remove(test_file)
                            else:
                                # 从卡片点击事件触发，切换状态
                                if test_file not in self.selected_test_files[module_key]:
                                    self.selected_test_files[module_key].append(test_file)
                                else:
                                    self.selected_test_files[module_key].remove(test_file)
                                # 同步复选框状态
                                checkbox.value = test_file in self.selected_test_files[module_key]
                            
                            _update_module_checkbox_color()
                        
                        # 使用默认参数捕获test_file的值，避免闭包问题
                        with ui.card().classes('w-full mb-3').style('background: rgba(10, 22, 40, 0.6); border: 1px solid rgba(0, 150, 255, 0.3); cursor: pointer;').on('click', lambda tf=test_file: toggle_file(tf)):
                            with ui.row().classes('w-full items-center').style('padding: 12px 16px;'):
                                checkbox = ui.checkbox(
                                    f'{file_name_cn}',
                                    value=is_selected,
                                    on_change=lambda e, tf=test_file: toggle_file(tf, e.value)
                                ).style('font-size: 14px; color: #e0e6ed; flex: 1;')
                                
                                # 显示文件名（小字）
                                ui.label(f'({test_file})').classes('text-xs').style('color: #80a4de; margin-left: 8px;')
                                
                                file_checkboxes[test_file] = checkbox
                
                def _update_all_checkboxes():
                    """更新所有复选框状态"""
                    selected_files = self.selected_test_files.get(module_key, [])
                    for test_file, checkbox in file_checkboxes.items():
                        checkbox.value = test_file in selected_files
                
                def _update_module_checkbox_color():
                    """更新模块复选框颜色"""
                    self._update_module_checkbox_state(module_key)
        
        # 打开对话框
        dialog_opening['value'] = True
        dialog.open()
    
    def get_selected_test_cases(self) -> Dict[str, List[str]]:
        """获取选中的测试文件（用于pytest执行）
        
        Returns:
            {module_key: [test_paths]}，例如 {'teaching': ['test_cases/teaching/test_teaching_basic.py']}
        """
        test_paths = {}
        
        for module_key, test_files in self.selected_test_files.items():
            if not test_files:
                continue
            
            if module_key not in test_paths:
                test_paths[module_key] = []
            
            # 直接使用文件路径，不指定具体用例
            for test_file in test_files:
                test_path = f"test_cases/{module_key}/{test_file}"
                test_paths[module_key].append(test_path)
        
        return test_paths

