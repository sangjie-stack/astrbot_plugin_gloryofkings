"""
账号管理模块
处理营地ID的绑定、切换、删除等操作
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, List
from astrbot.api import logger


class AccountManager:
    """账号管理器"""
    
    def __init__(self, data_dir: Path):
        self.data_file = data_dir / "user_data.json"
        self.role_selection_file = data_dir / "role_selection.json"
        self.user_data: Dict[str, Dict] = {}
        self.role_selections: Dict[str, str] = {}  # user_id -> selected_role_id
        self._load_data()
        self._load_role_selections()

    def _load_data(self):
        """加载用户数据"""
        if not os.path.exists(self.data_file):
            self._save_data()
            return
        
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                self.user_data = json.load(f)
        except Exception as e:
            logger.error(f"加载用户数据失败: {e}")
            self.user_data = {}

    def _save_data(self):
        """保存用户数据"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.user_data, f, ensure_ascii=False, indent=2)

    def _get_user_info(self, user_id: str) -> Dict:
        """获取用户信息"""
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "ids": [],
                "current": 0
            }
        return self.user_data[user_id]

    async def bind_id(self, user_id: str, camp_id: str) -> str:
        """绑定营地ID"""
        user_id = str(user_id)
        user_info = self._get_user_info(user_id)
        
        if camp_id in user_info["ids"]:
            return "❌ 该ID已经绑定过了"
        
        user_info["ids"].append(camp_id)
        if len(user_info["ids"]) == 1:
            user_info["current"] = 0
        
        self._save_data()
        logger.info(f"用户 {user_id} 绑定营地ID: {camp_id}, 当前数据: {user_info}")
        
        id_list = self._format_id_list(user_info)
        return f"✅ 绑定成功！\n营地ID: {camp_id}\n\n当前账号列表:\n{id_list}\n\n可用功能:\n• 切换营地 [序号]\n• 删除营地 [序号]\n• 我的ID"

    async def switch_id(self, user_id: str, index: int) -> str:
        """切换营地ID"""
        user_id = str(user_id)
        user_info = self._get_user_info(user_id)
        
        if not user_info["ids"]:
            return "❌ 您还没有绑定任何ID，请先绑定\n使用: 绑定营地 [ID]"
        
        if index < 0 or index >= len(user_info["ids"]):
            return f"❌ 序号无效，请输入1-{len(user_info['ids'])}之间的序号"
        
        user_info["current"] = index
        self._save_data()
        
        id_list = self._format_id_list(user_info)
        return f"✅ 切换成功！\n当前使用: {user_info['ids'][index]}\n\n账号列表:\n{id_list}"

    async def delete_id(self, user_id: str, index: int) -> str:
        """删除营地ID"""
        user_id = str(user_id)
        user_info = self._get_user_info(user_id)
        
        if not user_info["ids"]:
            return "❌ 您还没有绑定任何ID"
        
        if index < 0 or index >= len(user_info["ids"]):
            return f"❌ 序号无效，请输入1-{len(user_info['ids'])}之间的序号"
        
        deleted_id = user_info["ids"][index]
        user_info["ids"].pop(index)
        
        if user_info["current"] >= len(user_info["ids"]):
            user_info["current"] = max(0, len(user_info["ids"]) - 1)
        
        self._save_data()
        
        if user_info["ids"]:
            id_list = self._format_id_list(user_info)
            return f"✅ 删除成功！\n已删除: {deleted_id}\n\n剩余账号:\n{id_list}"
        else:
            return f"✅ 删除成功！\n已删除: {deleted_id}\n\n请使用【绑定营地 [ID]】添加新账号"

    async def get_id_list(self, user_id: str) -> str:
        """获取ID列表"""
        user_id = str(user_id)
        user_info = self._get_user_info(user_id)
        
        if not user_info["ids"]:
            return "❌ 您还没有绑定任何ID\n\n📖 如何获取营地ID？\n1. 打开王者营地APP\n2. 点击【我的】\n3. 点击【游戏资料】\n4. 复制营地ID\n\n使用: 绑定营地 [ID]"
        
        id_list = self._format_id_list(user_info)
        return f"📋 您的王者营地ID列表:\n\n{id_list}\n\n💡 提示:\n• 切换营地 [序号] - 切换账号\n• 删除营地 [序号] - 删除账号"

    def get_current_id(self, user_id: str) -> Optional[str]:
        """获取当前使用的ID"""
        user_id = str(user_id)
        user_info = self._get_user_info(user_id)
        if not user_info["ids"]:
            logger.debug(f"用户 {user_id} 没有绑定任何ID")
            return None
        current_id = str(user_info["ids"][user_info["current"]])
        logger.debug(f"用户 {user_id} 当前使用ID: {current_id}")
        return current_id

    def _format_id_list(self, user_info: Dict) -> str:
        """格式化ID列表显示"""
        lines = []
        for i, camp_id in enumerate(user_info["ids"]):
            prefix = "✅" if i == user_info["current"] else "☑️"
            lines.append(f"{prefix} {i + 1}. {camp_id}")
        return "\n".join(lines)
    
    def _load_role_selections(self):
        """加载角色选择数据"""
        if not os.path.exists(self.role_selection_file):
            self._save_role_selections()
            return
        
        try:
            with open(self.role_selection_file, "r", encoding="utf-8") as f:
                self.role_selections = json.load(f)
        except Exception as e:
            logger.error(f"加载角色选择数据失败: {e}")
            self.role_selections = {}
    
    def _save_role_selections(self):
        """保存角色选择数据"""
        try:
            with open(self.role_selection_file, "w", encoding="utf-8") as f:
                json.dump(self.role_selections, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存角色选择数据失败: {e}")
    
    def set_selected_role(self, user_id: str, role_id: str):
        """设置用户选择的角色"""
        user_id = str(user_id)
        self.role_selections[user_id] = role_id
        self._save_role_selections()
        logger.info(f"用户 {user_id} 选择了角色: {role_id}")
    
    def get_selected_role(self, user_id: str) -> Optional[str]:
        """获取用户选择的角色"""
        user_id = str(user_id)
        return self.role_selections.get(user_id)
    
    def clear_selected_role(self, user_id: str):
        """清除用户选择的角色"""
        user_id = str(user_id)
        if user_id in self.role_selections:
            del self.role_selections[user_id]
            self._save_role_selections()
            logger.info(f"清除用户 {user_id} 的角色选择")
