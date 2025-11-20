"""
英雄查询模块
处理英雄战力、皮肤等查询
"""

import os
import aiohttp
from astrbot.api import logger
from .api_service import api_service


class HeroQuery:
    """英雄查询类"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self._hero_list_cache = None
    
    def _get_render_options(self):
        """获取图片渲染配置选项"""
        return self.plugin.get_render_options()

    async def query_hero_power(self, hero_name: str, event):
        """查询英雄战力"""
        try:
            logger.info(f"开始查询英雄战力，英雄名: {hero_name}")
            power_data = await api_service.get_hero_fighting_capacity(hero_name)
            logger.info(f"战力数据获取结果: {power_data}")
            
            if not power_data:
                yield event.plain_result(
                    f"❌ 未找到英雄【{hero_name}】的战力数据\n请检查英雄名称是否正确"
                )
                return
            
            if not power_data or len(power_data) == 0:
                yield event.plain_result(f"❌ 未找到英雄【{hero_name}】的战力数据")
                return
            
            first_data = power_data[0].get("data", {})
            hero_alias = first_data.get("alias", hero_name)
            
            info_lines = [
                f"⚔️ 【{hero_name} 战力排行】",
                f"📝 别名: {hero_alias}",
                ""
            ]
            
            for platform_data in power_data:
                platform = platform_data.get("platform", "未知")
                data = platform_data.get("data", {})
                
                info_lines.append(f"📱 {platform}:")
                
                guobiao = data.get("guobiao", "0")
                info_lines.append(f"  🏆 国标: {guobiao}")
                
                province_name = data.get("province", "未知")
                province_power = data.get("provincePower", "0")
                info_lines.append(f"  🏙️ 省: {province_name} - {province_power}")
                
                city_name = data.get("city", "未知")
                city_power = data.get("cityPower", "0")
                info_lines.append(f"  🌆 市: {city_name} - {city_power}")
                
                area_name = data.get("area", "未知")
                area_power = data.get("areaPower", "0")
                info_lines.append(f"  🏘️ 区: {area_name} - {area_power}")
                
                update_time = data.get("updatetime", "未知")
                info_lines.append(f"  🕐 更新: {update_time}")
                
                info_lines.append("")
            
            first_platform_data = power_data[0].get("data", {}) if power_data else {}
            
            min_guobiao = float('inf')
            min_province_power = float('inf')
            min_city_power = float('inf')
            min_area_power = float('inf')
            
            platform_list = []
            for platform_data in power_data:
                platform = platform_data.get("platform", "未知")
                data = platform_data.get("data", {})
                
                try:
                    guobiao = int(data.get("guobiao", "0"))
                    province_power = int(data.get("provincePower", "0"))
                    city_power = int(data.get("cityPower", "0"))
                    area_power = int(data.get("areaPower", "0"))
                    
                    min_guobiao = min(min_guobiao, guobiao)
                    min_province_power = min(min_province_power, province_power)
                    min_city_power = min(min_city_power, city_power)
                    min_area_power = min(min_area_power, area_power)
                except:
                    pass
                
                platform_list.append({
                    "platform": platform,
                    "province": data.get("province", "未知"),
                    "provincePower": data.get("provincePower", "0"),
                    "city": data.get("city", "未知"),
                    "cityPower": data.get("cityPower", "0"),
                    "area": data.get("area", "未知"),
                    "areaPower": data.get("areaPower", "0"),
                    "guobiao": data.get("guobiao", "0"),
                    "updatetime": data.get("updatetime", "未知")
                })
            
            template_data = {
                "photo": first_platform_data.get("photo", ""),
                "name": first_platform_data.get("name", hero_name),
                "alias": first_platform_data.get("alias", hero_alias),
                "minStats": {
                    "guobiao": str(min_guobiao) if min_guobiao != float('inf') else "0",
                    "provincePower": str(min_province_power) if min_province_power != float('inf') else "0",
                    "cityPower": str(min_city_power) if min_city_power != float('inf') else "0",
                    "areaPower": str(min_area_power) if min_area_power != float('inf') else "0"
                },
                "data": platform_list
            }
            
            try:
                plugin_root = os.path.dirname(os.path.dirname(__file__))
                template_path = os.path.join(plugin_root, "templates", "hero_power.html")
                with open(template_path, "r", encoding="utf-8") as f:
                    html_template = f.read()
                
                url = await self.plugin.html_render(html_template, template_data, options=self._get_render_options())
                yield event.image_result(url)
            except Exception as e:
                logger.error(f"战力渲染图片失败，使用文本回退，错误: {e}", exc_info=True)
                text = "\n".join(info_lines)
                yield event.plain_result(text)
            
        except Exception as e:
            logger.error(f"查询英雄战力失败: {e}")
            yield event.plain_result(
                f"❌ 查询失败: {str(e)}\n\n💡 提示:\n• 请确保英雄名称正确\n• 例如: 查战力 李白"
            )

    async def query_hero_skin(self, hero_name: str, event):
        """查询英雄皮肤"""
        try:
            logger.info(f"开始查询英雄皮肤，英雄名: {hero_name}")
            if not self._hero_list_cache:
                logger.info("正在获取英雄列表...")
                self._hero_list_cache = await api_service.get_hero_list()
                logger.info(f"英雄列表获取成功，共{len(self._hero_list_cache)}个英雄")
            
            hero = None
            for h in self._hero_list_cache:
                if h.get("cname") == hero_name:
                    hero = h
                    logger.info(f"找到英雄: {hero_name}, ID: {h.get('ename')}")
                    break
            
            if not hero:
                yield event.plain_result(
                    f"❌ 未找到英雄【{hero_name}】\n请检查英雄名称是否正确"
                )
                return
            

            skin_names = hero.get("skin_name", "").split("|") if hero.get("skin_name") else []
            logger.info(f"皮肤名称列表: {skin_names}")
            
            if not skin_names or len(skin_names) == 0:
                yield event.plain_result(f"❌ 未找到【{hero_name}】的皮肤数据")
                return
            
            # 构建皮肤信息（文本版本，用于回退）
            info_lines = [
                f"👗 【{hero_name} 皮肤列表】",
                ""
            ]
            
            for i, skin_name in enumerate(skin_names, 1):
                if skin_name:  # 跳过空名称
                    info_lines.append(f"{i}. {skin_name}")
            
            info_lines.extend([
                "",
                f"共 {len(skin_names)} 款皮肤"
            ])
            

            hero_ename = hero.get("ename", "")
            skin_data = []
            

            index = 1
            async with aiohttp.ClientSession() as session:
                while True:
                    try:
                        skin_url = f"https://game.gtimg.cn/images/yxzj/img201606/skin/hero-info/{hero_ename}/{hero_ename}-bigskin-{index}.jpg"
                        async with session.head(skin_url, timeout=5) as response:
                            if response.status != 200:
                                break
                            
                            # 获取对应的皮肤名称
                            skin_name = skin_names[index - 1] if index - 1 < len(skin_names) else ""
                            skin_data.append({
                                "name": skin_name,
                                "url": skin_url
                            })
                            index += 1
                    except Exception as e:
                        logger.error(f"检查皮肤URL失败: {e}")
                        break
            
            if not skin_data:
                yield event.plain_result(f"❌ 未找到【{hero_name}】的皮肤图片")
                return
            
            template_data = {
                "heroName": hero_name,
                "skinData": skin_data
            }
            
            try:
                # 读取HTML模板（从插件根目录）
                plugin_root = os.path.dirname(os.path.dirname(__file__))
                template_path = os.path.join(plugin_root, "templates", "hero_skin.html")
                with open(template_path, "r", encoding="utf-8") as f:
                    html_template = f.read()
                
                # 使用 html_render 渲染HTML模板为图片
                url = await self.plugin.html_render(html_template, template_data, options=self._get_render_options())
                yield event.image_result(url)
            except Exception as e:
                logger.error(f"皮肤渲染图片失败，使用文本回退，错误: {e}", exc_info=True)
                text = "\n".join(info_lines)
                yield event.plain_result(text)
            
        except Exception as e:
            logger.error(f"查询英雄皮肤失败: {e}")
            yield event.plain_result(
                f"❌ 查询失败: {str(e)}\n\n💡 提示:\n• 请确保英雄名称正确\n• 例如: 查皮肤 李白"
            )

    def _get_skin_type(self, skin_type: int) -> str:
        """获取皮肤类型名称"""
        skin_types = {
            0: "普通",
            1: "勇者",
            2: "史诗",
            3: "传说",
            4: "限定",
            5: "荣耀典藏"
        }
        return skin_types.get(skin_type, "未知")
