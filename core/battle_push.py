"""
战绩推送模块
定时检查用户战绩变化，推送新战绩
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from .api_service import ApiService

api_service = ApiService()


class BattlePushManager:
    """战绩推送管理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.push_config_file = self.data_dir / "battle_push_config.json"
        self.last_battle_file = self.data_dir / "last_battle_record.json"
        self.push_config = self._load_push_config()
        self.last_battles = self._load_last_battles()
        self.task = None
        
    def _load_push_config(self) -> Dict:
        """加载推送配置"""
        if self.push_config_file.exists():
            try:
                with open(self.push_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载推送配置失败: {e}")
        return {}
    
    def _save_push_config(self):
        """保存推送配置"""
        try:
            with open(self.push_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.push_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存推送配置失败: {e}")
    
    def _load_last_battles(self) -> Dict:
        """加载上次战绩记录"""
        if self.last_battle_file.exists():
            try:
                with open(self.last_battle_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载战绩记录失败: {e}")
        return {}
    
    def _save_last_battles(self):
        """保存战绩记录"""
        try:
            with open(self.last_battle_file, 'w', encoding='utf-8') as f:
                json.dump(self.last_battles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存战绩记录失败: {e}")
    
    def add_push_user(self, user_id: str, camp_id: str, group_id: Optional[str] = None) -> str:
        """添加战绩推送用户"""
        user_id = str(user_id)
        
        if user_id not in self.push_config:
            self.push_config[user_id] = {
                "camp_id": camp_id,
                "groups": [],
                "enabled": True
            }
        
        # 添加群组
        if group_id:
            group_id = str(group_id)
            if group_id not in self.push_config[user_id]["groups"]:
                self.push_config[user_id]["groups"].append(group_id)
        
        self._save_push_config()
        return f"✅ 已开启战绩推送\n营地ID: {camp_id}\n推送到: {'当前会话' if group_id else '私聊'}"
    
    def remove_push_user(self, user_id: str, group_id: Optional[str] = None) -> str:
        """移除战绩推送用户"""
        user_id = str(user_id)
        
        if user_id not in self.push_config:
            return "❌ 未开启战绩推送"
        
        if group_id:
            group_id = str(group_id)
            if group_id in self.push_config[user_id]["groups"]:
                self.push_config[user_id]["groups"].remove(group_id)
                self._save_push_config()
                return f"✅ 已关闭本群的战绩推送"
        else:
            del self.push_config[user_id]
            self._save_push_config()
            return "✅ 已关闭战绩推送"
        
        return "❌ 未在本群开启战绩推送"
    
    def get_push_status(self, user_id: str) -> str:
        """获取推送状态"""
        user_id = str(user_id)
        
        if user_id not in self.push_config:
            return "❌ 未开启战绩推送"
        
        config = self.push_config[user_id]
        status = "✅ 战绩推送已开启\n"
        status += f"营地ID: {config['camp_id']}\n"
        status += f"状态: {'启用' if config['enabled'] else '暂停'}\n"
        
        if config['groups']:
            status += f"推送群组: {len(config['groups'])}个"
        else:
            status += "推送方式: 私聊"
        
        return status
    
    async def check_new_battles(self):
        """检查新战绩"""
        for user_id, config in self.push_config.items():
            if not config.get("enabled", True):
                continue
            
            try:
                camp_id = config["camp_id"]
                
                # 获取最新战绩
                battle_data = await api_service.get_more_battle_list(camp_id)
                if not battle_data.get("data") or not battle_data["data"].get("list"):
                    continue
                
                battle_list = battle_data["data"]["list"]
                if not battle_list:
                    continue
                
                # 获取最新一场战绩
                latest_battle = battle_list[0]
                battle_id = f"{latest_battle.get('gameSeq')}_{latest_battle.get('gametime')}"
                
                # 检查是否是新战绩
                last_battle_id = self.last_battles.get(user_id)
                
                if last_battle_id != battle_id:
                    # 发现新战绩
                    self.last_battles[user_id] = battle_id
                    self._save_last_battles()
                    
                    # 推送新战绩
                    await self._push_battle(user_id, latest_battle, config)
                    
            except Exception as e:
                logger.error(f"检查用户 {user_id} 战绩失败: {e}", exc_info=True)
    
    async def _push_battle(self, user_id: str, battle: dict, config: dict):
        """推送战绩"""
        try:
            # 构建战绩消息
            result = "✅ 胜利" if battle.get("isWin") == 1 else "❌ 失败"
            hero_name = battle.get("heroName", "未知")
            kda = f"{battle.get('killNum', 0)}/{battle.get('deadNum', 0)}/{battle.get('assistNum', 0)}"
            map_name = battle.get("mapName", "未知")
            score = battle.get("score", 0)
            
            message = f"🎮 【新战绩推送】\n\n"
            message += f"结果: {result}\n"
            message += f"英雄: {hero_name}\n"
            message += f"KDA: {kda}\n"
            message += f"地图: {map_name}\n"
            message += f"评分: {score}\n"
            message += f"时间: {battle.get('gametime', '')}"
            
            # 推送到配置的群组或私聊
            # 注意：这里需要根据AstrBot的API来发送消息
            # 由于我们没有直接的消息发送API，这里只记录日志
            logger.info(f"战绩推送 - 用户 {user_id}: {message}")
            
            # TODO: 实现实际的消息推送
            # 需要使用AstrBot的消息发送API
            
        except Exception as e:
            logger.error(f"推送战绩失败: {e}", exc_info=True)
    
    async def start_push_task(self, interval: int = 60):
        """启动推送任务"""
        logger.info(f"战绩推送任务已启动，检查间隔: {interval}秒")
        
        while True:
            try:
                await self.check_new_battles()
            except Exception as e:
                logger.error(f"战绩推送任务出错: {e}", exc_info=True)
            
            await asyncio.sleep(interval)
    
    def start(self, interval: int = 60):
        """启动推送服务"""
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self.start_push_task(interval))
            logger.info("战绩推送服务已启动")
    
    def stop(self):
        """停止推送服务"""
        if self.task and not self.task.done():
            self.task.cancel()
            logger.info("战绩推送服务已停止")
