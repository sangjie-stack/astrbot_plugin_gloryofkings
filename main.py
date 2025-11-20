"""
AstrBot 王者荣耀插件
提供王者荣耀数据查询功能
"""

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register, StarTools
from astrbot.api import logger, AstrBotConfig

from .core.account_manager import AccountManager
from .core.game_stats import GameStatsQuery
from .core.hero_query import HeroQuery
from .core.battle_push import BattlePushManager

HELP_TEXT = """
【王者荣耀插件帮助】

📋 账号管理
• 绑定营地 [ID] - 绑定王者营地ID
• 切换营地 [序号] - 切换使用的营地ID
• 删除营地 [序号] - 删除绑定的营地ID
• 我的ID - 查看已绑定的营地ID列表

📊 数据查询
• 王者主页 - 查看游戏信息概览
• 查询战绩 - 查看最近30场战绩
• 查询战绩 [序号] - 查看指定场次详细数据
• 查战力 [英雄名] - 查询指定英雄的战力排名
• 查皮肤 [英雄名] - 查询指定英雄的皮肤

💡 提示
• 首次使用请先绑定营地ID
• 营地ID获取方式：王者营地APP - 我的 - 游戏资料
"""

@register("astrbot_plugin_gloryofkings", "球球", "王者荣耀数据查询插件", "v1.1.0")
class GloryOfKingsPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config or {}
        self.plugin_data_dir = StarTools.get_data_dir("astrbot_plugin_gloryofkings")
        
        # 预初始化属性，避免在initialize失败时报错
        self.account_manager = None
        self.game_stats = None
        self.hero_query = None
        self.battle_push = None
    
    def get_render_options(self):
        """获取统一的图片渲染配置选项"""
        render_scale = self.config.get("render_scale", 2)
        render_quality = self.config.get("render_quality", 100)
        
        try:
            render_scale = int(render_scale)
            render_quality = int(render_quality)
        except (ValueError, TypeError):
            logger.warning(f"渲染配置参数类型错误，使用默认值。scale={render_scale}, quality={render_quality}")
            render_scale = 2
            render_quality = 100
        
        render_scale = max(1, min(3, render_scale))
        render_quality = max(1, min(100, render_quality))
        
        return {
            "full_page": True,
            "timeout": 30000,
            "device_scale_factor": render_scale,
            "quality": render_quality
        }

    async def initialize(self):
        """初始化插件"""
        try:
            logger.info("开始初始化王者荣耀插件...")
            
            self.account_manager = AccountManager(self.plugin_data_dir)
            self.game_stats = GameStatsQuery(self.plugin_data_dir, self)
            self.hero_query = HeroQuery(self)
            self.battle_push = BattlePushManager(self)
            
            self.battle_push.start(interval=60)
            
            logger.info("王者荣耀插件初始化成功！")
        except Exception as e:
            logger.error(f"王者荣耀插件初始化失败: {e}", exc_info=True)
            raise

    @filter.regex(r"[/!！]?绑定营地\s*(.+)")
    async def bind_account(self, event: AstrMessageEvent):
        """绑定营地ID"""
        import re
        logger.info(f"收到绑定营地指令: {event.message_str}")
        match = re.search(r"[/!！]?绑定营地\s*(.+)", event.message_str)
        if not match:
            yield event.plain_result("❌ 请提供营地ID\n用法: /绑定营地 [ID] 或 绑定营地[ID]")
            return
        
        camp_id = match.group(1).strip()
        logger.info(f"提取到营地ID: {camp_id}")
        if not camp_id:
            yield event.plain_result("❌ 请提供营地ID\n用法: /绑定营地 [ID] 或 绑定营地[ID]")
            return
        
        user_id = event.get_sender_id()
        result = await self.account_manager.bind_id(user_id, camp_id)
        
        try:
            async for res in self._render_account_result(event, "绑定", camp_id, user_id):
                yield res
        except Exception as e:
            logger.error(f"账号管理页面渲染失败，使用文本回退，错误: {e}", exc_info=True)
            yield event.plain_result(result)

    @filter.regex(r"[/!！]?切换营地\s*(\d+)")
    async def switch_account(self, event: AstrMessageEvent):
        """切换营地ID"""
        import re
        logger.info(f"收到切换营地指令: {event.message_str}")
        match = re.search(r"[/!！]?切换营地\s*(\d+)", event.message_str)
        if not match:
            yield event.plain_result("❌ 请提供序号\n用法: /切换营地 [序号] 或 切换营地[序号]")
            return
        
        index = int(match.group(1))
        logger.info(f"切换到序号: {index}")
        user_id = event.get_sender_id()
        result = await self.account_manager.switch_id(user_id, index - 1)
        
        try:
            camp_id = self.account_manager.get_current_id(user_id)
            async for res in self._render_account_result(event, "切换", camp_id or "未知", user_id):
                yield res
        except Exception as e:
            logger.error(f"账号管理页面渲染失败，使用文本回退，错误: {e}", exc_info=True)
            yield event.plain_result(result)

    @filter.regex(r"[/!！]?删除营地\s*(\d+)")
    async def delete_account(self, event: AstrMessageEvent):
        """删除营地ID"""
        import re
        logger.info(f"收到删除营地指令: {event.message_str}")
        match = re.search(r"[/!！]?删除营地\s*(\d+)", event.message_str)
        if not match:
            yield event.plain_result("❌ 请提供序号\n用法: /删除营地 [序号] 或 删除营地[序号]")
            return
        
        index = int(match.group(1))
        logger.info(f"删除序号: {index}")
        user_id = event.get_sender_id()
        result = await self.account_manager.delete_id(user_id, index - 1)
        
        try:
            camp_id = self.account_manager.get_current_id(user_id)
            async for res in self._render_account_result(event, "删除", camp_id or "未知", user_id):
                yield res
        except Exception as e:
            logger.error(f"账号管理页面渲染失败，使用文本回退，错误: {e}", exc_info=True)
            yield event.plain_result(result)

    @filter.command("我的ID")
    async def my_ids(self, event: AstrMessageEvent):
        """查看已绑定的营地ID"""
        user_id = event.get_sender_id()
        result = await self.account_manager.get_id_list(user_id)
        
        try:
            camp_id = self.account_manager.get_current_id(user_id)
            async for res in self._render_account_result(event, "查看", camp_id or "未知", user_id):
                yield res
        except Exception as e:
            logger.error(f"账号管理页面渲染失败，使用文本回退，错误: {e}", exc_info=True)
            yield event.plain_result(result)

    @filter.command("王者主页")
    async def homepage(self, event: AstrMessageEvent):
        """查看王者主页"""
        user_id = event.get_sender_id()
        camp_id = self.account_manager.get_current_id(user_id)
        
        if not camp_id:
            yield event.plain_result("❌ 请先绑定营地ID\n使用: 绑定营地 [ID]")
            return
        
        async for result in self.game_stats.get_homepage(camp_id, event, user_id):
            yield result
    
    @filter.command("王者角色列表")
    async def list_roles(self, event: AstrMessageEvent):
        """查看可用的王者角色列表"""
        user_id = event.get_sender_id()
        camp_id = self.account_manager.get_current_id(user_id)
        
        if not camp_id:
            yield event.plain_result("❌ 请先绑定营地ID\n使用: 绑定营地 [ID]")
            return
        
        try:
            from .core.api_service import ApiService
            api_service = ApiService()
            
            # 获取用户资料
            profile_data = await api_service.get_profile(camp_id)
            
            if not profile_data or profile_data.get("result") != 0:
                yield event.plain_result("❌ 获取角色列表失败")
                return
            
            profile = profile_data["data"]
            role_list = profile.get("roleList", [])
            
            if not role_list:
                yield event.plain_result("❌ 未找到角色数据")
                return
            
            # 获取当前选择的角色
            selected_role_id = self.account_manager.get_selected_role(user_id)
            
            # 构建角色列表
            lines = ["🎮 【王者角色列表】\n"]
            for i, role in enumerate(role_list, 1):
                role_id = role.get("roleId")
                role_name = role.get("roleName", "未知")
                rank_name = role.get("shortRoleJobName", "未知")
                server_name = role.get("serverName", "未知")
                
                # 标记当前选择的角色
                prefix = "✅" if role_id == selected_role_id else f"{i}."
                lines.append(f"{prefix} {role_name} ({rank_name}) - {server_name}")
                lines.append(f"   角色ID: {role_id}\n")
            
            lines.append("\n💡 使用【选择角色 序号】切换查看的角色")
            lines.append("💡 使用【清除角色选择】恢复默认角色")
            
            yield event.plain_result("\n".join(lines))
            
        except Exception as e:
            logger.error(f"获取角色列表失败: {e}", exc_info=True)
            yield event.plain_result(f"❌ 获取角色列表失败: {e}")
    
    @filter.regex(r"[/!！]?选择角色\s*(\d+)")
    async def select_role(self, event: AstrMessageEvent):
        """选择要查看的王者角色"""
        import re
        user_id = event.get_sender_id()
        camp_id = self.account_manager.get_current_id(user_id)
        
        if not camp_id:
            yield event.plain_result("❌ 请先绑定营地ID\n使用: 绑定营地 [ID]")
            return
        
        match = re.search(r"[/!！]?选择角色\s*(\d+)", event.message_str)
        if not match:
            yield event.plain_result("❌ 请提供角色序号\n用法: 选择角色 [序号]")
            return
        
        index = int(match.group(1)) - 1
        
        try:
            from .core.api_service import ApiService
            api_service = ApiService()
            
            # 获取用户资料
            profile_data = await api_service.get_profile(camp_id)
            
            if not profile_data or profile_data.get("result") != 0:
                yield event.plain_result("❌ 获取角色列表失败")
                return
            
            profile = profile_data["data"]
            role_list = profile.get("roleList", [])
            
            if not role_list:
                yield event.plain_result("❌ 未找到角色数据")
                return
            
            if index < 0 or index >= len(role_list):
                yield event.plain_result(f"❌ 角色序号无效，请输入 1-{len(role_list)}")
                return
            
            selected_role = role_list[index]
            role_id = selected_role.get("roleId")
            role_name = selected_role.get("roleName", "未知")
            rank_name = selected_role.get("shortRoleJobName", "未知")
            server_name = selected_role.get("serverName", "未知")
            
            # 保存选择
            self.account_manager.set_selected_role(user_id, role_id)
            
            yield event.plain_result(
                f"✅ 已选择角色\n\n"
                f"👤 {role_name}\n"
                f"🎯 {rank_name}\n"
                f"🏠 {server_name}\n\n"
                f"💡 现在使用【王者主页】将查看此角色的数据"
            )
            
        except Exception as e:
            logger.error(f"选择角色失败: {e}", exc_info=True)
            yield event.plain_result(f"❌ 选择角色失败: {e}")
    
    @filter.command("清除角色选择")
    async def clear_role_selection(self, event: AstrMessageEvent):
        """清除角色选择，恢复默认"""
        user_id = event.get_sender_id()
        self.account_manager.clear_selected_role(user_id)
        yield event.plain_result("✅ 已清除角色选择\n💡 现在将使用默认角色（最常用角色）")

    @filter.regex(r"[/!！]?查询战绩\s*(\d*)")
    async def query_battle(self, event: AstrMessageEvent):
        """查询战绩"""
        import re
        logger.info(f"收到查询战绩指令: {event.message_str}")
        match = re.search(r"[/!！]?查询战绩\s*(\d*)", event.message_str)
        index = None
        if match and match.group(1):
            index = int(match.group(1))
        
        user_id = event.get_sender_id()
        camp_id = self.account_manager.get_current_id(user_id)
        
        if not camp_id:
            yield event.plain_result("❌ 请先绑定营地ID\n使用: 绑定营地 [ID]")
            return
        
        async for result in self.game_stats.query_battle_stats(camp_id, event, index):
            yield result

    @filter.regex(r"[/!！]?查战力\s*(.+)")
    async def query_hero_power(self, event: AstrMessageEvent):
        """查询英雄战力"""
        import re
        logger.info(f"收到查战力指令: {event.message_str}")
        logger.info(f"消息原始内容: repr={repr(event.message_str)}")
        match = re.search(r"[/!！]?查战力\s*(.+)", event.message_str)
        if not match:
            yield event.plain_result("❌ 请提供英雄名称\n用法: /查战力 [英雄名] 或 查战力[英雄名]")
            return
        
        hero_name = match.group(1).strip()
        logger.info(f"提取到英雄名: {hero_name}")
        async for result in self.hero_query.query_hero_power(hero_name, event):
            yield result

    @filter.regex(r"[/!！]?查皮肤\s*(.+)")
    async def query_hero_skin(self, event: AstrMessageEvent):
        """查询英雄皮肤"""
        import re
        logger.info(f"收到查皮肤指令: {event.message_str}")
        logger.info(f"消息原始内容: repr={repr(event.message_str)}")
        match = re.search(r"[/!！]?查皮肤\s*(.+)", event.message_str)
        if not match:
            yield event.plain_result("❌ 请提供英雄名称\n用法: /查皮肤 [英雄名] 或 查皮肤[英雄名]")
            return
        
        hero_name = match.group(1).strip()
        logger.info(f"提取到英雄名: {hero_name}")
        async for result in self.hero_query.query_hero_skin(hero_name, event):
            yield result

    @filter.command("王者帮助")
    async def show_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        try:
            # 读取HTML模板
            import os
            template_path = os.path.join(os.path.dirname(__file__), "templates", "help.html")
            with open(template_path, "r", encoding="utf-8") as f:
                html_template = f.read()
            
            # 使用 html_render 渲染HTML模板为图片（帮助页面是静态的，不需要数据）
            url = await self.html_render(html_template, {}, options=self.get_render_options())
            yield event.image_result(url)
        except Exception as e:
            logger.error(f"帮助页面渲染失败，使用文本回退，错误: {e}", exc_info=True)
            yield event.plain_result(HELP_TEXT)
    
    @filter.command("开启战绩推送")
    async def enable_battle_push(self, event: AstrMessageEvent):
        """开启战绩推送"""
        user_id = event.get_sender_id()
        camp_id = self.account_manager.get_current_id(user_id)
        
        if not camp_id:
            yield event.plain_result("❌ 请先绑定营地ID\n使用: 绑定营地 [ID]")
            return
        
        # 获取群组ID（如果在群聊中）
        group_id = getattr(event, 'group_id', None)
        
        result = self.battle_push.add_push_user(user_id, camp_id, group_id)
        yield event.plain_result(result)
    
    @filter.command("关闭战绩推送")
    async def disable_battle_push(self, event: AstrMessageEvent):
        """关闭战绩推送"""
        user_id = event.get_sender_id()
        group_id = getattr(event, 'group_id', None)
        
        result = self.battle_push.remove_push_user(user_id, group_id)
        yield event.plain_result(result)
    
    @filter.command("战绩推送状态")
    async def battle_push_status(self, event: AstrMessageEvent):
        """查看战绩推送状态"""
        user_id = event.get_sender_id()
        result = self.battle_push.get_push_status(user_id)
        yield event.plain_result(result)

    async def _render_account_result(self, event, operation_type, camp_id, user_id):
        """渲染账号管理结果页面"""
        import os
        from datetime import datetime
        
        id_list_str = await self.account_manager.get_id_list(user_id)
        
        template_data = {
            "type": operation_type,
            "wzryId": camp_id,
            "idList": id_list_str,
            "functionList": [
                "【/王者主页】查看游戏信息概览",
                "【/查询战绩】查询最近30条战绩",
                "【/查战力 英雄名】查询英雄战力",
                "【/查皮肤 英雄名】查询英雄皮肤"
            ],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        template_path = os.path.join(os.path.dirname(__file__), "templates", "account_manage.html")
        with open(template_path, "r", encoding="utf-8") as f:
            html_template = f.read()
        
        url = await self.html_render(html_template, template_data, options=self.get_render_options())
        yield event.image_result(url)

    async def terminate(self):
        """插件卸载时调用"""
        self.battle_push.stop()
        logger.info("王者荣耀插件已关闭")
