"""使用帮助对话框 — 详细的使用说明书"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout
)

HELP_TEXT = """
<h1>CAD 图像转代码工具 — 使用说明书</h1>

<hr>

<h2>一、快速开始</h2>

<ol>
<li><b>打开图像</b> — 点击工具栏 [打开图像] 或按 Ctrl+O，选择你的 CAD 图纸图片（支持 PNG/JPG/BMP/TIFF）</li>
<li><b>检测特征</b> — 点击 [检测特征] 或按 Ctrl+D，程序会自动识别图中的墙体、门、窗、圆、弧等几何元素</li>
<li><b>生成代码</b> — 点击 [生成代码] 或按 Ctrl+G，将识别结果转换为 AutoCAD 脚本</li>
<li><b>导出</b> — 选择导出模式后点击 [导出] 或按 Ctrl+E</li>
</ol>

<hr>

<h2>二、检测功能说明</h2>

<h3>自动检测的元素：</h3>
<ul>
<li><b style='color:red;'>墙体</b> — 识别平行双线结构（红色标记）</li>
<li><b style='color:blue;'>窗户</b> — 识别墙体间的细缝（蓝色标记）</li>
<li><b style='color:red;'>门</b> — 识别墙体间隙处的弧形（红色点标记）</li>
<li><b style='color:green;'>圆 / 树</b> — 霍夫圆检测（绿色标记）</li>
<li><b style='color:cyan;'>圆弧</b> — 椭圆拟合检测（青色标记）</li>
<li><b style='color:yellow;'>道路/曲线</b> — 曲率分析（黄色标记）</li>
<li><b style='color:cyan;'>水体</b> — 大面积闭合轮廓（青色填充）</li>
</ul>

<h3>提高识别准确率的技巧：</h3>
<ul>
<li>使用清晰、高对比度的扫描图或导出图</li>
<li>避免使用手机拍摄的模糊照片</li>
<li>可以在 <b>[设置]</b> 中调整检测参数（Canny阈值、霍夫阈值、墙体厚度范围等）</li>
<li>使用 <b>[框选区域]</b> 按钮框选需要检测的部分，排除无关区域</li>
</ul>

<hr>

<h2>三、图片操作</h2>

<ul>
<li><b>滚轮缩放</b> — 鼠标滚轮放大/缩小图片（10%~400%）</li>
<li><b>拖拽平移</b> — 按住鼠标左键拖拽移动视图</li>
<li><b>双击切换</b> — 在 原图 / 检测叠加层 之间切换</li>
<li><b>右键菜单</b> — 更多操作（缩放、框选、切换视图）</li>
<li><b>框选区域</b> — 右键选择"框选检测区域"，在图片上拖拽选择区域后，只检测该区域内的特征</li>
</ul>

<hr>

<h2>四、导出模式说明</h2>

<h3>模式 1：COM 自动控制</h3>
<ul>
<li>需要安装 <b>AutoCAD 2020 或更高版本</b></li>
<li>程序会自动连接 AutoCAD 并执行绘图命令</li>
<li>如果 AutoCAD 未运行，程序会尝试启动它</li>
<li>如果连接失败，程序会提示并建议使用其他模式</li>
</ul>

<h3>模式 2：复制到剪贴板</h3>
<ul>
<li>生成 SCR 脚本文件并复制文件路径到剪贴板</li>
<li>在 AutoCAD 中：</li>
<ol>
<li>输入 <code>SCRIPT</code> 命令并回车</li>
<li>在文件对话框中按 <b>Ctrl+V</b> 粘贴路径</li>
<li>按回车执行</li>
</ol>
</ul>

<h3>模式 3：保存为 SCR 文件</h3>
<ul>
<li>将脚本保存为 <code>.scr</code> 文件到指定位置</li>
<li>在 AutoCAD 中：</li>
<ol>
<li>输入 <code>SCRIPT</code> 命令并回车</li>
<li>选择保存的 <code>.scr</code> 文件</li>
<li>按回车执行</li>
</ol>
</ul>

<hr>

<h2>五、SCR 脚本格式说明</h2>

<p>生成的 <code>.scr</code> 文件是 AutoCAD 脚本文件，包含一系列绘图命令：</p>

