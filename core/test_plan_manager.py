"""
测试计划管理器
管理测试用例分组和执行计划

@File  : test_plan_manager.py
@Author: shenyuan
"""
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class TestPlanManager:
    """测试计划管理器"""
    
    def __init__(self, plans_dir: str = "test_plans"):
        """初始化测试计划管理器
        
        Args:
            plans_dir: 测试计划目录
        """
        self.plans_dir = Path(plans_dir)
        self.plans_dir.mkdir(exist_ok=True)
        self.plans: Dict[str, Dict] = {}
        self._load_plans()
    
    def _load_plans(self):
        """加载所有测试计划"""
        plans_file = self.plans_dir / "plans.yaml"
        if plans_file.exists():
            with open(plans_file, 'r', encoding='utf-8') as f:
                self.plans = yaml.safe_load(f) or {}
        else:
            self.plans = {}
            self._save_plans()
    
    def create_plan(
        self,
        plan_id: str,
        name: str,
        description: str = "",
        modules: Optional[List[str]] = None,
        test_cases: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None
    ) -> bool:
        """创建测试计划
        
        Args:
            plan_id: 计划ID
            name: 计划名称
            description: 计划描述
            modules: 模块列表
            test_cases: 测试用例列表（可选，如果提供则只执行这些用例）
            dependencies: 依赖的计划ID列表（可选）
            
        Returns:
            是否创建成功
        """
        self.plans[plan_id] = {
            'name': name,
            'description': description,
            'modules': modules or [],
            'test_cases': test_cases or [],
            'dependencies': dependencies or [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self._save_plans()
        return True
    
    def get_plan(self, plan_id: str) -> Optional[Dict]:
        """获取测试计划
        
        Args:
            plan_id: 计划ID
            
        Returns:
            计划配置，如果不存在返回None
        """
        return self.plans.get(plan_id)
    
    def get_all_plans(self) -> Dict[str, Dict]:
        """获取所有测试计划
        
        Returns:
            计划字典
        """
        return self.plans
    
    def update_plan(self, plan_id: str, **kwargs) -> bool:
        """更新测试计划
        
        Args:
            plan_id: 计划ID
            **kwargs: 要更新的字段
            
        Returns:
            是否更新成功
        """
        if plan_id not in self.plans:
            return False
        
        self.plans[plan_id].update(kwargs)
        self.plans[plan_id]['updated_at'] = datetime.now().isoformat()
        self._save_plans()
        return True
    
    def delete_plan(self, plan_id: str) -> bool:
        """删除测试计划
        
        Args:
            plan_id: 计划ID
            
        Returns:
            是否删除成功
        """
        if plan_id in self.plans:
            del self.plans[plan_id]
            self._save_plans()
            return True
        return False
    
    def get_plan_execution_command(self, plan_id: str) -> Optional[List[str]]:
        """获取计划执行命令
        
        Args:
            plan_id: 计划ID
            
        Returns:
            pytest命令列表
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        
        cmd = ['pytest', '-v']
        
        # 如果有依赖，先执行依赖
        if plan.get('dependencies'):
            # 这里可以递归处理依赖，简化处理只返回当前计划
            pass
        
        # 如果有指定测试用例，使用用例路径
        if plan.get('test_cases'):
            cmd.extend(plan['test_cases'])
        # 否则使用模块标记
        elif plan.get('modules'):
            marks = ' or '.join(plan['modules'])
            cmd.extend(['-m', marks])
        
        return cmd
    
    def _save_plans(self):
        """保存测试计划到文件"""
        plans_file = self.plans_dir / "plans.yaml"
        with open(plans_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.plans, f, allow_unicode=True, default_flow_style=False)

