"""
测试调度服务
支持定时执行测试任务

@File  : test_scheduler.py
@Author: shenyuan
"""
import subprocess
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path
import yaml

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    BackgroundScheduler = None
    CronTrigger = None
    IntervalTrigger = None


class TestScheduler:
    """测试调度器"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """初始化调度器
        
        Args:
            config_path: 配置文件路径
        """
        if not APSCHEDULER_AVAILABLE:
            raise ImportError("APScheduler未安装，请运行: pip install APScheduler")
        
        self.config_path = config_path
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.jobs: Dict[str, str] = {}  # job_id -> job_name
        self._load_schedules()
    
    def _load_schedules(self):
        """从配置文件加载调度任务"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            return
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        schedules = config.get('schedules', [])
        for schedule in schedules:
            if schedule.get('enabled', False):
                self.add_schedule(
                    name=schedule.get('name', ''),
                    modules=schedule.get('modules', []),
                    cron=schedule.get('cron'),
                    interval=schedule.get('interval'),
                    job_id=schedule.get('id')
                )
    
    def add_schedule(
        self,
        name: str,
        modules: List[str],
        cron: Optional[str] = None,
        interval: Optional[Dict] = None,
        job_id: Optional[str] = None,
        callback: Optional[Callable] = None
    ) -> str:
        """添加调度任务
        
        Args:
            name: 任务名称
            modules: 要执行的模块列表
            cron: Cron表达式，例如 "0 9 * * *" (每天9点)
            interval: 间隔触发，例如 {"hours": 2} (每2小时)
            job_id: 任务ID（如果不提供则自动生成）
            callback: 执行回调函数（可选）
            
        Returns:
            任务ID
        """
        if not job_id:
            job_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 构建pytest命令
        cmd_parts = ['pytest', '-v']
        if modules:
            marks = ' or '.join(modules)
            cmd_parts.extend(['-m', marks])
        
        def run_test():
            """执行测试任务"""
            try:
                subprocess.run(cmd_parts, check=False)
            except Exception as e:
                print(f"调度任务执行失败: {e}")
            if callback:
                callback()
        
        # 设置触发器
        if cron:
            trigger = CronTrigger.from_crontab(cron)
        elif interval:
            trigger = IntervalTrigger(**interval)
        else:
            raise ValueError("必须提供cron或interval参数")
        
        # 添加任务
        self.scheduler.add_job(
            func=run_test,
            trigger=trigger,
            id=job_id,
            name=name,
            replace_existing=True
        )
        
        self.jobs[job_id] = name
        return job_id
    
    def remove_schedule(self, job_id: str) -> bool:
        """删除调度任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            是否删除成功
        """
        try:
            self.scheduler.remove_job(job_id)
            self.jobs.pop(job_id, None)
            return True
        except Exception as e:
            print(f"删除调度任务失败: {e}")
            return False
    
    def get_all_jobs(self) -> List[Dict]:
        """获取所有调度任务
        
        Returns:
            任务列表
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def pause_job(self, job_id: str) -> bool:
        """暂停任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            是否成功
        """
        try:
            self.scheduler.pause_job(job_id)
            return True
        except Exception as e:
            print(f"暂停任务失败: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """恢复任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            是否成功
        """
        try:
            self.scheduler.resume_job(job_id)
            return True
        except Exception as e:
            print(f"恢复任务失败: {e}")
            return False
    
    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()

