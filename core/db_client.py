"""
数据库客户端封装
使用PyMySQL连接MySQL数据库
支持SSH隧道连接

@File  : db_client.py
@Author: shenyuan
"""
import pymysql
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import sshtunnel


class DBClient:
    """MySQL数据库客户端"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """初始化数据库客户端
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.db_config = self.config.get('database', {})
        self.connection = None
        self.ssh_tunnel = None
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _setup_ssh_tunnel(self) -> Optional[sshtunnel.SSHTunnelForwarder]:
        """设置SSH隧道（如果需要）
        
        Returns:
            SSH隧道对象，如果不需要则返回None
        """
        ssh_config = self.db_config.get('ssh_tunnel', {})
        if not ssh_config.get('enabled', False):
            return None
        
        tunnel = sshtunnel.SSHTunnelForwarder(
            (ssh_config['ssh_host'], ssh_config.get('ssh_port', 22)),
            ssh_username=ssh_config['ssh_user'],
            ssh_password=ssh_config.get('ssh_password'),
            ssh_private_key=ssh_config.get('ssh_private_key'),
            remote_bind_address=(self.db_config['host'], self.db_config.get('port', 3306)),
            local_bind_address=('127.0.0.1', 0)  # 0表示自动分配端口
        )
        tunnel.start()
        return tunnel
    
    def connect(self):
        """连接到数据库"""
        # 设置SSH隧道（如果需要）
        self.ssh_tunnel = self._setup_ssh_tunnel()
        
        # 确定实际连接的主机和端口
        if self.ssh_tunnel:
            # 通过SSH隧道连接
            host = '127.0.0.1'
            port = self.ssh_tunnel.local_bind_port
        else:
            # 直接连接
            host = self.config['host']
            port = self.config.get('port', 3306)
        
        # 建立数据库连接
        self.connection = pymysql.connect(
            host=host,
            port=port,
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database'],
            charset=self.db_config.get('charset', 'utf8mb4'),
            cursorclass=pymysql.cursors.DictCursor  # 返回字典格式的结果
        )
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
        
        if self.ssh_tunnel:
            self.ssh_tunnel.stop()
            self.ssh_tunnel = None
    
    def is_connected(self) -> bool:
        """检查是否已连接
        
        Returns:
            是否已连接
        """
        return self.connection is not None and self.connection.open
    
    @contextmanager
    def get_cursor(self):
        """获取数据库游标的上下文管理器
        
        使用示例:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                results = cursor.fetchall()
        """
        if not self.is_connected():
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
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器
        
        使用示例:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
                results = cursor.fetchall()
        """
        if not self.is_connected():
            self.connect()
        
        try:
            yield self.connection
        finally:
            # 注意：这里不关闭连接，由 disconnect() 方法统一管理
            pass
    
    def execute_query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """执行查询语句
        
        Args:
            sql: SQL查询语句
            params: 查询参数（用于防止SQL注入）
            
        Returns:
            查询结果列表（字典格式）
        """
        with self.get_cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    
    def execute_update(self, sql: str, params: Optional[tuple] = None) -> int:
        """执行更新语句（INSERT、UPDATE、DELETE）
        
        Args:
            sql: SQL更新语句
            params: 更新参数（用于防止SQL注入）
            
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
        result = self.execute_query(sql, (self.db_config['database'], table_name))
        return result[0]['count'] > 0
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """获取表的列名
        
        Args:
            table_name: 表名
            
        Returns:
            列名列表
        """
        sql = "SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s"
        result = self.execute_query(sql, (self.db_config['database'], table_name))
        return [row['column_name'] for row in result]
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
        return False

