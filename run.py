"""
命令行启动入口

@File  : run.py
@Author: shenyuan
"""
import sys
import re
import threading
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def get_address_type(ip: str) -> tuple[str, str]:
    """判断IP地址类型并返回说明
    
    Args:
        ip: IP地址字符串
        
    Returns:
        (类型, 说明) 元组
    """
    if ip in ['localhost', '127.0.0.1']:
        return ('本机访问', '只能在本机访问，最快最稳定')
    elif ip.startswith('169.254.'):
        return ('自动配置地址', 'Windows自动分配，通常无法用于局域网访问，可忽略')
    elif ip.startswith('172.16.') or ip.startswith('172.17.') or ip.startswith('172.18.') or ip.startswith('172.19.') or \
         ip.startswith('172.20.') or ip.startswith('172.21.') or ip.startswith('172.22.') or ip.startswith('172.23.') or \
         ip.startswith('172.24.') or ip.startswith('172.25.') or ip.startswith('172.26.') or ip.startswith('172.27.') or \
         ip.startswith('172.28.') or ip.startswith('172.29.') or ip.startswith('172.30.') or ip.startswith('172.31.'):
        return ('虚拟网络', '可能是VMware/VirtualBox/Docker等虚拟网络接口')
    elif ip.startswith('192.168.') or ip.startswith('10.'):
        return ('局域网地址', '⭐ 这是别人访问应该使用的地址！同一局域网内可访问')
    elif ip.startswith('172.'):
        return ('私有网络', '可能是私有网络地址')
    else:
        return ('其他', '其他类型的网络地址')


# 全局标志和锁，确保地址说明只显示一次
_address_info_shown = False
_address_info_lock = threading.Lock()


# 必须在导入nicegui之前设置
if __name__ in {"__main__", "__mp_main__"}:
    # 直接在这里导入和运行，确保ui.run()在主线程中调用
    from nicegui import ui
    from web_ui.main import WebUIController
    import yaml
    
    # 创建控制器并渲染UI
    controller = WebUIController()
    controller.render()
    
    # 加载配置
    config_path = Path("config/settings.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        web_config = config.get('web_ui', {})
        host = web_config.get('host', '0.0.0.0')
        port = web_config.get('port', 8080)
        title = web_config.get('title', 'WebUI自动化测试控制台')
    else:
        host = '0.0.0.0'
        port = 8080
        title = 'WebUI自动化测试控制台'
    
    # 使用标记文件确保只显示一次（跨进程安全）
    _marker_file = Path("temp/address_info_shown.txt")
    _marker_file.parent.mkdir(exist_ok=True)
    
    # 使用线程在启动后解析并显示地址说明
    def show_address_info():
        """延迟显示地址说明"""
        global _address_info_shown
        
        # 检查标记文件是否存在（跨进程检查）
        if _marker_file.exists():
            return  # 已经显示过，不再显示
        
        # 使用线程锁确保线程安全
        with _address_info_lock:
            if _address_info_shown:
                return  # 已经显示过，不再显示
        
        import time
        time.sleep(1.5)  # 等待服务启动
        
        # 再次检查标记文件和标志
        if _marker_file.exists():
            return
        
        with _address_info_lock:
            if _address_info_shown:
                return
            
            # 再次检查文件（双重检查）
            if _marker_file.exists():
                return
            
            # 创建标记文件
            try:
                with open(_marker_file, 'x') as f:  # 'x' 模式：如果文件存在会抛出 FileExistsError
                    f.write("1")
                _address_info_shown = True
            except FileExistsError:
                return  # 其他进程已经创建了文件
            except Exception:
                # 如果创建失败，仍然继续显示（避免因为文件系统问题导致不显示）
                _address_info_shown = True
        
        # 获取所有网络接口的IP地址
        import socket
        addresses = []
        
        # 获取本机地址
        addresses.append(('localhost', '本机访问', '只能在本机访问，最快最稳定'))
        addresses.append(('127.0.0.1', '本机访问', '只能在本机访问，最快最稳定'))
        
        # 获取所有网络接口的IP（只获取IPv4）
        try:
            hostname = socket.gethostname()
            # 获取所有IP地址
            seen_ips = set(['127.0.0.1', 'localhost'])
            for addr_info in socket.getaddrinfo(hostname, None, socket.AF_INET):
                ip = addr_info[4][0]
                if ip and ip not in seen_ips:
                    seen_ips.add(ip)
                    addr_type, description = get_address_type(ip)
                    addresses.append((ip, addr_type, description))
        except:
            pass
        
        # 显示地址说明
        print("\n" + "="*80)
        print("📍 访问地址说明：")
        print("="*80)
        
        local_addresses = []
        lan_addresses = []
        other_addresses = []
        
        for ip, addr_type, desc in addresses:
            full_url = f"http://{ip}:{port}"
            if addr_type == '本机访问':
                local_addresses.append((full_url, addr_type, desc))
            elif addr_type == '局域网地址':
                lan_addresses.append((full_url, addr_type, desc))
            else:
                other_addresses.append((full_url, addr_type, desc))
        
        # 显示本机访问地址
        if local_addresses:
            print("\n🖥️  本机访问（推荐自己使用）：")
            for url, addr_type, desc in local_addresses[:2]:  # 只显示前两个
                print(f"   {url:50s} - {desc}")
        
        # 显示局域网地址（最重要）
        if lan_addresses:
            print("\n🌐 局域网访问（别人访问你的服务）：")
            for url, addr_type, desc in lan_addresses:
                print(f"   {url:50s} - {desc}")
            print("\n   ⚠️  注意：如果别人无法访问，请检查Windows防火墙是否允许端口8080")
            print("   快速解决：以管理员身份运行 PowerShell，执行：")
            print("   New-NetFirewallRule -DisplayName \"WebUI 服务端口 8080\" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow")
        
        # 显示其他地址（只显示前几个，过滤IPv6）
        if other_addresses:
            # 过滤掉IPv6地址（fe80::开头）
            ipv4_others = [addr for addr in other_addresses if not addr[0].startswith('http://fe80::')]
            if ipv4_others:
                print("\n📡 其他网络接口：")
                for url, addr_type, desc in ipv4_others[:3]:  # 只显示前3个
                    print(f"   {url:50s} - {desc}")
                if len(ipv4_others) > 3:
                    print(f"   ... 还有 {len(ipv4_others) - 3} 个其他网络接口")
        
        print("\n" + "="*80)
        print("💡 提示：")
        print("   - 自己访问：使用 localhost 或 127.0.0.1")
        print("   - 别人访问：使用 192.168.x.x 或 10.x.x.x 开头的地址")
        print("   - 详细说明请查看：docs/网络访问说明.md")
        print("="*80 + "\n")
    
    # 启动后台线程显示地址说明（只启动一次）
    import threading
    info_thread = threading.Thread(target=show_address_info, daemon=True)
    info_thread.start()
    
    # 在主线程中调用ui.run()
    ui.run(host=host, port=port, title=title)

