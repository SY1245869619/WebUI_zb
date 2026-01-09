"""
高级功能管理组件
包含测试调度、环境管理、数据管理等功能入口

@File  : advanced_features.py
@Author: shenyuan
"""
from nicegui import ui
from pathlib import Path
from datetime import datetime
import yaml

# 可选依赖导入，如果缺失则功能不可用
try:
    from core.test_scheduler import TestScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    TestScheduler = None

try:
    from core.environment_manager import EnvironmentManager
    ENV_MANAGER_AVAILABLE = True
except ImportError:
    ENV_MANAGER_AVAILABLE = False
    EnvironmentManager = None

try:
    from core.test_data_manager import TestDataManager
    DATA_MANAGER_AVAILABLE = True
except ImportError:
    DATA_MANAGER_AVAILABLE = False
    TestDataManager = None

try:
    from core.element_library import ElementLibrary
    ELEMENT_LIB_AVAILABLE = True
except ImportError:
    ELEMENT_LIB_AVAILABLE = False
    ElementLibrary = None

try:
    from core.test_plan_manager import TestPlanManager
    PLAN_MANAGER_AVAILABLE = True
except ImportError:
    PLAN_MANAGER_AVAILABLE = False
    TestPlanManager = None

try:
    from core.test_result_analyzer import TestResultAnalyzer
    from core.db_client import DBClient
    RESULT_ANALYZER_AVAILABLE = True
except ImportError:
    RESULT_ANALYZER_AVAILABLE = False
    TestResultAnalyzer = None
    DBClient = None


