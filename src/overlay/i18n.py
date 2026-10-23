"""Translations for desktop controls only; business and overlay data stay English."""

SUPPORTED_LANGUAGES = ("en", "zh_CN")
_language = "en"

TRANSLATIONS = {
    "zh_CN": {
        "File": "文件",
        "Settings": "设置",
        "Links": "链接",
        "Html files": "HTML 文件",
        "Config/logs": "配置与日志",
        "Exit": "退出",
        "Log match data": "记录对局数据",
        "App on Github": "项目 GitHub 页面",
        "My discord": "作者的 Discord",
        "Donate": "捐赠",
        "Games": "历史对局",
        "Build orders": "建造顺序",
        "Randomize": "随机选择",
        "Override": "手动覆盖",
        "Profile": "玩家资料",
        "No player identified": "尚未选择玩家",
        "Steam ID / Profile ID / Name": "Steam ID / 玩家 ID / 名称",
        "Search": "搜索",
        "Search for your account with one of these (Steam ID / Profile ID / Name). Searching by name might not find the correct player.":
            "输入 Steam ID、玩家 ID 或名称来搜索账号。按名称搜索可能找到其他同名玩家。",
        "Overlay": "悬浮窗",
        "Hotkey for showing and hiding overlay:": "显示或隐藏悬浮窗的快捷键：",
        "Hotkey for showing and hiding overlay": "显示或隐藏悬浮窗的快捷键",
        "Hotkey for showing and hiding overlay.": "显示或隐藏悬浮窗的快捷键。",
        "Overlay font size:": "悬浮窗字号：",
        "Change/fix overlay position": "移动或固定悬浮窗",
        "Click to change overlay position. Click again to fix its position.":
            "点击后可移动悬浮窗，再次点击可固定位置。",
        "New update!": "发现新版本！",
        "Click here to download new app version": "点击下载新版本",
        "Steam_id: {steam_id}": "Steam ID：{steam_id}",
        "Profile_id: {profile_id}": "玩家 ID：{profile_id}",
        "AoE4 World profile": "AoE4 World 玩家资料",
        "Player found!": "已找到玩家！",
        "Failed to find such player!": "未找到该玩家！",
        "Retry": "重试",
        "Retry the last failed request": "重试上一次失败的请求",
        "API endpoint:": "数据接口地址：",
        "Add": "添加",
        "Remove": "移除",
        "Test connection": "测试连接",
        "Test the connection to the selected API endpoint": "测试与所选数据接口的连接",
        "Auto-switch endpoint on failure": "连接失败时自动切换备用地址",
        "Automatically switch to a backup API endpoint when requests keep failing":
            "当请求持续失败时自动切换到备用数据接口。",
        "Testing connection...": "正在测试连接…",
        "Connection OK ({latency} ms)": "连接正常（{latency} 毫秒）",
        "Connection failed": "连接失败",
        "Invalid address": "地址无效",
        "Endpoint added": "已添加备用地址",
        "Endpoint removed": "已移除备用地址",
        "Keep at least one endpoint": "至少保留一个地址",
        "API endpoint switched": "已切换数据接口",
        "Failed to use this hotkey": "无法使用此快捷键",
        "Press shortcut": "按下快捷键",
        "Restart the app to apply the language change.": "重启程序后语言设置生效。",
        "Failed to save the language preference.": "无法保存语言设置。",
        "Team 1": "队伍 1",
        "Team 2": "队伍 2",
        "Team {number}": "队伍 {number}",
        "No team": "无队伍",
        "Map": "地图",
        "Started": "开始时间",
        "Mode": "模式",
        "Result": "结果",
        "Rating diff": "评分变化",
        "game link": "对局链接",
        "Randomize civ": "随机文明",
        "Randomize map": "随机地图",
        "Change BO overlay position": "移动建造顺序悬浮窗",
        "Adapt the build order name here": "在此修改建造顺序名称",
        "Add build order": "添加建造顺序",
        "Remove build order": "删除建造顺序",
        "Move build order up": "上移建造顺序",
        "Move build order down": "下移建造顺序",
        "Hotkey for cycling build orders:": "切换建造顺序的快捷键：",
        "Hotkey for cycling build orders.": "切换建造顺序的快捷键。",
        "Hotkey to go to previous step:": "上一步的快捷键：",
        "Hotkey to go to the previous step of the build order.": "切换到建造顺序上一步的快捷键。",
        "Hotkey to go to next step:": "下一步的快捷键：",
        "Hotkey to go to the next step of the build order.": "切换到建造顺序下一步的快捷键。",
        "Overlay images height:": "悬浮窗图片高度：",
        "Click to change BO overlay position. Click again to fix its position.":
            "点击后可移动建造顺序悬浮窗，再次点击可固定位置。",
        'Find & copy build orders from <a href="https://age4builder.com/">age4builder.com</a><br>or <a href="https://aoe4guides.com/">aoe4guides.com</a>.':
            '从 <a href="https://age4builder.com/">age4builder.com</a><br>或 <a href="https://aoe4guides.com/">aoe4guides.com</a> 查找并复制建造顺序。',
        "Reset": "重置",
        "Prevent automatic update": "暂停自动更新",
        "Here you can override what is being shown on the overlay.<br><br><b>Override</b> will apply these values.<br><b>Reset</b> will reset the overlay and this to current live values.<br><b>Prevent automatic update</b> will prevent automatic updating with new games.":
            "在此修改悬浮窗显示的信息。<br><br>点击<b>手动覆盖</b>应用修改。<br>点击<b>重置</b>将本页与悬浮窗恢复为当前对局数据。<br>勾选<b>暂停自动更新</b>后，新对局不会自动替换当前数据。",
        "Country": "国家/地区",
        "Elo": "评分",
        "Rank": "排名",
        "Winrate": "胜率",
        "Wins": "胜场",
        "Losses": "负场",
        "Wintime": "获胜时长",
        "CIV STATS": "文明统计",
        'Cannot reach the API endpoint ({endpoint}).<br>Check your network or proxy, or switch to a backup API endpoint below.':
            '无法连接数据接口（{endpoint}）。<br>请检查网络或代理，或在下方切换 API 备用地址。',
    }
}

CONTEXT_TRANSLATIONS = {"zh_CN": {"stats": {"Games": "对局数"}}}


def normalize_language(language):
    """Older configs and unsupported preferences use the original English UI."""
    return language if language in SUPPORTED_LANGUAGES else "en"


def set_language(language):
    """Select the running UI language once, after loading settings at startup."""
    global _language
    _language = normalize_language(language)


def get_language():
    return _language


def tr(source, context=None, **values):
    """Translate an English source string, optionally filling named placeholders."""
    text = TRANSLATIONS.get(_language, {}).get(source, source)
    if context:
        text = CONTEXT_TRANSLATIONS.get(_language, {}).get(context, {}).get(source, text)
    return text.format(**values) if values else text
