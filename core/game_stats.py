"""
Game data query module
"""

import os
import json
import base64
import time
import re
from datetime import datetime
from typing import Optional
from astrbot.api import logger
from .api_service import api_service


class GameStatsQuery:
    """游戏数据查询类"""
    
    def __init__(self, data_dir, plugin_instance):
        self.data_dir = data_dir
        self.plugin = plugin_instance
    
    def _get_render_options(self):
        """获取图片渲染配置选项（使用插件统一配置）"""
        return self.plugin.get_render_options()

    async def get_homepage(self, camp_id: str, event, user_id: str = None):
        """获取王者主页"""
        try:
            # 获取调试模式配置
            debug_mode = self.plugin.config.get("debug_mode", False)
            
            if debug_mode:
                logger.info(f"开始查询王者主页，营地ID: {camp_id}")
            
            # 获取用户资料
            profile_data = await api_service.get_profile(camp_id)
            
            if debug_mode:
                logger.info(f"API响应完整数据: {profile_data}")
            
           
            return_code = profile_data.get("returnCode")
            
            if return_code == -30107:
                yield event.plain_result("❌ 获取数据失败，请稍后重试")
                return
            
            if return_code == -10107:
                yield event.plain_result(f"❌ ID: {camp_id}\n召唤师隐藏了主页信息，无法查看")
                return
            
            profile = profile_data["data"]
            role_list = profile.get("roleList", [])
            
            if not role_list:
                yield event.plain_result("❌ 未找到角色数据")
                return
            
            # 检查用户是否选择了特定角色
            current_role = None
            is_custom_role = False  # 标记是否使用了自定义选择的角色
            target_role_id = profile.get("targetRoleId")
            
            if user_id:
                if debug_mode:
                    logger.info(f"检查用户 {user_id} 的角色选择")
                selected_role_id = self.plugin.account_manager.get_selected_role(user_id)
                if debug_mode:
                    logger.info(f"获取到选择的角色ID: {selected_role_id}")
                
                if selected_role_id:
                    # 查找用户选择的角色
                    for role in role_list:
                        if role.get("roleId") == selected_role_id:
                            current_role = role
                            # 判断是否是非默认角色
                            if selected_role_id != target_role_id:
                                is_custom_role = True
                            if debug_mode:
                                logger.info(f"使用用户选择的角色: {selected_role_id} - {role.get('roleName')}, 是否自定义: {is_custom_role}")
                                logger.info(f"选择的角色完整信息: {role}")
                            break
                    
                    if not current_role:
                        logger.warning(f"未找到用户选择的角色 {selected_role_id}，使用默认角色")
            
            # 如果没有选择角色，使用默认逻辑
            if not current_role:
                # 找到目标角色
                for role in role_list:
                    if role.get("roleId") == target_role_id:
                        current_role = role
                        break
                
                if not current_role:
                    # 如果没找到，使用第一个角色
                    current_role = role_list[0]
            

            head_data = profile.get("head", {})
            mods = head_data.get("mods", [])
            
            # 找到关键的mod数据
            mode_10v10 = None  # modId: 708
            mode_5v5 = None    # modId: 701
            mode_peak = None   # modId: 702
            
            stats = {}
            for mod in mods:
                mod_id = mod.get("modId")
                name = mod.get("name", "")
                content = mod.get("content", "0")
                param1 = mod.get("param1", "")
                

                if mod_id == 708:  # 10v10模式
                    mode_10v10 = mod
                elif mod_id == 701:  # 5v5模式
                    mode_5v5 = mod
                elif mod_id == 702:  # 巅峰赛
                    mode_peak = mod
                elif mod_id == 304:  # 战斗力
                    stats["power"] = content
                elif mod_id == 401:  # 总场次
                    stats["total"] = content
                elif mod_id == 408:  # MVP
                    stats["mvp"] = content
                elif mod_id == 409:  # 胜率
                    stats["win_rate"] = content
                elif mod_id == 201:  # 英雄
                    stats["hero"] = content
                elif mod_id == 202:  # 皮肤
                    stats["skin"] = content
            

            if mode_10v10:
                try:
                    param_data = json.loads(mode_10v10.get("param1", "{}"))
                    rank_star = param_data.get("rankingStar", "0")
                    stats["rank_10v10"] = f"{mode_10v10.get('name', '未知')} {rank_star}星"
                except:
                    stats["rank_10v10"] = mode_10v10.get("name", "未知")
            
            if mode_5v5:
                try:
                    param_data = json.loads(mode_5v5.get("param1", "{}"))
                    rank_star = param_data.get("rankingStar", "0")
                    stats["rank_5v5"] = f"{mode_5v5.get('name', '未知')} {rank_star}星"
                except:
                    stats["rank_5v5"] = mode_5v5.get("name", "未知")
            
            if mode_peak:
                stats["peak"] = mode_peak.get("name", "巅峰赛")
            

            role_name = current_role.get("roleName", "未知")
            rank_name = current_role.get("roleJobName", "未知")
            game_level = current_role.get("gameLevel", 0)
            area_name = current_role.get("areaName", "未知")  # 分区
            server_name = current_role.get("serverName", "未知")  # 区服
            role_text = current_role.get("roleText", "未知")
            

            game_online_status = current_role.get("gameOnline", 0)
            game_online_map = {
                0: "离线",
                1: "在线",
                2: "游戏中"
            }
            game_online = game_online_map.get(game_online_status, "未知")
            

            online_time = current_role.get("onlineTime", 0)
            offline_time = current_role.get("offlineTime", 0)
            
            def format_time(timestamp):
                if timestamp == 0:
                    return "未知"
                try:
                    dt = datetime.fromtimestamp(timestamp)
                    now = datetime.now()
                    if dt.date() == now.date():
                        return f"今天{dt.strftime('%H:%M')}"
                    else:
                        return dt.strftime("%Y/%m/%d")
                except:
                    return "未知"
            
            info_lines = [
                "🎮 【王者荣耀主页】",
                "",
                f"👤 昵称: {role_name}",
                f"🆔 营地ID: {camp_id}",
                f"🎯 等级: {game_level}",
                f"🏠 区服: {role_text}",
                f"📱 状态: {game_online}",
                "",
                f"⚔️ 5v5段位: {stats.get('rank_5v5', rank_name)}",
                f"🎯 10v10段位: {stats.get('rank_10v10', '未知')}",
                "",
                f"⚡ 战斗力: {stats.get('power', '0')}",
                f"📊 总场次: {stats.get('total', '0')}",
                f"📈 胜率: {stats.get('win_rate', '0%')}",
                f"🎖️ MVP次数: {stats.get('mvp', '0')}",
                "",
                f"🦸 英雄: {stats.get('hero', '0/0')}",
                f"👗 皮肤: {stats.get('skin', '0/0')}",
                "",
                f"🟢 上次上线: {format_time(online_time)}",
                f"🔴 上次离线: {format_time(offline_time)}",
                "",
                "💡 使用【查询战绩】查看详细战绩"
            ]
            
            logger.info(f"王者主页查询成功，用户: {role_name}")
            
            def img_to_base64(img_name):
                plugin_root = os.path.dirname(os.path.dirname(__file__))
                
                try:
                    img_path = os.path.join(plugin_root, "assets", img_name)
                    with open(img_path, "rb") as f:
                        data = base64.b64encode(f.read()).decode('utf-8')
                        logger.info(f"从assets目录读取图片成功: {img_name}")
                        return data
                except:
                    pass
                
                try:
                    img_path = os.path.join(plugin_root, "resources", "img", img_name)
                    with open(img_path, "rb") as f:
                        data = base64.b64encode(f.read()).decode('utf-8')
                        logger.info(f"从resources/img读取图片成功: {img_name}")
                        return data
                except Exception as e:
                    logger.error(f"读取图片失败 {img_name}: {e}")
                    return ""
            
            plugin_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__))).replace("\\", "/")
            
            bg_img_base64 = img_to_base64("bgImgV2.png")
            if bg_img_base64:
                logger.info(f"背景图片读取成功，大小: {len(bg_img_base64)} 字符")
            else:
                logger.warning("背景图片读取失败，将使用渐变色背景")
            
            mod_list = []
            combat_data = None
            for mod in mods:
                if mod.get("stype") == 0:
                    mod_list.append({
                        "icon": mod.get("icon", ""),
                        "content": mod.get("content", "0"),
                        "name": mod.get("name", ""),
                        "showStyle": mod.get("showStyle", 0)
                    })
                elif mod.get("stype") == 1:
                    combat_data = {
                        "icon": mod.get("icon", ""),
                        "content": mod.get("content", "0"),
                        "name": mod.get("name", "战斗力")
                    }
            
            rank_star_5v5 = 0
            star_img = ""
            rank_icon = ""
            if mode_5v5:
                try:
                    param_data = json.loads(mode_5v5.get("param1", "{}"))
                    rank_star_5v5 = param_data.get("rankingStar", 0)
                    star_img = param_data.get("starImg", "")
                except:
                    pass
                rank_icon = mode_5v5.get("icon", "")
            
            rank_star_10v10 = 0
            if mode_10v10:
                try:
                    param_data = json.loads(mode_10v10.get("param1", "{}"))
                    rank_star_10v10 = param_data.get("rankingStar", 0)
                except:
                    pass
            
            mode_peak_race_data = {"param1": {"desc": "未参加", "roleIcon": "", "flagPag": "1"}, "icon": ""}
            if mode_peak:
                try:
                    param1 = json.loads(mode_peak.get("param1", "{}"))
                    flag_pag = param1.get("flagPag", "1.pag")
                    if "/" in flag_pag:
                        flag_pag = flag_pag.split("/")[-1]
                    if ".pag" in flag_pag:
                        flag_pag = flag_pag.split(".")[0]
                    mode_peak_race_data = {
                        "icon": mode_peak.get("icon", ""),
                        "param1": {
                            "desc": param1.get("desc", "未参加"),
                            "roleIcon": param1.get("roleIcon", current_role.get("roleIcon", "")),
                            "flagPag": flag_pag
                        }
                    }
                except Exception as e:
                    logger.error(f"解析巅峰赛数据失败: {e}")
            
            rank_5v5_text = stats.get('rank_5v5', rank_name)
            flag_img = '4'
            if any(x in rank_5v5_text for x in ['青铜', '白银', '黄金', '铂金']):
                flag_img = '1'
            elif any(x in rank_5v5_text for x in ['钻石', '星耀']):
                flag_img = '2'
            elif '最强王者' in rank_5v5_text:
                flag_img = '3'
            
            is_king = '王者' in rank_5v5_text
            is_offline = game_online == '离线'
            honor = 'honor' if is_king else 'roleJob'
            
            # 读取旗帜和荣耀图标为base64
            flag_img_base64 = img_to_base64(f"flag{flag_img}.png")
            honor_img_base64 = img_to_base64(f"{honor}.png")
            star_img_base64 = img_to_base64("star.png") if is_king else ""
            cube_img_base64 = img_to_base64("cube.png")
            peak_avatar_border_base64 = img_to_base64("modePeakRace-avatar.png")
            
            # 读取巅峰赛旗帜
            peak_flag_num = mode_peak_race_data.get("param1", {}).get("flagPag", "1")
            peak_flag_img_base64 = img_to_base64(f"flag{peak_flag_num}.png")
            
            template_data = {
                "plugin_dir": plugin_dir,
                "bg_img_base64": bg_img_base64,
                "flag_img_base64": flag_img_base64,
                "honor_img_base64": honor_img_base64,
                "star_img_base64": star_img_base64,
                "cube_img_base64": cube_img_base64,
                "peak_avatar_border_base64": peak_avatar_border_base64,
                "peak_flag_img_base64": peak_flag_img_base64,
                "roleIcon": current_role.get("roleIcon", ""),
                "roleName": role_name,
                "gameLevel": game_level,
                "gameOnline": game_online,
                "rank10v10": f"{mode_10v10.get('name', '未知')} {rank_star_10v10}星" if mode_10v10 else "未知",
                "rank5v5": f"{mode_5v5.get('name', '未知')} {rank_star_5v5}星" if mode_5v5 else "未知",
                "areaName": area_name,
                "roleText": role_text,
                "flagImg": flag_img,
                "rankIcon": rank_icon,
                "starImg": star_img,
                "honor": honor,
                "isKing": is_king,
                "rankingStar": rank_star_5v5,
                "isOffline": is_offline,
                "onlineTime": format_time(online_time),
                "offlineTime": format_time(offline_time),
                "mod": mod_list,
                "combat": combat_data,
                "modePeakRace": mode_peak_race_data
            }
            
            try:
                plugin_root = os.path.dirname(os.path.dirname(__file__))
                template_path = os.path.join(plugin_root, "templates", "homepage_full.html")
                with open(template_path, "r", encoding="utf-8") as f:
                    html_template = f.read()
                
                url = await self.plugin.html_render(html_template, template_data, options=self._get_render_options())
                yield event.image_result(url)
            except Exception as e:
                logger.error(f"主页渲染图片失败，使用文本回退，错误: {e}", exc_info=True)
                text = "\n".join(info_lines)
                yield event.plain_result(text)
            
        except Exception as e:
            logger.error(f"获取主页失败，营地ID: {camp_id}, 错误: {e}", exc_info=True)
            yield event.plain_result(
                f"❌ 查询失败: {str(e)}\n\n💡 可能的原因:\n"
                f"• 网络连接问题\n"
                f"• API服务暂时不可用\n"
                f"• 营地ID格式错误\n\n"
                f"请稍后重试或检查日志"
            )

    async def query_battle_stats(self, camp_id: str, event, index: Optional[int] = None):
        """查询战绩"""
        try:
            # 获取战绩列表
            battle_data = await api_service.get_more_battle_list(camp_id)
            
            if not battle_data.get("data") or not battle_data["data"].get("list"):
                yield event.plain_result("❌ 未查询到战绩数据")
                return
            
            battle_list = battle_data["data"]["list"]
            
            # 如果指定了序号，查询单场详情
            if index is not None:
                if index < 1 or index > len(battle_list):
                    yield event.plain_result(
                        f"❌ 序号超出范围，当前最多可查询{len(battle_list)}场战绩"
                    )
                    return
                
                async for result in self._get_battle_detail(camp_id, battle_list[index - 1], index, event):
                    yield result
                return
            
            # 显示战绩列表（文本版本，用于回退）
            info_lines = [
                "📊 【最近战绩】",
                f"营地ID: {camp_id}",
                ""
            ]
            
            for i, battle in enumerate(battle_list[:15], 1):  # 只显示前15场
                result = "✅胜利" if battle.get("isWin") == 1 else "❌失败"
                hero_name = battle.get("heroName", "未知")
                kda = f"{battle.get('killNum', 0)}/{battle.get('deadNum', 0)}/{battle.get('assistNum', 0)}"
                map_name = battle.get("mapName", "未知")
                
                info_lines.append(
                    f"{i}. {result} | {hero_name} | {kda} | {map_name}"
                )
            
            info_lines.extend([
                "",
                "💡 使用【查询战绩 [序号]】查看详细数据",
                f"💡 例如: 查询战绩 1"
            ])
            
            # 使用HTML渲染
            try:
                # 处理战绩数据
                processed_data = []
                for battle in battle_list[:30]:

                    tags = []
                    desc = battle.get("desc", "")
                    if desc:
                        tags = [tag.strip() for tag in desc.split(",") if tag.strip()]
                    

                    game_time = battle.get("gametime", "")
                    if game_time:
                        try:
                            dt = datetime.strptime(game_time, "%Y-%m-%d %H:%M:%S")
                            game_time = dt.strftime("%m-%d %H:%M")
                        except:
                            pass
                    

                    used_time = battle.get("usedTime", 0)
                    minutes = used_time // 60
                    seconds = used_time % 60
                    game_duration = f"{minutes}分{seconds}秒"
                    
                    processed_data.append({
                        "gameType": battle.get("mapName", "未知"),
                        "gameTime": game_time,
                        "gameDuration": game_duration,
                        "gameResult": "胜利" if battle.get("isWin") == 1 else "失败",
                        "killCnt": battle.get("killNum", 0),
                        "deadCnt": battle.get("deadNum", 0),
                        "assistCnt": battle.get("assistNum", 0),
                        "heroIcon": battle.get("heroIcon", ""),
                        "tags": tags,
                        "gradeGame": battle.get("score", 0)
                    })
                
                template_data = {
                    "data": processed_data
                }
                
                # 读取HTML模板（从插件根目录）
                plugin_root = os.path.dirname(os.path.dirname(__file__))
                template_path = os.path.join(plugin_root, "templates", "battle_list.html")
                with open(template_path, "r", encoding="utf-8") as f:
                    html_template = f.read()
                
                # 使用 html_render 渲染HTML模板为图片
                # 使用配置中的渲染选项
                url = await self.plugin.html_render(html_template, template_data, options=self._get_render_options())
                yield event.image_result(url)
            except Exception as e:
                logger.error(f"战绩渲染图片失败，使用文本回退，错误: {e}", exc_info=True)
                text = "\n".join(info_lines)
                yield event.plain_result(text)
            
        except Exception as e:
            logger.error(f"查询战绩失败: {e}")
            yield event.plain_result(f"❌ 查询失败: {str(e)}")

    async def _get_battle_detail(self, camp_id: str, battle: dict, index: int, event):
        """获取单场战斗详情"""
        try:
            # 提取必要参数
            battle_type = battle.get("battleType")
            game_svr_id = battle.get("gameSvrId")
            relay_svr_id = battle.get("relaySvrId")
            game_seq = battle.get("gameSeq")
            
            battle_url = battle.get("battleDetailUrl", "")
            match = re.search(r"toAppRoleId=(\d+)", battle_url)
            target_role_id = match.group(1) if match else "0"
            
            detail_data = await api_service.get_battle_detail(
                camp_id, battle_type, game_svr_id, relay_svr_id, target_role_id, game_seq
            )
            
            if not detail_data.get("data"):
                yield event.plain_result("❌ 获取战斗详情失败")
                return
            
            detail = detail_data["data"]
            
            result = "✅ 胜利" if battle.get("isWin") == 1 else "❌ 失败"
            info_lines = [
                f"🎮 【战绩详情 #{index}】",
                "",
                f"📌 结果: {result}",
                f"🦸 英雄: {battle.get('heroName', '未知')}",
                f"🗺️ 地图: {battle.get('mapName', '未知')}",
                f"⏱️ 时长: {self._format_duration(battle.get('usedTime', 0))}",
                "",
                "📊 数据统计:",
                f"⚔️ 击杀: {battle.get('killNum', 0)}",
                f"💀 死亡: {battle.get('deadNum', 0)}",
                f"🤝 助攻: {battle.get('assistNum', 0)}",
                f"💰 金币: {detail.get('totalMoney', 0)}",
                f"🏅 评分: {detail.get('score', 0)}",
                f"🎯 伤害: {detail.get('hurt', 0)}",
                f"🛡️ 承伤: {detail.get('hurtTaken', 0)}",
            ]
            
            yield event.plain_result("\n".join(info_lines))
            
        except Exception as e:
            logger.error(f"获取战斗详情失败: {e}")
            yield event.plain_result(f"❌ 获取详情失败: {str(e)}")

    def _calc_win_rate(self, win_num: int, total_num: int) -> str:
        """计算胜率"""
        if total_num == 0:
            return "0%"
        return f"{(win_num / total_num * 100):.1f}%"

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}分{secs}秒"
