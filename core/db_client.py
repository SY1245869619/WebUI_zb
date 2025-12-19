"""
数据库客户端封装
使用PyMySQL连接MySQL数据库
"""
import pymysql
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class DBClient:
    """MySQL数据库客户端"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """初始化数据库客户端
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.connection = None
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def connect(self):
        """建立数据库连接"""
        db_config = self.config['database']
        self.connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            charset=db_config['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    @contextmanager
    def get_cursor(self):
        """获取数据库游标的上下文管理器"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def execute_query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """执行查询语句
        
        Args:
            sql: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        with self.get_cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    
    def execute_update(self, sql: str, params: Optional[tuple] = None) -> int:
        """执行更新语句（INSERT, UPDATE, DELETE）
        
        Args:
            sql: SQL更新语句
            params: 更新参数
            
        Returns:
            受影响的行数
        """
        with self.get_cursor() as cursor:
            return cursor.execute(sql, params)
    
    def execute_many(self, sql: str, params_list: List[tuple]) -> int:
        """批量执行SQL语句
        
        Args:
            sql: SQL语句
            params_list: 参数列表
            
        Returns:
            受影响的总行数
        """
        with self.get_cursor() as cursor:
            return cursor.executemany(sql, params_list)
    
    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在
        
        Args:
            table_name: 表名
            
        Returns:
            表是否存在
        """
        sql = "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = %s AND table_name = %s"
        result = self.execute_query(sql, (self.config['database']['database'], table_name))
        return result[0]['count'] > 0
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """获取表的列名
        
        Args:
            table_name: 表名
            
        Returns:
            列名列表
        """
        sql = "SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s"
        result = self.execute_query(sql, (self.config['database']['database'], table_name))
        return [row['column_name'] for row in result]

