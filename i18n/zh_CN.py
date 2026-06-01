"""中文 UI 字符串常量"""

STRINGS = {
    # === 窗口 ===
    "app_title": "CAD 图像转代码工具",
    "app_version": "v1.0.0",

    # === 工具栏 ===
    "btn_open_image": "打开图像",
    "btn_detect": "检测特征",
    "btn_generate": "生成代码",
    "btn_settings": "设置",
    "btn_export": "导出",
    "btn_clear": "清除",

    # === 导出模式 ===
    "mode_com": "COM 自动控制",
    "mode_clipboard": "复制到剪贴板",
    "mode_file": "保存为 SCR 文件",
    "lbl_export_mode": "导出模式:",

    # === 状态栏 ===
    "status_ready": "就绪 — 请打开一张图像",
    "status_loading": "正在加载图像...",
    "status_detecting": "正在检测特征...",
    "status_generating": "正在生成代码...",
    "status_exporting": "正在导出...",
    "status_done_detect": "检测完成 — {walls}面墙, {doors}扇门, {windows}扇窗, {trees}棵树, {circles}个圆",
    "status_done_generate": "代码生成完成 — 共 {lines} 行",
    "status_done_export": "导出成功 — {path}",

    # === 错误消息 ===
    "err_no_image": "请先打开一张图像",
    "err_no_geometry": "请先检测特征",
    "err_no_code": "请先生成代码",
    "err_load_image": "无法加载图像: {error}",
    "err_save_file": "无法保存文件: {error}",
    "err_com_not_found": "未检测到 AutoCAD。请确认已安装 AutoCAD 2020 或更高版本，并至少运行过一次。",
    "err_com_connection": "无法连接到 AutoCAD: {error}",
    "err_detect_failed": "特征检测失败: {error}",
    "err_generate_failed": "代码生成失败: {error}",
    "err_unsupported_format": "不支持的图片格式。支持的格式: {formats}",

    # === 对话框 ===
    "dlg_open_image": "打开图像",
    "dlg_save_scr": "保存 SCR 脚本",
    "dlg_settings_title": "设置",
    "dlg_image_filter": "图像文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.tif)",
    "dlg_scr_filter": "SCR 脚本 (*.scr)",

    # === 设置面板 ===
    "settings_tab_detection": "检测参数",
    "settings_tab_export": "导出设置",
    "settings_tab_autocad": "AutoCAD 版本",

    "settings_canny_label": "Canny 边缘检测",
    "settings_canny_low": "低阈值",
    "settings_canny_high": "高阈值",

    "settings_hough_line_label": "霍夫直线检测",
    "settings_hough_threshold": "累加器阈值",
    "settings_hough_min_length": "最小线段长度",
    "settings_hough_max_gap": "最大间隙",

    "settings_wall_label": "墙体检测",
    "settings_wall_thickness_min": "最小墙厚 (mm)",
    "settings_wall_thickness_max": "最大墙厚 (mm)",

    "settings_scale_label": "比例尺",
    "settings_default_scale": "默认比例 (mm/像素)",
    "settings_scale_hint": "当图片中未检测到比例尺时使用此默认值",

    "settings_autocad_version": "AutoCAD 版本",

    # === 提示消息 ===
    "msg_clipboard_copied": "已生成 SCR 文件并复制路径到剪贴板。\n\n请在 AutoCAD 中:\n1. 输入 SCRIPT 命令\n2. 按 Ctrl+V 粘贴路径\n3. 按回车执行",
    "msg_file_saved": "SCR 文件已保存到: {path}",
    "msg_com_success": "已连接到 AutoCAD 并开始执行脚本。",

    # === 面板标签 ===
    "panel_image": "图像预览",
    "panel_code": "生成代码",

    # === 菜单 ===
    "menu_file": "文件(&F)",
    "menu_help": "帮助(&H)",
    "action_about": "关于",
    "about_text": "CAD 图像转代码工具 v1.0.0\n\n将建筑平面图 / 园林景观设计图转换为 AutoCAD 脚本代码。\n\n支持:\n• 墙体、门、窗检测\n• 树木、道路、水体检测\n• COM 自动控制 / 剪贴板 / SCR 文件导出",
}
