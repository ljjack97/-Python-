"""AutoCAD 图块模板和常用参数"""

# === 门块定义（用于 INSERT 命令） ===
# 简单平开门：一个矩形 + 一个圆弧表示门扇
DOOR_BLOCK_DEF = """
; 门块定义 — 平开门
; 参数：宽度 W，开启方向（左/右）
"""

# === 窗块定义 ===
WINDOW_BLOCK_DEF = """
; 窗块定义 — 双线窗
; 参数：长度 L，厚度 T
"""

# === 树符号定义 ===
TREE_BLOCK_DEF = """
; 树符号 — 圆 + 填充
; 参数：半径 R
"""

# === AutoCAD 颜色索引 ===
ACAD_COLORS = {
    "red": 1,
    "yellow": 2,
    "green": 3,
    "cyan": 4,
    "blue": 5,
    "magenta": 6,
    "white": 7,
    "dark_gray": 8,
    "light_gray": 9,
}

# === 常见线型 ===
LINETYPES = {
    "continuous": "Continuous",
    "dashed": "DASHED",
    "center": "CENTER",
    "hidden": "HIDDEN",
}

# === 常见填充图案 ===
HATCH_PATTERNS = {
    "solid": "SOLID",
    "brick": "AR-BRSTD",
    "concrete": "AR-CONC",
    "earth": "EARTH",
    "grass": "GRASS",
    "water": "AR-HBONE",       # 水体用
    "sand": "AR-SAND",
    "net": "NET",
    "dots": "DOTS",
}

# === 景观设计常用符号尺寸（mm） ===
LANDSCAPE_SIZES = {
    "tree_small": 1000,        # 小乔木半径
    "tree_medium": 2500,       # 中型乔木半径
    "tree_large": 5000,        # 大乔木半径
    "shrub": 500,              # 灌木半径
    "path_residential": 1200,  # 住宅区步道宽度
    "path_main": 2500,         # 主要步道宽度
    "path_vehicle": 4000,      # 车行道宽度
}