<h3>常用命令：</h3>
<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;'>
<tr><th>命令</th><th>说明</th><th>示例</th></tr>
<tr><td>LINE</td><td>绘制直线</td><td><code>LINE 0,0 100,100</code></td></tr>
<tr><td>CIRCLE</td><td>绘制圆</td><td><code>CIRCLE 50,50 30</code></td></tr>
<tr><td>ARC</td><td>三点圆弧</td><td><code>ARC 0,0 50,50 100,0</code></td></tr>
<tr><td>PLINE</td><td>多段线</td><td><code>PLINE 0,0 100,0 100,100 C</code></td></tr>
<tr><td>RECTANG</td><td>矩形</td><td><code>RECTANG 0,0 200,100</code></td></tr>
<tr><td>-HATCH</td><td>填充图案</td><td><code>-HATCH P SOLID 1 0 W ...</code></td></tr>
<tr><td>-LAYER</td><td>图层管理</td><td><code>-LAYER N Walls C 7 Walls</code></td></tr>
</table>

<h3>重要提示：</h3>
<ul>
<li><b>不要直接粘贴脚本内容到 AutoCAD 命令行！</b></li>
<li>请使用 <code>SCRIPT</code> 命令加载 <code>.scr</code> 文件</li>
<li>SCR 文件中每个换行 = 按一次回车键</li>
<li>脚本自动包含图层创建和设置命令</li>
</ul>

<h3>生成的图层：</h3>
<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;'>
<tr><th>图层名</th><th>颜色</th><th>内容</th></tr>
<tr><td>Walls</td><td>白色</td><td>墙体</td></tr>
<tr><td>Doors</td><td>红色</td><td>门</td></tr>
<tr><td>Windows</td><td>蓝色</td><td>窗户</td></tr>
<tr><td>Lines</td><td>白色</td><td>检测直线</td></tr>
<tr><td>Circles</td><td>绿色</td><td>检测圆</td></tr>
<tr><td>Arcs</td><td>青色</td><td>检测圆弧</td></tr>
<tr><td>Trees</td><td>绿色</td><td>树木符号</td></tr>
<tr><td>Paths</td><td>黄色</td><td>道路/步道</td></tr>
<tr><td>Water</td><td>青色</td><td>水体填充</td></tr>
</table>

<hr>

<h2>六、设置说明</h2>

<ul>
<li><b>检测参数</b> — 调整 Canny 边缘检测、霍夫直线/圆检测的阈值，以及墙体厚度范围</li>
<li><b>导出设置</b> — 设置默认比例尺（mm/像素），当自动检测不到比例尺时使用</li>
<li><b>AutoCAD 版本</b> — 选择你的 AutoCAD 版本（影响 COM 连接）</li>
</ul>

<hr>

<h2>七、常见问题</h2>

<p><b>Q: 检测不到墙体？</b><br>
A: 在 [设置] 中调整墙体厚度范围、降低 Canny 或霍夫阈值。也可以用框选功能排除干扰区域。</p>

<p><b>Q: 代码无法在 AutoCAD 运行？</b><br>
A: 请使用 <code>SCRIPT</code> 命令加载 .scr 文件，不要直接粘贴。确保文件以 UTF-8 编码保存。</p>

<p><b>Q: COM 模式连接失败？</b><br>
A: 确认 AutoCAD 已安装并至少运行过一次。可以在设置中尝试不同的版本号。</p>

<p><b>Q: 比例尺不对？</b><br>
A: 在 [设置] → [导出设置] 中手动调整默认比例（mm/像素）。</p>

<hr>

<p style='color:#757575; text-align:center;'>CAD 图像转代码工具 v1.0.0</p>
"""


class HelpDialog(QDialog):
    """使用帮助对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("使用说明 — CAD 图像转代码工具")
        self.resize(750, 600)
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        self._browser = QTextBrowser()
        self._browser.setHtml(HELP_TEXT)
        self._browser.setOpenExternalLinks(True)
        self._browser.setStyleSheet("""
            QTextBrowser {
                background-color: #FAFAFA;
                border: 1px solid #BBDEFB;
                border-radius: 4px;
                font-size: 13px;
                padding: 12px;
            }
        """)
        layout.addWidget(self._browser)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