class AdvancedFeaturesPanel:
    """高级功能面板"""
    
    def __init__(self):
        """初始化高级功能面板"""
        # 初始化各个管理器（如果可用）
        self.scheduler = TestScheduler() if SCHEDULER_AVAILABLE else None
        self.env_manager = EnvironmentManager() if ENV_MANAGER_AVAILABLE else None
        self.data_manager = TestDataManager() if DATA_MANAGER_AVAILABLE else None
        self.element_lib = ElementLibrary() if ELEMENT_LIB_AVAILABLE else None
        self.plan_manager = TestPlanManager() if PLAN_MANAGER_AVAILABLE else None
        
        # 初始化结果分析器（如果数据库可用）
        self.result_analyzer = None
        if RESULT_ANALYZER_AVAILABLE:
            try:
                db_client = DBClient()
                db_client.connect()
                self.result_analyzer = TestResultAnalyzer(db_client)
            except:
                try:
                    self.result_analyzer = TestResultAnalyzer()
                except:
                    pass
        
        # 执行配置（重试次数和超时时间）
        self.config_path = Path("config/settings.yaml")
        self.retry_count = 2  # 默认重试次数
        self.timeout_seconds = 30  # 默认超时时间（秒）
        self.retry_count_input = None
        self.timeout_input = None
        # 加载保存的配置
        self._load_execution_config()
    
    def render(self):
        """渲染高级功能面板"""
        with ui.card().classes('w-full config-section'):
            with ui.column().classes('card-content').style('padding: 32px 40px;'):
                ui.label('高级功能').classes('section-title').style('color: #e0e6ed; margin-bottom: 24px;')
                
                # 功能按钮网格
                with ui.grid(columns=3).classes('w-full gap-4'):
                    # 测试调度
                    ui.button(
                        '测试调度',
                        icon='schedule',
                        on_click=self.show_scheduler
                    ).style('min-height: 80px; font-size: 14px;')
                    
                    # 环境管理
                    ui.button(
                        '环境管理',
                        icon='public',
                        on_click=self.show_environment_manager
                    ).style('min-height: 80px; font-size: 14px;')
                    
                    # 测试数据
                    ui.button(
                        '测试数据',
                        icon='table_chart',
                        on_click=self.show_data_manager
                    ).style('min-height: 80px; font-size: 14px;')
                    
                    # 元素库
                    ui.button(
                        '元素库',
                        icon='category',
                        on_click=self.show_element_library
                    ).style('min-height: 80px; font-size: 14px;')
                    
                    # 测试计划
                    ui.button(
                        '测试计划',
                        icon='assignment',
                        on_click=self.show_test_plans
                    ).style('min-height: 80px; font-size: 14px;')
                    
                    # 趋势分析
                    ui.button(
                        '趋势分析',
                        icon='trending_up',
                        on_click=self.show_trend_analysis
                    ).style('min-height: 80px; font-size: 14px;')
                    
                    # 执行配置（重试次数和超时时间）
                    ui.button(
                        '执行配置',
                        icon='settings',
                        on_click=self.show_execution_config
                    ).style('min-height: 80px; font-size: 14px;')
    
    def show_scheduler(self):
        """显示测试调度管理"""
        if not self.scheduler:
            ui.notify('测试调度功能需要安装 APScheduler，请运行: pip install APScheduler', type='warning')
            return
        
        jobs = self.scheduler.get_all_jobs()
        
        with ui.dialog() as dialog, ui.card().style('width: 900px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; box-sizing: border-box;'):
            with ui.column().classes('w-full').style('padding: 24px; overflow-y: auto; flex: 1; min-height: 0; box-sizing: border-box; width: 100%; max-width: 100%;'):
                ui.label('测试调度管理').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 20px;')
                
                # 添加新任务按钮
                with ui.row().classes('w-full justify-end').style('margin-bottom: 16px;'):
                    ui.button('添加调度任务', icon='add', on_click=self._add_schedule_task).style('min-height: 36px;')
                
                # 任务列表
                if jobs:
                    with ui.column().classes('w-full').style('max-height: calc(90vh - 200px); overflow-y: auto; gap: 12px; padding-right: 8px;'):
                        for job in jobs:
                            with ui.card().classes('w-full').style('background: rgba(10, 22, 40, 0.6); border: 1px solid rgba(0, 150, 255, 0.3); padding: 16px; border-radius: 8px; box-shadow: none;'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    with ui.column().classes('flex-1'):
                                        ui.label(job['name']).style('color: #e0e6ed; font-size: 14px; font-weight: 500; margin-bottom: 4px;')
                                        ui.label(f"触发器: {job['trigger']}").style('color: #90caf9; font-size: 12px;')
                                        if job['next_run']:
                                            ui.label(f"下次执行: {job['next_run']}").style('color: #90caf9; font-size: 12px;')
                                    
                                    with ui.row().classes('gap-2'):
                                        ui.button('删除', icon='delete', color='red', on_click=lambda jid=job['id']: self._delete_schedule(jid, dialog)).style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
                else:
                    ui.label('暂无调度任务').style('color: #90caf9; text-align: center; padding: 40px;')
                
                with ui.row().classes('w-full justify-end').style('margin-top: 20px;'):
                    ui.button('关闭', on_click=dialog.close, icon='close').style('min-height: 36px;')
        
        dialog.open()
    
    def _add_schedule_task(self):
        """添加调度任务"""
        if not self.scheduler:
            ui.notify('测试调度功能需要安装 APScheduler', type='warning')
            return
        
        # 获取模块列表（从module_selector获取）
        modules = ['teaching', 'exercise', 'exam']
        module_names = {'teaching': '授课教学', 'exercise': '攻防演练', 'exam': '考试测评'}
        
        with ui.dialog() as add_dialog, ui.card().classes('schedule-task-dialog').style('width: 800px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; box-sizing: border-box;'):
            # 只针对这个弹窗的输入框样式
            ui.add_head_html('''
            <style>
                /* 只针对添加调度任务弹窗的输入框 - 文案垂直居中，增加高度 */
                .schedule-task-dialog .q-field__control,
                .schedule-task-dialog .q-input__control {
                    min-height: 64px !important;
                    display: flex !important;
                    align-items: center !important;
                }
                .schedule-task-dialog .q-field__native,
                .schedule-task-dialog .q-input__native {
                    min-height: 64px !important;
                    padding: 16px !important;
                    line-height: 1.5 !important;
                    display: flex !important;
                    align-items: center !important;
                    overflow: visible !important;
                }
                /* 任务名称框高度调高到72px，确保文案完全可见 */
                .schedule-task-dialog .task-name-field .q-field__control,
                .schedule-task-dialog .task-name-field .q-input__control {
                    min-height: 72px !important;
                }
                .schedule-task-dialog .task-name-field .q-field__native,
                .schedule-task-dialog .task-name-field .q-input__native {
                    min-height: 72px !important;
                    padding: 18px 16px !important;
                    overflow: visible !important;
                }
                /* Cron表达式框高度调高到72px */
                .schedule-task-dialog .cron-input-field .q-field__control,
                .schedule-task-dialog .cron-input-field .q-input__control {
                    min-height: 72px !important;
                }
                .schedule-task-dialog .cron-input-field .q-field__native,
                .schedule-task-dialog .cron-input-field .q-input__native {
                    min-height: 72px !important;
                    padding: 18px 16px !important;
                }
                /* 间隔小时数框优化 */
                .schedule-task-dialog .interval-hours-field .q-field__control,
                .schedule-task-dialog .interval-hours-field .q-input__control {
                    min-height: 64px !important;
                }
                .schedule-task-dialog .interval-hours-field .q-field__native,
                .schedule-task-dialog .interval-hours-field .q-input__native {
                    min-height: 64px !important;
                    padding: 16px !important;
                }
            </style>
            ''')
            with ui.column().classes('w-full').style('padding: 24px; overflow-y: auto; flex: 1; min-height: 0; box-sizing: border-box; width: 100%; max-width: 100%;'):
                ui.label('添加调度任务').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 20px;')
                
                # 任务名称 - 调高框的高度，确保文案完全可见
                with ui.column().classes('task-name-field').style('width: 100%; margin-bottom: 20px;'):
                    task_name_input = ui.input('任务名称', placeholder='例如：每日回归测试').style('width: 100%;')
                
                # 选择模块
                selected_modules = {}
                ui.label('选择执行模块：').style('color: #e0e6ed; margin-bottom: 8px;')
                with ui.column().style('margin-bottom: 16px;'):
                    for module in modules:
                        checkbox = ui.checkbox(module_names.get(module, module), value=False)
                        selected_modules[module] = checkbox
                
                # 调度方式
                schedule_type = ui.radio(['Cron表达式', '间隔触发'], value='Cron表达式').props('inline').style('margin-bottom: 16px;')
                
                # Cron表达式输入 - 调高框的高度
                with ui.column().classes('cron-input-field').style('width: 100%; margin-bottom: 16px;'):
                    cron_input = ui.input('Cron表达式', placeholder='例如：0 9 * * * (每天9点)', value='0 9 * * *').style('width: 100%;')
                
                # Cron表达式说明（多举例子）
                with ui.column().style('background: rgba(10, 22, 40, 0.4); padding: 12px; border-radius: 8px; margin-bottom: 16px; box-sizing: border-box; width: 100%; max-width: 100%;'):
                    ui.label('Cron格式说明：分 时 日 月 周（5个字段，用空格分隔）').style('color: #90caf9; font-size: 12px; font-weight: 500; margin-bottom: 8px; word-break: break-word;')
                    with ui.column().style('gap: 6px;'):
                        ui.label('• 0 9 * * * → 每天上午9点执行').style('color: #b0c4de; font-size: 11px; word-break: break-word; padding-left: 8px;')
                        ui.label('• 0 14 * * * → 每天下午2点执行').style('color: #b0c4de; font-size: 11px; word-break: break-word; padding-left: 8px;')
                        ui.label('• 0 9 * * 1 → 每周一上午9点执行').style('color: #b0c4de; font-size: 11px; word-break: break-word; padding-left: 8px;')
                        ui.label('• 0 9 1 * * → 每月1号上午9点执行').style('color: #b0c4de; font-size: 11px; word-break: break-word; padding-left: 8px;')
                        ui.label('• */30 * * * * → 每30分钟执行一次').style('color: #b0c4de; font-size: 11px; word-break: break-word; padding-left: 8px;')
                        ui.label('• 0 9-17 * * 1-5 → 工作日上午9点到下午5点，每小时执行').style('color: #b0c4de; font-size: 11px; word-break: break-word; padding-left: 8px;')
                
                # 间隔触发输入 - 调长框的长度，与任务名称一致
                with ui.column().classes('interval-hours-field').style('margin-bottom: 16px; width: 100%;'):
                    interval_hours = ui.number('间隔小时数', value=2, min=1, max=24).style('width: 100%;')
                
                def save_schedule():
                    name = task_name_input.value.strip()
                    if not name:
                        ui.notify('请输入任务名称', type='warning')
                        return
                    
                    selected = [m for m, cb in selected_modules.items() if cb.value]
                    if not selected:
                        ui.notify('请至少选择一个模块', type='warning')
                        return
                    
                    try:
                        if schedule_type.value == 'Cron表达式':
                            cron = cron_input.value.strip()
                            if not cron:
                                ui.notify('请输入Cron表达式', type='warning')
                                return
                            job_id = self.scheduler.add_schedule(name, selected, cron=cron)
                        else:
                            hours = int(interval_hours.value) if interval_hours.value else 2
                            job_id = self.scheduler.add_schedule(name, selected, interval={'hours': hours})
                        
                        ui.notify('调度任务已添加', type='positive')
                        add_dialog.close()
                        ui.timer(0.3, lambda: self.show_scheduler(), once=True)
                    except Exception as e:
                        ui.notify(f'添加失败: {str(e)}', type='negative')
                
                with ui.row().classes('w-full justify-end').style('margin-top: 20px; gap: 12px;'):
                    ui.button('取消', on_click=add_dialog.close).style('min-height: 36px;')
                    ui.button('保存', on_click=save_schedule, color='primary').style('min-height: 36px;')
        
        add_dialog.open()
    
    def _delete_schedule(self, job_id: str, dialog):
        """删除调度任务"""
        if self.scheduler.remove_schedule(job_id):
            ui.notify('调度任务已删除', type='positive')
            dialog.close()
            ui.timer(0.3, lambda: self.show_scheduler(), once=True)
        else:
            ui.notify('删除失败', type='negative')
    
    def show_environment_manager(self):
        """显示环境管理"""
        if not self.env_manager:
            ui.notify('环境管理功能不可用', type='warning')
            return
        
        envs = self.env_manager.get_all_environments()
        current_env = self.env_manager.current_env
        
        with ui.dialog() as dialog, ui.card().style('width: 900px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; box-sizing: border-box;'):
            with ui.column().classes('w-full').style('padding: 24px; overflow-y: auto; flex: 1; min-height: 0; box-sizing: border-box; width: 100%; max-width: 100%;'):
                ui.label('环境管理').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 20px;')
                
                # 添加环境按钮
                with ui.row().classes('w-full justify-end').style('margin-bottom: 16px;'):
                    ui.button('添加环境', icon='add', on_click=lambda: self._add_environment(dialog)).style('min-height: 36px;')
                
                # 环境列表（可滚动）
                with ui.column().classes('w-full').style('max-height: calc(90vh - 200px); overflow-y: auto; gap: 12px; padding-right: 8px;'):
                    if envs:
                        for env_name, env_config in envs.items():
                            is_current = env_name == current_env
                            with ui.card().classes('w-full').style(f'background: rgba(10, 22, 40, 0.6); border: 1px solid {"rgba(0, 255, 150, 0.5)" if is_current else "rgba(0, 150, 255, 0.3)"}; padding: 16px; border-radius: 8px; box-shadow: none;'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    with ui.column().classes('flex-1').style('min-width: 0; width: 100%; max-width: 100%; box-sizing: border-box; overflow: hidden;'):
                                        with ui.row().classes('gap-2 items-center').style('margin-bottom: 4px; flex-wrap: wrap; width: 100%; max-width: 100%; box-sizing: border-box;'):
                                            if is_current:
                                                ui.label('✓ 当前环境').style('color: #00ff88; font-size: 11px; padding: 2px 8px; background: rgba(0, 255, 150, 0.2); border-radius: 4px; white-space: nowrap;')
                                            ui.label(env_config.get('name', env_name)).style('color: #e0e6ed; font-size: 14px; font-weight: 500; word-break: break-word; overflow-wrap: break-word; white-space: normal; width: 100%; max-width: 100%; box-sizing: border-box;')
                                        ui.label(f"Base URL: {env_config.get('base_url', 'N/A')}").style('color: #90caf9; font-size: 12px; word-break: break-word; overflow-wrap: break-word; white-space: normal; width: 100%; max-width: 100%; box-sizing: border-box;')
                                        if env_config.get('login_url'):
                                            ui.label(f"登录URL: {env_config.get('login_url', 'N/A')}").style('color: #90caf9; font-size: 12px; word-break: break-word; overflow-wrap: break-word; white-space: normal; width: 100%; max-width: 100%; box-sizing: border-box;')
                                    
                                    with ui.row().classes('gap-2').style('flex-shrink: 0;'):
                                        if not is_current:
                                            ui.button('切换', icon='swap_horiz', on_click=lambda en=env_name: self._switch_environment(en, dialog)).style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
                                        if env_name != 'default':
                                            ui.button('删除', icon='delete', color='red', on_click=lambda en=env_name: self._delete_environment(en, dialog)).style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
                    else:
                        ui.label('暂无环境配置').style('color: #90caf9; text-align: center; padding: 40px;')
                
                with ui.row().classes('w-full justify-end').style('margin-top: 20px;'):
                    ui.button('关闭', on_click=dialog.close, icon='close').style('min-height: 36px;')
        
        dialog.open()
    
    def _switch_environment(self, env_name: str, dialog):
        """切换环境"""
        if self.env_manager.set_environment(env_name):
            ui.notify(f'已切换到环境: {env_name}', type='positive')
            dialog.close()
            ui.timer(0.3, lambda: self.show_environment_manager(), once=True)
        else:
            ui.notify('切换失败', type='negative')
    
    def _add_environment(self, dialog):
        """添加环境"""
        with ui.dialog() as add_dialog, ui.card().style('width: 800px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; box-sizing: border-box;'):
            with ui.column().classes('w-full').style('padding: 24px; overflow-y: auto; flex: 1; min-height: 0; box-sizing: border-box; width: 100%; max-width: 100%;'):
                ui.label('添加环境').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 20px;')
                
                env_name_input = ui.input('环境名称（英文ID）', placeholder='例如：test、prod', value='').style('width: 100%; margin-bottom: 16px;')
                env_display_name = ui.input('环境显示名称', placeholder='例如：测试环境', value='').style('width: 100%; margin-bottom: 16px;')
                base_url_input = ui.input('Base URL', placeholder='http://10.70.70.96/Shenyuan_9', value='').style('width: 100%; margin-bottom: 16px;')
                login_url_input = ui.input('登录URL', placeholder='http://10.70.70.96/Shenyuan_9#/login', value='').style('width: 100%; margin-bottom: 16px;')
                username_input = ui.input('用户名', placeholder='Shenyuan_9', value='').style('width: 100%; margin-bottom: 16px;')
                password_input = ui.input('密码', placeholder='密码', password=True).style('width: 100%; margin-bottom: 16px;')
                
                def save_env():
                    name = env_name_input.value.strip()
                    if not name:
                        ui.notify('请输入环境名称', type='warning')
                        return
                    
                    if name == 'default':
                        ui.notify('不能使用default作为环境名称', type='warning')
                        return
                    
                    config = {
                        'name': env_display_name.value.strip() or name,
                        'base_url': base_url_input.value.strip(),
                        'login_url': login_url_input.value.strip(),
                        'username': username_input.value.strip(),
                        'password': password_input.value.strip()
                    }
                    
                    if self.env_manager.add_environment(name, config):
                        ui.notify('环境已添加', type='positive')
                        add_dialog.close()
                        dialog.close()
                        ui.timer(0.3, lambda: self.show_environment_manager(), once=True)
                    else:
                        ui.notify('添加失败', type='negative')
                
                with ui.row().classes('w-full justify-end').style('margin-top: 20px; gap: 12px;'):
                    ui.button('取消', on_click=add_dialog.close).style('min-height: 36px;')
                    ui.button('保存', on_click=save_env, color='primary').style('min-height: 36px;')
        
        add_dialog.open()
    
    def _delete_environment(self, env_name: str, dialog):
        """删除环境"""
        if self.env_manager.remove_environment(env_name):
            ui.notify('环境已删除', type='positive')
            dialog.close()
            ui.timer(0.3, lambda: self.show_environment_manager(), once=True)
        else:
            ui.notify('删除失败', type='negative')
    
    def show_data_manager(self):
        """显示测试数据管理"""
        if not self.data_manager:
            ui.notify('测试数据管理功能不可用', type='warning')
            return
        
        files = self.data_manager.get_data_files()
        
        with ui.dialog() as dialog, ui.card().style('width: 900px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; box-sizing: border-box;'):
            with ui.column().classes('w-full').style('padding: 24px; overflow-y: auto; flex: 1; min-height: 0; box-sizing: border-box; width: 100%; max-width: 100%;'):
                ui.label('测试数据管理').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 12px;')
                ui.label('用于数据驱动测试，支持CSV/JSON/YAML格式。数据文件存放在 test_data/ 目录。').style('color: #90caf9; font-size: 12px; margin-bottom: 20px; word-break: break-word; overflow-wrap: break-word; white-space: normal; line-height: 1.6; width: 100%; max-width: 100%; box-sizing: border-box;')
                
                # 创建示例数据按钮
                with ui.row().classes('w-full justify-end').style('margin-bottom: 16px;'):
                    ui.button('📝 创建示例数据', icon='add', on_click=self._create_sample_data).style('min-height: 36px;')
                
                if files:
                    with ui.column().classes('w-full').style('max-height: calc(90vh - 200px); overflow-y: auto; gap: 12px; padding-right: 8px;'):
                        for file_info in files:
                            with ui.card().classes('w-full').style('background: rgba(10, 22, 40, 0.6); border: 1px solid rgba(0, 150, 255, 0.3); padding: 16px; border-radius: 8px; box-shadow: none;'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    with ui.column().classes('flex-1'):
                                        ui.label(file_info['name']).style('color: #e0e6ed; font-size: 14px; font-weight: 500; margin-bottom: 4px;')
                                        ui.label(f"类型: {file_info['type']} | 大小: {file_info['size']} bytes").style('color: #90caf9; font-size: 12px;')
                                    
                                    with ui.row().classes('gap-2'):
                                        ui.button('查看', icon='visibility', on_click=lambda fi=file_info: self._view_data_file(fi)).style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
                else:
                    with ui.column().classes('w-full items-center').style('padding: 40px;'):
                        ui.label('暂无数据文件').style('color: #90caf9; text-align: center; margin-bottom: 16px;')
                        ui.label('点击"创建示例数据"按钮创建示例文件，或手动在 test_data/ 目录添加CSV/JSON/YAML文件').style('color: #b0c4de; font-size: 12px; text-align: center;')
                
                with ui.row().classes('w-full justify-end').style('margin-top: 20px;'):
                    ui.button('关闭', on_click=dialog.close, icon='close').style('min-height: 36px;')
        
        dialog.open()
    
    def _create_sample_data(self):
        """创建示例数据"""
        try:
            # 创建示例CSV
            sample_csv = [
                {'username': 'user1', 'password': 'pass1', 'expected_result': 'success'},
                {'username': 'user2', 'password': 'pass2', 'expected_result': 'success'},
                {'username': 'invalid', 'password': 'wrong', 'expected_result': 'failed'}
            ]
            self.data_manager.save_csv(sample_csv, 'sample_users.csv')
            
            # 创建示例JSON
            sample_json = [
                {'test_case': 'login_test', 'url': 'http://example.com/login', 'action': 'click'},
                {'test_case': 'search_test', 'url': 'http://example.com/search', 'action': 'type'}
            ]
            self.data_manager.save_json(sample_json, 'sample_test_data.json')
            
            ui.notify('示例数据已创建在 test_data/ 目录', type='positive')
            ui.timer(0.3, lambda: self.show_data_manager(), once=True)
        except Exception as e:
            ui.notify(f'创建失败: {str(e)}', type='negative')
    
    def _view_data_file(self, file_info: dict):
        """查看数据文件"""
        try:
            file_path = Path(file_info['full_path'])
            if not file_path.exists():
                ui.notify('文件不存在', type='negative')
                return
            
            # 根据文件类型加载内容
            if file_info['type'] == 'csv':
                data = self.data_manager.load_csv(file_info['path'])
            elif file_info['type'] == 'json':
                data = self.data_manager.load_json(file_info['path'])
            elif file_info['type'] in ['yaml', 'yml']:
                data = self.data_manager.load_yaml(file_info['path'])
            else:
                ui.notify('不支持的文件类型', type='warning')
                return
            
            # 显示数据内容
            with ui.dialog() as view_dialog, ui.card().style('width: 900px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; box-sizing: border-box;'):
                with ui.column().classes('w-full').style('padding: 24px; overflow-y: auto; flex: 1; min-height: 0; box-sizing: border-box; width: 100%; max-width: 100%;'):
                    ui.label(f'查看数据文件: {file_info["name"]}').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 20px;')
                    
                    # 显示数据（最多显示20条）
                    display_data = data[:20]
                    if len(data) > 20:
                        ui.label(f'共 {len(data)} 条数据，仅显示前20条').style('color: #90caf9; font-size: 12px; margin-bottom: 12px;')
                    
                    with ui.column().classes('w-full').style('max-height: calc(90vh - 250px); overflow-y: auto; gap: 8px; padding-right: 8px;'):
                        for i, item in enumerate(display_data, 1):
                            with ui.card().classes('w-full').style('background: rgba(10, 22, 40, 0.6); border: 1px solid rgba(0, 150, 255, 0.3); padding: 12px; border-radius: 8px; box-shadow: none;'):
                                ui.label(f'数据 {i}:').style('color: #e0e6ed; font-size: 12px; font-weight: 500; margin-bottom: 4px;')
                                ui.label(str(item)).style('color: #90caf9; font-size: 11px; word-break: break-word; overflow-wrap: break-word; white-space: normal; font-family: monospace;')
                    
                    with ui.row().classes('w-full justify-end').style('margin-top: 20px;'):
                        ui.button('关闭', on_click=view_dialog.close, icon='close').style('min-height: 36px;')
            
            view_dialog.open()
        except Exception as e:
            ui.notify(f'查看文件失败: {str(e)}', type='negative')
    
    def show_element_library(self):
        """显示元素库管理"""
        if not self.element_lib:
            ui.notify('元素库管理功能不可用', type='warning')
            return
        
        pages = self.element_lib.get_all_pages()
        
        with ui.dialog() as dialog, ui.card().style('width: 900px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; box-sizing: border-box;'):
            with ui.column().classes('w-full').style('padding: 24px; overflow-y: auto; flex: 1; min-height: 0; box-sizing: border-box; width: 100%; max-width: 100%;'):
                ui.label('元素库管理').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 12px;')
                ui.label('集中管理页面元素定位器，便于维护和复用。元素库文件：element_library/elements.yaml').style('color: #90caf9; font-size: 12px; margin-bottom: 20px; word-break: break-word; overflow-wrap: break-word; white-space: normal; line-height: 1.6; width: 100%; max-width: 100%; box-sizing: border-box;')
                
                # 添加元素按钮
                with ui.row().classes('w-full justify-end').style('margin-bottom: 16px;'):
                    ui.button('添加元素', icon='add', on_click=self._add_element).style('min-height: 36px;')
                
                if pages:
                    with ui.column().classes('w-full').style('max-height: calc(90vh - 200px); overflow-y: auto; gap: 12px; padding-right: 8px;'):
                        for page in pages:
                            elements = self.element_lib.get_page_elements(page)
                            with ui.card().classes('w-full').style('background: rgba(10, 22, 40, 0.6); border: 1px solid rgba(0, 150, 255, 0.3); padding: 16px; border-radius: 8px; box-shadow: none;'):
                                with ui.row().classes('w-full items-center justify-between').style('margin-bottom: 8px;'):
                                    ui.label(f"页面: {page} ({len(elements)} 个元素)").style('color: #e0e6ed; font-size: 14px; font-weight: 500;')
                                    ui.button('删除页面', icon='delete', color='red', on_click=lambda p=page: self._delete_page(p, dialog)).style('min-height: 28px; padding: 2px 8px; font-size: 11px;')
                                for elem_name, elem_info in elements.items():
                                    with ui.row().classes('w-full items-center justify-between').style('margin-left: 16px; margin-bottom: 4px;'):
                                        ui.label(f"{elem_name}: {elem_info.get('selector', '')}").style('color: #90caf9; font-size: 12px; word-break: break-word; overflow-wrap: break-word; white-space: normal; width: 100%; max-width: 100%; box-sizing: border-box;')
                                        ui.button('删除', icon='delete', color='red', on_click=lambda p=page, e=elem_name: self._delete_element(p, e, dialog)).style('min-height: 24px; padding: 2px 8px; font-size: 11px;')
                else:
                    with ui.column().classes('w-full items-center').style('padding: 40px;'):
                        ui.label('暂无元素数据').style('color: #90caf9; text-align: center; margin-bottom: 16px;')
                        ui.label('点击"添加元素"按钮添加元素，或手动编辑 element_library/elements.yaml 文件').style('color: #b0c4de; font-size: 12px; text-align: center;')
                
                with ui.row().classes('w-full justify-end').style('margin-top: 20px;'):
                    ui.button('关闭', on_click=dialog.close, icon='close').style('min-height: 36px;')
        
        dialog.open()
    
    def _add_element(self):
        """添加元素"""
        with ui.dialog() as add_dialog, ui.card().style('width: 800px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; box-sizing: border-box;'):
            with ui.column().classes('w-full').style('padding: 24px; overflow-y: auto; flex: 1; min-height: 0; box-sizing: border-box; width: 100%; max-width: 100%;'):
                ui.label('添加元素').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 20px;')
                
                page_input = ui.input('页面名称', placeholder='例如：login_page', value='').style('width: 100%; margin-bottom: 16px;')
                name_input = ui.input('元素名称', placeholder='例如：username_input', value='').style('width: 100%; margin-bottom: 16px;')
                selector_input = ui.input('元素选择器', placeholder='例如：input[name="username"]', value='').style('width: 100%; margin-bottom: 16px;')
                desc_input = ui.input('元素描述（可选）', placeholder='例如：用户名输入框', value='').style('width: 100%; margin-bottom: 16px;')
                
                def save_element():
                    page = page_input.value.strip()
                    name = name_input.value.strip()
                    selector = selector_input.value.strip()
                    
                    if not all([page, name, selector]):
                        ui.notify('请填写完整信息', type='warning')
                        return
                    
                    self.element_lib.add_element(page, name, selector, desc_input.value.strip())
                    ui.notify('元素已添加', type='positive')
                    add_dialog.close()
                    ui.timer(0.3, lambda: self.show_element_library(), once=True)
                
                with ui.row().classes('w-full justify-end').style('margin-top: 20px; gap: 12px;'):
                    ui.button('取消', on_click=add_dialog.close).style('min-height: 36px;')
                    ui.button('保存', on_click=save_element, color='primary').style('min-height: 36px;')
        
        add_dialog.open()
    
    def _delete_element(self, page: str, element: str, dialog):
        """删除元素"""
        if self.element_lib.remove_element(page, element):
            ui.notify('元素已删除', type='positive')
            dialog.close()
            ui.timer(0.3, lambda: self.show_element_library(), once=True)
        else:
            ui.notify('删除失败', type='negative')
    
    def _delete_page(self, page: str, dialog):
        """删除页面（删除页面下所有元素）"""
        elements = self.element_lib.get_page_elements(page)
        for elem_name in list(elements.keys()):
            self.element_lib.remove_element(page, elem_name)
        ui.notify('页面已删除', type='positive')
        dialog.close()
        ui.timer(0.3, lambda: self.show_element_library(), once=True)
    
    def show_test_plans(self):
        """显示测试计划管理"""
        if not self.plan_manager:
            ui.notify('测试计划管理功能不可用', type='warning')
            return
        
        plans = self.plan_manager.get_all_plans()
        
        with ui.dialog() as dialog, ui.card().style('width: 900px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; box-sizing: border-box;'):
            with ui.column().classes('w-full').style('padding: 24px; overflow-y: auto; flex: 1; min-height: 0; box-sizing: border-box; width: 100%; max-width: 100%;'):
                ui.label('测试计划管理').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 12px;')
                ui.label('管理测试用例分组和执行计划，支持计划依赖关系。计划文件：test_plans/plans.yaml').style('color: #90caf9; font-size: 12px; margin-bottom: 20px; word-break: break-word; overflow-wrap: break-word; white-space: normal; line-height: 1.6; width: 100%; max-width: 100%; box-sizing: border-box;')
                
                # 添加计划按钮
                with ui.row().classes('w-full justify-end').style('margin-bottom: 16px;'):
                    ui.button('创建测试计划', icon='add', on_click=self._add_test_plan).style('min-height: 36px;')
                
                if plans:
                    with ui.column().classes('w-full').style('max-height: calc(90vh - 200px); overflow-y: auto; gap: 12px; padding-right: 8px;'):
                        for plan_id, plan in plans.items():
                            with ui.card().classes('w-full').style('background: rgba(10, 22, 40, 0.6); border: 1px solid rgba(0, 150, 255, 0.3); padding: 16px; border-radius: 8px; box-shadow: none;'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    with ui.column().classes('flex-1'):
                                        ui.label(plan.get('name', plan_id)).style('color: #e0e6ed; font-size: 14px; font-weight: 500; margin-bottom: 4px; word-break: break-word; overflow-wrap: break-word; white-space: normal; width: 100%; max-width: 100%; box-sizing: border-box;')
                                        if plan.get('description'):
                                            ui.label(plan['description']).style('color: #90caf9; font-size: 12px; margin-bottom: 4px; word-break: break-word; overflow-wrap: break-word; white-space: normal; width: 100%; max-width: 100%; box-sizing: border-box;')
                                        if plan.get('modules'):
                                            ui.label(f"模块: {', '.join(plan['modules'])}").style('color: #90caf9; font-size: 12px; word-break: break-word; overflow-wrap: break-word; white-space: normal; width: 100%; max-width: 100%; box-sizing: border-box;')
                                    
                                    with ui.row().classes('gap-2'):
                                        ui.button('删除', icon='delete', color='red', on_click=lambda pid=plan_id: self._delete_test_plan(pid, dialog)).style('min-height: 32px; padding: 4px 12px; font-size: 12px;')
                else:
                    with ui.column().classes('w-full items-center').style('padding: 40px;'):
                        ui.label('暂无测试计划').style('color: #90caf9; text-align: center; margin-bottom: 16px;')
                        ui.label('点击"创建测试计划"按钮创建计划，用于组织和管理测试用例的执行').style('color: #b0c4de; font-size: 12px; text-align: center;')
                
                with ui.row().classes('w-full justify-end').style('margin-top: 20px;'):
                    ui.button('关闭', on_click=dialog.close, icon='close').style('min-height: 36px;')
        
        dialog.open()
    
    def _add_test_plan(self):
        """添加测试计划"""
        modules = ['teaching', 'exercise', 'exam']
        module_names = {'teaching': '授课教学', 'exercise': '攻防演练', 'exam': '考试测评'}
        
        with ui.dialog() as add_dialog, ui.card().style('width: 800px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; box-sizing: border-box;'):
            with ui.column().classes('w-full').style('padding: 24px; overflow-y: auto; flex: 1; min-height: 0; box-sizing: border-box; width: 100%; max-width: 100%;'):
                ui.label('创建测试计划').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 20px;')
                
                plan_id_input = ui.input('计划ID（英文）', placeholder='例如：regression_test', value='').style('width: 100%; margin-bottom: 16px;')
                plan_name_input = ui.input('计划名称', placeholder='例如：回归测试计划', value='').style('width: 100%; margin-bottom: 16px;')
                desc_input = ui.textarea('计划描述（可选）', placeholder='计划说明...').style('width: 100%; margin-bottom: 16px;')
                
                ui.label('选择模块：').style('color: #e0e6ed; margin-bottom: 8px;')
                selected_modules = {}
                with ui.column().style('margin-bottom: 16px;'):
                    for module in modules:
                        checkbox = ui.checkbox(module_names.get(module, module), value=False)
                        selected_modules[module] = checkbox
                
                def save_plan():
                    plan_id = plan_id_input.value.strip()
                    plan_name = plan_name_input.value.strip()
                    
                    if not plan_id or not plan_name:
                        ui.notify('请填写计划ID和名称', type='warning')
                        return
                    
                    selected = [m for m, cb in selected_modules.items() if cb.value]
                    if not selected:
                        ui.notify('请至少选择一个模块', type='warning')
                        return
                    
                    if self.plan_manager.create_plan(
                        plan_id=plan_id,
                        name=plan_name,
                        description=desc_input.value.strip(),
                        modules=selected
                    ):
                        ui.notify('测试计划已创建', type='positive')
                        add_dialog.close()
                        ui.timer(0.3, lambda: self.show_test_plans(), once=True)
                    else:
                        ui.notify('创建失败', type='negative')
                
                with ui.row().classes('w-full justify-end').style('margin-top: 20px; gap: 12px;'):
                    ui.button('取消', on_click=add_dialog.close).style('min-height: 36px;')
                    ui.button('保存', on_click=save_plan, color='primary').style('min-height: 36px;')
        
        add_dialog.open()
    
    def _delete_test_plan(self, plan_id: str, dialog):
        """删除测试计划"""
        if self.plan_manager.delete_plan(plan_id):
            ui.notify('测试计划已删除', type='positive')
            dialog.close()
            ui.timer(0.3, lambda: self.show_test_plans(), once=True)
        else:
            ui.notify('删除失败', type='negative')
    
    def show_trend_analysis(self):
        """显示趋势分析"""
        if not self.result_analyzer:
            ui.notify('趋势分析功能不可用', type='warning')
            return
        
        stats = self.result_analyzer.get_statistics(30)
        trend_data = self.result_analyzer.get_trend_data(30)
        
        with ui.dialog() as dialog, ui.card().style('width: 1000px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; box-sizing: border-box;'):
            with ui.column().classes('w-full').style('padding: 24px; overflow-y: auto; flex: 1; min-height: 0; box-sizing: border-box; width: 100%; max-width: 100%;'):
                ui.label('测试结果趋势分析').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 12px;')
                ui.label('分析历史测试结果，显示趋势统计。数据来源：test_results/ 目录和 reports/ 目录中的报告文件。').style('color: #90caf9; font-size: 12px; margin-bottom: 20px; word-break: break-word; overflow-wrap: break-word; white-space: normal; line-height: 1.6; width: 100%; max-width: 100%; box-sizing: border-box;')
                
                # 统计信息和刷新按钮区域
                with ui.row().classes('w-full items-start justify-between').style('margin-bottom: 20px; flex-wrap: wrap; gap: 16px;'):
                    # 统计信息
                    with ui.grid(columns=3).classes('flex-1').style('min-width: 0; gap: 12px;'):
                        with ui.card().style('background: rgba(10, 22, 40, 0.6); padding: 16px; min-width: 0; box-sizing: border-box; border-radius: 8px; box-shadow: none;'):
                            ui.label('总执行次数').style('color: #90caf9; font-size: 12px; word-break: break-word;')
                            ui.label(str(stats['total_executions'])).style('color: #e0e6ed; font-size: 24px; font-weight: 700; word-break: break-word;')
                        
                        with ui.card().style('background: rgba(10, 22, 40, 0.6); padding: 16px; min-width: 0; box-sizing: border-box; border-radius: 8px; box-shadow: none;'):
                            ui.label('平均通过率').style('color: #90caf9; font-size: 12px; word-break: break-word;')
                            ui.label(f"{stats['avg_pass_rate']}%").style('color: #00ff88; font-size: 24px; font-weight: 700; word-break: break-word;')
                        
                        with ui.card().style('background: rgba(10, 22, 40, 0.6); padding: 16px; min-width: 0; box-sizing: border-box; border-radius: 8px; box-shadow: none;'):
                            ui.label('平均执行时长').style('color: #90caf9; font-size: 12px; word-break: break-word;')
                            ui.label(f"{stats['avg_duration']:.2f}秒").style('color: #e0e6ed; font-size: 24px; font-weight: 700; word-break: break-word;')
                    
                    # 刷新数据按钮
                    ui.button('刷新数据', icon='refresh', on_click=lambda: self._refresh_trend_data(dialog)).style('min-height: 36px; flex-shrink: 0;')
                
                # 趋势数据列表
                if trend_data:
                    ui.label(f'最近执行记录（共 {len(trend_data)} 条）').style('color: #e0e6ed; font-size: 14px; font-weight: 500; margin-bottom: 12px;')
                    with ui.column().classes('w-full').style('max-height: calc(90vh - 380px); overflow-y: auto; gap: 8px; padding-right: 8px; box-sizing: border-box; width: 100%; max-width: 100%;'):
                        for result in trend_data[:20]:  # 只显示最近20条
                            with ui.card().classes('w-full').style('background: rgba(10, 22, 40, 0.6); border: 1px solid rgba(0, 150, 255, 0.3); padding: 12px; border-radius: 8px; box-shadow: none; box-sizing: border-box; width: 100%; max-width: 100%; overflow: hidden;'):
                                with ui.row().classes('w-full items-center justify-between').style('width: 100%; max-width: 100%; box-sizing: border-box;'):
                                    with ui.column().classes('flex-1').style('min-width: 0; max-width: 100%; box-sizing: border-box; overflow: hidden;'):
                                        exec_time = result.get('execution_time', '')
                                        if 'T' in exec_time:
                                            exec_time = exec_time.replace('T', ' ')[:19]
                                        ui.label(exec_time).style('color: #90caf9; font-size: 12px; margin-bottom: 4px; word-break: break-word; overflow-wrap: break-word; white-space: normal;')
                                        ui.label(f"通过: {result.get('passed', 0)} | 失败: {result.get('failed', 0)} | 跳过: {result.get('skipped', 0)} | 通过率: {result.get('pass_rate', 0):.2f}%").style('color: #e0e6ed; font-size: 12px; word-break: break-word; overflow-wrap: break-word; white-space: normal;')
                                        if result.get('modules') and result['modules'] != 'unknown':
                                            ui.label(f"模块: {result['modules']}").style('color: #90caf9; font-size: 11px; word-break: break-word; overflow-wrap: break-word; white-space: normal;')
                else:
                    with ui.column().classes('w-full items-center').style('padding: 40px;'):
                        ui.label('暂无历史数据').style('color: #90caf9; text-align: center; margin-bottom: 16px;')
                        ui.label('执行测试后会自动保存结果，或点击"刷新数据"从已有报告中读取数据').style('color: #b0c4de; font-size: 12px; text-align: center;')
                
                with ui.row().classes('w-full justify-end').style('margin-top: 20px;'):
                    ui.button('关闭', on_click=dialog.close, icon='close').style('min-height: 36px;')
        
        dialog.open()


    def _refresh_trend_data(self, dialog):
        """刷新趋势数据"""
        if not self.result_analyzer:
            return
        
        # 重新解析报告
        try:
            # 触发一次数据解析
            trend_data = self.result_analyzer.get_trend_data(30)
            ui.notify(f'已刷新，找到 {len(trend_data)} 条历史数据', type='positive')
            dialog.close()
            ui.timer(0.3, lambda: self.show_trend_analysis(), once=True)
        except Exception as e:
            ui.notify(f'刷新失败: {str(e)}', type='negative')
    
    def _load_execution_config(self):
        """从配置文件加载执行配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    execution_config = config.get('execution', {})
                    if execution_config:
                        self.retry_count = execution_config.get('retry_count', 2)
                        self.timeout_seconds = execution_config.get('timeout_seconds', 30)
        except Exception as e:
            # 如果加载失败，使用默认值
            pass
    
    def _save_execution_config(self):
        """保存执行配置到配置文件"""
        try:
            # 确保config目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 读取现有配置
            config = {}
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
            
            # 更新执行配置
            if 'execution' not in config:
                config['execution'] = {}
            config['execution']['retry_count'] = self.retry_count
            config['execution']['timeout_seconds'] = self.timeout_seconds
            
            # 保存到文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            # 保存失败不影响使用
            pass
    
    def show_execution_config(self):
        """显示执行配置（重试次数和超时时间）"""
        with ui.dialog() as dialog, ui.card().style('width: 600px; max-width: 95vw; max-height: 90vh; background: rgba(20, 30, 50, 0.95); border: 2px solid rgba(0, 150, 255, 0.5); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; box-sizing: border-box;'):
            with ui.column().classes('w-full').style('padding: 24px; overflow-y: auto; flex: 1; min-height: 0; box-sizing: border-box; width: 100%; max-width: 100%;'):
                ui.label('执行配置').classes('text-lg font-bold').style('color: #e0e6ed; margin-bottom: 20px;')
                
                # 重试次数配置
                with ui.column().style('margin-bottom: 20px;'):
                    ui.label('重试次数').style('color: #e0e6ed; font-size: 14px; font-weight: 500; margin-bottom: 8px;')
                    ui.label('测试失败时自动重试的次数（范围：0-10次）').style('color: #90caf9; font-size: 12px; margin-bottom: 8px;')
                    retry_count_input = ui.number(
                        label='',
                        value=self.retry_count,
                        min=0,
                        max=10,
                        precision=0,
                        format='%.0f'
                    ).style('width: 120px;')
                    self.retry_count_input = retry_count_input
                
                # 超时时间配置
                with ui.column().style('margin-bottom: 20px;'):
                    ui.label('超时时间（秒）').style('color: #e0e6ed; font-size: 14px; font-weight: 500; margin-bottom: 8px;')
                    ui.label('单个操作的最大等待时间（范围：5-300秒）').style('color: #90caf9; font-size: 12px; margin-bottom: 8px;')
                    timeout_input = ui.number(
                        label='',
                        value=self.timeout_seconds,
                        min=5,
                        max=300,
                        precision=0,
                        format='%.0f'
                    ).style('width: 120px;')
                    self.timeout_input = timeout_input
                
                def save_config():
                    # 获取并验证值
                    retry_count = int(retry_count_input.value) if retry_count_input.value is not None else 2
                    timeout_seconds = int(timeout_input.value) if timeout_input.value is not None else 30
                    
                    # 限制范围
                    retry_count = max(0, min(10, retry_count))
                    timeout_seconds = max(5, min(300, timeout_seconds))
                    
                    # 保存配置
                    self.retry_count = retry_count
                    self.timeout_seconds = timeout_seconds
                    
                    # 保存到配置文件
                    self._save_execution_config()
                    
                    ui.notify(f'配置已保存：重试次数={retry_count}，超时时间={timeout_seconds}秒', type='positive')
                    dialog.close()
                
                with ui.row().classes('w-full justify-end').style('margin-top: 20px; gap: 12px;'):
                    ui.button('取消', on_click=dialog.close).style('min-height: 36px;')
                    ui.button('保存', on_click=save_config, color='primary').style('min-height: 36px;')
        
        dialog.open()
    
    def get_retry_count(self):
        """获取重试次数"""
        return self.retry_count
    
    def get_timeout_seconds(self):
        """获取超时时间"""
        return self.timeout_seconds
