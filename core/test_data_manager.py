"""
测试数据管理器
支持CSV/JSON/YAML格式的测试数据

@File  : test_data_manager.py
@Author: shenyuan
"""
import csv
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd


class TestDataManager:
    """测试数据管理器"""
    
    def __init__(self, data_dir: str = "test_data"):
        """初始化数据管理器
        
        Args:
            data_dir: 测试数据目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def load_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """加载CSV文件
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            数据列表（字典格式）
        """
        file_path = self.data_dir / file_path if not Path(file_path).is_absolute() else Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {file_path}")
        
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))
        
        return data
    
    def load_json(self, file_path: str) -> List[Dict[str, Any]]:
        """加载JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            数据列表
        """
        file_path = self.data_dir / file_path if not Path(file_path).is_absolute() else Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 如果是单个字典，转换为列表
        if isinstance(data, dict):
            data = [data]
        
        return data if isinstance(data, list) else []
    
    def load_yaml(self, file_path: str) -> List[Dict[str, Any]]:
        """加载YAML文件
        
        Args:
            file_path: YAML文件路径
            
        Returns:
            数据列表
        """
        file_path = self.data_dir / file_path if not Path(file_path).is_absolute() else Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # 如果是单个字典，转换为列表
        if isinstance(data, dict):
            data = [data]
        
        return data if isinstance(data, list) else []
    
    def save_csv(self, data: List[Dict[str, Any]], file_path: str):
        """保存数据到CSV文件
        
        Args:
            data: 数据列表
            file_path: 保存路径
        """
        file_path = self.data_dir / file_path if not Path(file_path).is_absolute() else Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not data:
            return
        
        fieldnames = data[0].keys()
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    def save_json(self, data: List[Dict[str, Any]], file_path: str):
        """保存数据到JSON文件
        
        Args:
            data: 数据列表
            file_path: 保存路径
        """
        file_path = self.data_dir / file_path if not Path(file_path).is_absolute() else Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_yaml(self, data: List[Dict[str, Any]], file_path: str):
        """保存数据到YAML文件
        
        Args:
            data: 数据列表
            file_path: 保存路径
        """
        file_path = self.data_dir / file_path if not Path(file_path).is_absolute() else Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
    
    def get_data_files(self) -> List[Dict[str, Any]]:
        """获取所有数据文件列表
        
        Returns:
            文件信息列表
        """
        files = []
        for ext in ['*.csv', '*.json', '*.yaml', '*.yml']:
            for file_path in self.data_dir.rglob(ext):
                stat = file_path.stat()
                files.append({
                    'name': file_path.name,
                    'path': str(file_path.relative_to(self.data_dir)),
                    'full_path': str(file_path),
                    'type': ext.replace('*.', ''),
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
        
        return sorted(files, key=lambda x: x['modified'], reverse=True)

