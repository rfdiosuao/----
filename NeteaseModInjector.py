# 脚本名称：网易我的世界模组自动注入器 (NeteaseModInjector)
# 功能：专为网易版设计，在启动器清空Mods文件夹的瞬间极速注入自定义模组、光影和材质包
# 特性：自动路径识别、毫秒级响应、持续监控、防误触

import os
import shutil
import time
import winreg
import sys
import threading
from datetime import datetime

class ModInjector:
    def __init__(self):
        self.game_mods_path = None
        self.game_resource_path = None
        self.game_shader_path = None
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.local_mods_path = os.path.join(self.base_dir, "MyMods")
        self.local_resource_path = os.path.join(self.base_dir, "MyResourcePacks")
        self.local_shader_path = os.path.join(self.base_dir, "MyShaderPacks")
        
        self.running = True
        self.injection_count = 0
        self.last_injection_time = 0
        self.resources_injected = False
        
    def log(self, message):
        """带时间戳的日志输出"""
        current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{current_time}] {message}")

    def get_netease_path(self):
        """从注册表自动获取网易启动器路径"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Netease\MCLauncher")
            path, _ = winreg.QueryValueEx(key, "DownloadPath")
            winreg.CloseKey(key)
            return path
        except:
            return None

    def setup_directories(self):
        """初始化目录结构"""
        # 1. 寻找游戏路径
        base_path = self.get_netease_path()
        if not base_path:
            self.log("错误：无法从注册表找到网易启动器路径。请确认游戏已安装。")
            return False
            
        # 网易版常见路径
        self.game_mods_path = os.path.join(base_path, "Game", ".minecraft", "mods")
        self.game_resource_path = os.path.join(base_path, "Game", ".minecraft", "resourcepacks")
        self.game_shader_path = os.path.join(base_path, "Game", ".minecraft", "shaderpacks")
        
        self.log(f"已锁定游戏目录：\n   -> Mods: {self.game_mods_path}")

        # 2. 准备本地目录
        for path, name in [
            (self.local_mods_path, "MyMods (模组)"),
            (self.local_resource_path, "MyResourcePacks (材质包)"),
            (self.local_shader_path, "MyShaderPacks (光影包)")
        ]:
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                    self.log(f"已创建文件夹：{name}")
                except Exception as e:
                    self.log(f"创建文件夹 {name} 失败: {e}")

        # 检查是否有文件
        mods = [f for f in os.listdir(self.local_mods_path) if f.endswith(".jar")]
        if not mods:
            self.log("提示：MyMods 文件夹为空，将不会注入模组。")
        else:
            self.log(f"就绪：检测到 {len(mods)} 个待注入模组。")
            
        return True

    def inject_files(self, source_dir, target_dir, file_types):
        """通用文件注入函数"""
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
            except:
                return 0

        source_files = [f for f in os.listdir(source_dir) if f.endswith(file_types)]
        if not source_files:
            return 0

        success_count = 0
        for file_name in source_files:
            src = os.path.join(source_dir, file_name)
            dst = os.path.join(target_dir, file_name)
            try:
                # 如果目标文件已存在且大小相同，跳过（避免重复复制）
                if os.path.exists(dst) and os.path.getsize(src) == os.path.getsize(dst):
                    continue
                    
                shutil.copy2(src, dst)
                success_count += 1
            except Exception:
                pass
        return success_count

    def inject_mods(self):
        """极速注入模组"""
        if not os.path.exists(self.game_mods_path):
            return

        source_files = [f for f in os.listdir(self.local_mods_path) if f.endswith(".jar")]
        if not source_files:
            return

        success_count = 0
        start_time = time.time()
        
        for file_name in source_files:
            src = os.path.join(self.local_mods_path, file_name)
            dst = os.path.join(self.game_mods_path, file_name)
            try:
                shutil.copy2(src, dst)
                success_count += 1
            except Exception:
                pass 
                
        duration = (time.time() - start_time) * 1000
        if success_count > 0:
            self.log(f"⚡ 模组注入完成！耗时 {duration:.2f}ms | 成功: {success_count} 个")
            self.injection_count += 1
            self.last_injection_time = time.time()
            
            # 模组注入成功后，顺便检查并注入一次资源包和光影
            # 不需要每次毫秒级轮询，只要在模组注入（意味着游戏启动）时做一次即可
            if not self.resources_injected:
                self.inject_resources()

    def inject_resources(self):
        """注入光影和材质包"""
        self.log("正在检查资源包和光影包...")
        
        # 注入材质包
        r_count = self.inject_files(self.local_resource_path, self.game_resource_path, ('.zip', '.mcpack'))
        if r_count > 0:
            self.log(f"📦 已注入 {r_count} 个材质包")
            
        # 注入光影包
        s_count = self.inject_files(self.local_shader_path, self.game_shader_path, ('.zip',))
        if s_count > 0:
            self.log(f"✨ 已注入 {s_count} 个光影包")
            
        self.resources_injected = True

    def start_monitoring(self):
        """主监控循环"""
        if not self.setup_directories():
            return

        print("=" * 60)
        print("  网易我的世界全能注入器 (模组/光影/材质)")
        print("  状态：正在监控游戏启动...")
        print("  说明：请保持本窗口开启，游戏启动时自动工作")
        print("=" * 60)

        # 启动时先尝试注入一次资源包（防止用户是在游戏关闭时运行的脚本）
        self.inject_resources()

        try:
            while self.running:
                # 检查 Mods 文件夹
                if os.path.exists(self.game_mods_path):
                    try:
                        # 极速检测空文件夹
                        with os.scandir(self.game_mods_path) as it:
                            is_empty = not any(it)
                        
                        if is_empty and (time.time() - self.last_injection_time > 2.0):
                            self.log("检测到 Mods 被清空，正在注入所有资源...")
                            self.inject_mods()
                            # 发生清空通常意味着游戏重启，重置资源注入标志以便再次检查
                            self.resources_injected = False 
                            
                    except OSError:
                        pass
                
                time.sleep(0.01)

        except KeyboardInterrupt:
            self.log("用户停止了监控。")

if __name__ == "__main__":
    injector = ModInjector()
    injector.start_monitoring()
    input("按回车键退出...")
