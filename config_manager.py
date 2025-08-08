import json
import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "project_directory": "C:/Users/shiya/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft",
            "current_project": "",
            "recent_projects": [],
            "theme": "auto",
            "auto_backup": True
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置，确保所有必要的键都存在
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return default_config
        else:
            return default_config
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        self.config[key] = value
        self.save_config()
    
    def add_recent_project(self, project_path: str):
        """添加最近使用的项目"""
        recent = self.config.get("recent_projects", [])
        if project_path in recent:
            recent.remove(project_path)
        recent.insert(0, project_path)
        # 只保留最近10个项目
        self.config["recent_projects"] = recent[:10]
        self.save_config()