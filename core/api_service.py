"""
王者荣耀API服务
封装所有API调用
"""

import json
import time
import re
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from astrbot.api import logger


class ApiService:
    """王者荣耀API服务类"""
    
    def __init__(self):
        self.base_urls = {
            "main": "https://kohcamp.qq.com",
            "game": "https://ssl.kohsocialapp.qq.com:10001",
            "token": "https://api.t1qq.com/api/tool/wzrr/wztoken"
        }
        self.headers = self._get_default_headers()
        self._token_cache = None
        self._token_time = 0

    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        return {
            "Host": "kohcamp.qq.com",
            "cchannelid": "2002",
            "cclientversioncode": "2037905606",
            "cclientversionname": "8.101.1017",
            "ccurrentgameid": "20001",
            "cgameid": "20001",
            "cgzip": "1",
            "cisarm64": "false",
            "content-type": "application/json",
            "cpuhardware": "unknown",
            "crand": "1734580133908",
            "csupportarm64": "true",
            "csystem": "android",
            "csystemversioncode": "32",
            "csystemversionname": "12",
            "gameareaid": "1",
            "gameid": "20001",
            "gameopenid": "54533036A3D6E4241440CBCD66694578",
            "gameroleid": "2157931910",
            "gameserverid": "1312",
            "gameusersex": "2",
            "kohdimgender": "1",
            "noencrypt": "1",
            "openid": "472AD0DD361C8EC026E52F445041F843",
            "tinkerid": "2037905606_32_0",
            "userid": "2118558336",
            "x-client-proto": "https"
        }

    def _get_common_headers(self, url: str) -> Dict[str, str]:
        """获取通用请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Mobile Safari/537.36",
            "origin": "https://yingdi.qq.com",
            "pragma": "no-cache",
            "q-guid": "4c3328459d6b53c1fbc97281377988cb",
            "q-ua2": "PR=PC&CO=WBK&QV=3&PL=WIN&PB=GE&PPVN=12.2.0.5544&COVC=049400&CHID=10031074&RL=1920*1080&MO=QB&VE=GA&BIT=64&OS=10.0.19045&RT=32",
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "ssoappid": "campAuthor",
            "ssobusinessid": "web"
        }
        
        if self.base_urls["main"] in url:
            headers["Host"] = "kohcamp.qq.com"
        else:
            headers["Host"] = "ssl.kohsocialapp.qq.com"
        
        return headers

    async def _get_token(self) -> str:
        """获取API访问令牌"""
        current_time = time.time()
        
        if self._token_cache and (current_time - self._token_time) < 300:
            logger.debug(f"使用缓存的token: {self._token_cache[:20]}...")
            return self._token_cache
        
        try:
            logger.info(f"正在获取新的token，URL: {self.base_urls['token']}")
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_urls["token"], timeout=10) as response:
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'application/json' in content_type:
                        data = await response.json()
                        logger.debug(f"Token API响应(JSON): {data}")
                        self._token_cache = data.get("token", "")
                    else:
                        text = await response.text()
                        logger.warning(f"Token API返回非JSON格式，Content-Type: {content_type}")
                        logger.debug(f"响应内容前200字符: {text[:200]}")
                        
                        token_match = re.search(r'"token"\s*:\s*"([^"]+)"', text)
                        if token_match:
                            self._token_cache = token_match.group(1)
                            logger.info("从HTML响应中提取到token")
                        else:
                            logger.error("Token API失效，将尝试不使用token")
                            self._token_cache = ""
                    
                    self._token_time = current_time
                    if self._token_cache:
                        logger.info(f"Token获取成功: {self._token_cache[:20]}...")
                    else:
                        logger.warning("Token为空，API请求可能会失败")
                    return self._token_cache
        except Exception as e:
            logger.error(f"获取token失败: {e}", exc_info=True)
            return ""

    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        body: Optional[Dict] = None, 
        additional_headers: Optional[Dict] = None,
        retries: int = 3
    ) -> Dict[str, Any]:
        """通用请求方法"""
        url = f"{self.base_urls['main']}{endpoint}"
        headers = {**self._get_common_headers(url), **(additional_headers or {})}
        
        if self.base_urls["main"] in url:
            headers["Host"] = "kohcamp.qq.com"
        else:
            headers["Host"] = "ssl.kohsocialapp.qq.com"
        
        logger.info(f"=" * 80)
        logger.info(f"完整请求信息 - URL: {url}, Method: {method}")
        logger.info(f"请求体: {body}")
        logger.info(f"完整Headers:")
        for key, value in headers.items():
            if key.lower() in ['token', 'gameopenid', 'openid', 'userid', 'host', 'content-type']:
                logger.info(f"  {key}: {value}")
        logger.info(f"=" * 80)
        
        for i in range(retries):
            try:
                body_str = json.dumps(body) if body else None
                
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        data=body_str,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"HTTP错误 {response.status}: {error_text[:200]}")
                            raise Exception(f"HTTP {response.status}: {error_text[:100]}")
                        

                        text = await response.text()
                        return json.loads(text)
            except Exception as e:
                if i == retries - 1:
                    logger.error(f"API请求失败: {e}, URL: {url}")
                    raise
                await asyncio.sleep(1 * (2 ** i))
        
        return {}

    async def _make_auth_request(self, endpoint: str, body: Dict) -> Dict[str, Any]:
        """创建带认证的请求"""
        token = await self._get_token()
        
        auth_headers = {**self.headers}
        if token:
            auth_headers["token"] = token
            logger.info(f"使用token进行请求: {endpoint}, token前20字符: {token[:20]}...")
        else:
            logger.warning(f"⚠️ 无token，尝试直接请求: {endpoint}")
        
        logger.debug(f"请求体: {body}")
        logger.debug(f"认证headers包含的关键字段: gameopenid={auth_headers.get('gameopenid', 'N/A')[:20]}..., openid={auth_headers.get('openid', 'N/A')[:20]}...")
        
        return await self._request(
            "POST",
            endpoint,
            body,
            auth_headers
        )

    # ========== 公开API方法 ==========
    
    async def get_more_battle_list(self, user_id: str) -> Dict[str, Any]:
        """获取战绩列表"""
        return await self._make_auth_request("/game/morebattlelist", {
            "lastTime": 0,
            "recommendPrivacy": 0,
            "apiVersion": 5,
            "friendUserId": user_id,
            "option": 0
        })

    async def get_battle_detail(
        self, 
        user_id: str, 
        battle_type: int, 
        game_svr: str, 
        relay_svr: str, 
        target_role_id: str, 
        game_seq: str
    ) -> Dict[str, Any]:
        """获取战斗详情"""
        return await self._make_auth_request("/game/battledetail", {
            "recommendPrivacy": 0,
            "battleType": battle_type,
            "gameSvr": game_svr,
            "relaySvr": relay_svr,
            "targetRoleId": target_role_id,
            "gameSeq": game_seq,
            "friendUserId": user_id
        })

    async def get_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户资料"""
        try:

            user_id = str(user_id)
            logger.info(f"正在请求用户资料，ID: {user_id}")
            result = await self._make_auth_request("/game/koh/profile", {
                "targetUserId": user_id,
                "targetRoleId": "0",
                "resVersion": "3",
                "recommendPrivacy": "0",
                "apiVersion": "2"
            })
            logger.info(f"用户资料API响应: {result}")
            return result
        except Exception as e:
            logger.error(f"获取用户资料异常: {e}", exc_info=True)
            return {"code": -1, "msg": str(e)}

    async def get_season_page(self, user_id: str) -> Dict[str, Any]:
        """获取赛季页面数据"""
        return await self._make_auth_request("/game/seasonpage", {
            "recommendPrivacy": 0,
            "seasonId": 0,
            "roleId": user_id
        })

    async def get_hero_fighting_capacity(self, hero_name: str) -> list:
        """获取英雄战力数据（多平台）"""
        regions = ["aqq", "awx", "iqq", "iwx"]
        region_names = {
            "aqq": "Android QQ",
            "awx": "Android 微信",
            "iqq": "iOS QQ",
            "iwx": "iOS 微信"
        }
        
        results = []
        async with aiohttp.ClientSession() as session:
            for region in regions:
                try:
                    url = f"https://www.sapi.run/hero/select.php?hero={hero_name}&type={region}"
                    async with session.get(url, timeout=10) as response:
                        data = await response.json()
                        if data.get("code") == 200:
                            results.append({
                                "platform": region_names.get(region, region),
                                "data": data.get("data", {})
                            })
                except Exception as e:
                    logger.error(f"获取{region}战力失败: {e}")
        
        return results

    async def get_hero_list(self) -> List[Dict[str, Any]]:
        """获取所有英雄列表"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://pvp.qq.com/web201605/js/herolist.json",
                    timeout=10
                ) as response:

                    text = await response.text()
                    return json.loads(text)
        except Exception as e:
            logger.error(f"获取英雄列表失败: {e}")
            return []

    async def get_hero_skin_data(self) -> Dict[str, Any]:
        """获取英雄皮肤数据"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://pvp.qq.com/zlkdatasys/data_zlk_xpflby.json",
                    timeout=10
                ) as response:

                    text = await response.text()
                    return json.loads(text)
        except Exception as e:
            logger.error(f"获取皮肤数据失败: {e}")
            return {}


# 创建全局实例
api_service = ApiService()
