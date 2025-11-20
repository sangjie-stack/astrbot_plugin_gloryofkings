# 王者荣耀数据查询插件

<div align="center">

一个为 [AstrBot](https://github.com/Soulter/AstrBot) 提供王者荣耀相关功能的插件



</div>

## 🌟 主要功能

### 📋 账号管理
- ✅ 绑定/切换/删除营地ID
- ✅ 多账号管理支持
- ✅ 账号信息展示
- ✅ 角色选择功能（支持多角色切换）

### 📊 数据查询
- ✅ 主页查询（段位/场次/MVP等）
- ✅ 战绩查询（最近30场）
- ✅ 战绩详情（评分/经济/装备等）
- ✅ 英雄战力查询
- ✅ 英雄皮肤查询
- ✅ 赛季数据查询

### 🔔 战绩推送
- ✅ 自动检测新战绩
- ✅ 推送到指定群聊
- ✅ 可配置检测间隔

## 📦 安装方法

### 1. 安装插件

将插件文件夹复制到 AstrBot 的 `data/plugins/` 目录:

```bash
# 假设 AstrBot 安装在 /path/to/AstrBot
cp -r astrbot_plugin_gloryofkings /path/to/AstrBot/data/plugins/
```

### 2. 安装依赖

```bash
cd /path/to/AstrBot/data/plugins/astrbot_plugin_gloryofkings
pip install -r requirements.txt
```

### 3. 配置插件（可选）

复制配置示例文件并根据需要修改：

```bash
cp config.example.json config.json
```

或通过 WebUI 的插件配置界面进行配置。

### 4. 重启 AstrBot

重启 AstrBot 或在 WebUI 中重载插件即可使用。

## 🎯 使用指南

### 账号管理

- `/绑定营地 [ID]` - 绑定营地ID，可绑定多个
- `/切换营地 [序号]` - 切换使用的营地ID
- `/删除营地 [序号]` - 删除绑定的营地ID
- `/我的ID` - 查看已绑定的营地ID列表

**如何获取营地ID？**
1. 打开王者营地APP
2. 点击【我的】
3. 点击【游戏资料】
4. 复制营地ID

### 角色选择

- `/王者角色列表` - 查看所有游戏角色
- `/选择角色 [序号]` - 选择指定角色查看数据
- `/清除角色选择` - 清除角色选择，恢复默认

### 数据查询

- `/王者主页` - 查看游戏信息概览
- `/查询战绩` - 查看最近30场战绩
- `/查询战绩 [序号]` - 查看指定场次详细数据
- `/查战力 [英雄名]` - 查询指定英雄的战力排名
- `/查皮肤 [英雄名]` - 查询指定英雄的皮肤
- `/赛季数据` - 查看赛季统计数据

### 战绩推送

- `/开启战绩推送` - 在当前群开启战绩推送
- `/关闭战绩推送` - 在当前群关闭战绩推送
- `/战绩推送状态` - 查看当前群推送状态

### 系统设置

- `/王者帮助` - 显示功能帮助

## 💡 使用示例

### 1. 绑定账号
```
/绑定营地 123456789
```

### 2. 查看主页
```
/王者主页
```

### 3. 查询战绩
```
/查询战绩
/查询战绩 1
```

### 4. 选择角色
```
/王者角色列表
/选择角色 2
```

### 5. 查询英雄数据
```
/查战力 李白
/查皮肤 露娜
```

### 6. 战绩推送
```
/开启战绩推送
/战绩推送状态
```

## 📁 文件结构

```
astrbot_plugin_gloryofkings/
├── main.py                # 主插件文件
├── __init__.py            # 包初始化文件
├── core/                  # 核心功能模块
│   ├── __init__.py        # 模块初始化
│   ├── account_manager.py # 账号管理模块
│   ├── api_service.py     # API调用服务
│   ├── battle_push.py     # 战绩推送模块
│   ├── game_stats.py      # 战绩查询模块
│   └── hero_query.py      # 英雄查询模块
├── templates/             # HTML模板文件
│   ├── account_manage.html
│   ├── battle_list.html
│   ├── help.html
│   ├── hero_power.html
│   ├── hero_skin.html
│   ├── homepage.html
│   └── homepage_full.html
├── assets/                # 静态资源文件
│   ├── bgImgV2.png
│   ├── cube.png
│   ├── flag1.png
│   ├── roleJob.png
│   └── ...
├── resources/             # 其他资源
│   ├── css/               # 样式文件
│   └── font/              # 字体文件
├── docs/                  # 文档目录
├── _conf_schema.json      # 插件配置定义
├── metadata.yaml          # 插件元数据
├── requirements.txt       # 依赖列表
└── README.md             # 本文件
```

## ⚙️ 配置说明

### 图片渲染质量配置

插件支持自定义图片渲染质量，可以根据网络环境和需求调整：

#### render_scale（渲染分辨率倍数）
- **默认值：** 2（高清）
- **可选值：** 1-3
  - 1 = 标准清晰度（适合移动网络）
  - 2 = 高清（推荐，日常使用）
  - 3 = 超清（适合高速网络）

#### render_quality（图片压缩质量）
- **默认值：** 100（最高质量）
- **可选值：** 1-100
  - 95-100 = 极高质量（推荐）
  - 80-94 = 高质量平衡
  - 60-79 = 标准质量
  - <60 = 低质量（不推荐）

**配置方法：**
1. 通过 WebUI 的插件配置界面修改
2. 或直接编辑配置文件

**推荐配置：**
- 日常使用：`render_scale=2, render_quality=90`
- 追求质量：`render_scale=2, render_quality=100`
- 节省流量：`render_scale=1, render_quality=75`

详细说明请查看：[图片渲染质量配置说明](docs/图片渲染质量配置说明.md)

### 其他配置项

- **check_interval**: 战绩检测间隔（秒），默认 300
- **push_delay**: 战绩推送延迟（秒），默认 60
- **debug_mode**: 调试模式开关，默认 false

## 🔧 技术实现

### 架构设计
```
main.py (插件主类)
    ├── core/
    │   ├── AccountManager (账号管理)
    │   ├── GameStatsQuery (战绩查询)
    │   ├── HeroQuery (英雄查询)
    │   ├── BattlePushManager (战绩推送)
    │   └── ApiService (API调用服务)
    ├── templates/ (HTML模板)
    ├── assets/ (静态资源)
    └── resources/ (CSS/字体)
```

### 数据存储
- 使用 JSON 文件存储用户数据
- 路径: `data/plugins/astrbot_plugin_gloryofkings/user_data.json`

### API来源
- 王者营地官方API
- 第三方战力查询API
- 官方英雄/皮肤数据

## ⚠️ 注意事项

1. **首次使用**：需要先绑定营地ID才能查询数据
2. **API限制**：部分API可能有访问频率限制
3. **数据准确性**：数据来源于王者营地，可能存在延迟
4. **网络要求**：需要稳定的网络连接

## 🆚 与原版对比

### 保留功能
- ✅ 账号管理（绑定/切换/删除）
- ✅ 战绩查询
- ✅ 英雄战力查询
- ✅ 英雄皮肤查询
- ✅ 游戏主页展示
- ✅ 图片渲染展示

### 新增功能
- ✅ 角色选择功能
- ✅ 战绩自动推送
- ✅ Web配置界面
- ✅ 调试模式开关

### 优化改进
- ✅ 使用 Python 异步编程
- ✅ 更简洁的代码结构
- ✅ 更好的错误处理
- ✅ 适配 AstrBot 框架
- ✅ 支持多角色切换
- ✅ 配置文件管理

## 🐛 常见问题

### Q: 查询失败怎么办？
A: 检查以下几点：
1. 营地ID是否正确
2. 网络连接是否正常
3. API是否可访问

### Q: 如何获取营地ID？
A: 打开王者营地APP → 我的 → 游戏资料 → 复制ID

### Q: 支持哪些平台？
A: 支持所有 AstrBot 支持的平台（QQ、Telegram等）

## 📝 更新日志

### v1.1.0 (2025-11-19)
- ✅ 新增角色选择功能
- ✅ 新增战绩自动推送
- ✅ 新增Web配置界面
- ✅ 优化调试日志输出
- ✅ 完善错误处理

### v1.0.0 (2025-11-18)
- ✅ 初始版本
- ✅ 从 Yunzai-Bot 插件转换
- ✅ 实现核心功能
- ✅ 适配 AstrBot 框架

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

- 原作者: [@Tloml-Starry](https://gitee.com/Tloml-Starry)
- 作者: 球球

## 📄 开源协议

本项目基于原项目协议开源

## 🙏 致谢

- 感谢 [Yunzai-Bot](https://gitee.com/Le-niao/Yunzai-Bot) 项目
- 感谢 [GloryOfKings-Plugin](https://gitee.com/Tloml-Starry/GloryOfKings-Plugin) 原作者
- 感谢 [AstrBot](https://github.com/Soulter/AstrBot) 框架

## ⭐ 支持项目

如果你觉得这个项目对你有帮助，欢迎给一个 Star 支持一下~
