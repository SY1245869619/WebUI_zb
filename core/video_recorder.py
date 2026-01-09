"""
视频录制模块
失败用例自动录屏

@File  : video_recorder.py
@Author: shenyuan
"""
from pathlib import Path
from typing import Optional
from playwright.async_api import BrowserContext


class VideoRecorder:
    """视频录制器"""
    
    def __init__(self, video_dir: str = "videos"):
        """初始化视频录制器
        
        Args:
            video_dir: 视频保存目录
        """
        self.video_dir = Path(video_dir)
        self.video_dir.mkdir(parents=True, exist_ok=True)
        self.current_video_path: Optional[Path] = None
    
    def get_recording_options(self, test_name: str) -> dict:
        """获取视频录制配置选项（用于在创建BrowserContext时使用）
        
        Args:
            test_name: 测试用例名称
            
        Returns:
            视频录制配置字典
        """
        # 生成视频文件名
        video_file = self.video_dir / f"{test_name}.webm"
        self.current_video_path = video_file
        
        # 返回视频录制选项（用于在创建context时传入）
        return {
            'record_video_dir': str(self.video_dir),
            'record_video_size': {'width': 1920, 'height': 1080}
        }
    
    def enable_recording(self, context: BrowserContext, test_name: str) -> Path:
        """启用视频录制（已废弃，请使用get_recording_options）
        
        注意：此方法已废弃，因为BrowserContext不支持set_option。
        视频录制必须在创建BrowserContext时通过参数配置。
        
        Args:
            context: BrowserContext对象（未使用）
            test_name: 测试用例名称
            
        Returns:
            视频文件路径
        """
        # 生成视频文件名
        video_file = self.video_dir / f"{test_name}.webm"
        self.current_video_path = video_file
        
        # 注意：无法在已创建的context上设置视频录制选项
        # 视频录制必须在创建context时通过record_video_dir参数配置
        print(f"[VideoRecorder] 警告：视频录制应在创建BrowserContext时配置，当前context无法启用录制")
        
        return video_file
    
    def save_video(self, context: BrowserContext, test_name: str, failed: bool = False) -> Optional[Path]:
        """保存视频（仅在失败时保存）
        
        Args:
            context: BrowserContext对象
            test_name: 测试用例名称
            failed: 是否失败
            
        Returns:
            视频文件路径，如果未保存返回None
        """
        if not failed:
            # 如果测试通过，删除视频文件
            try:
                if self.current_video_path and self.current_video_path.exists():
                    self.current_video_path.unlink()
            except:
                pass
            return None
        
        # 如果失败，保留视频文件
        if self.current_video_path and self.current_video_path.exists():
            # 重命名为包含失败标记的文件名
            failed_video = self.video_dir / f"{test_name}_FAILED.webm"
            if failed_video.exists():
                failed_video.unlink()
            self.current_video_path.rename(failed_video)
            return failed_video
        
        return None

