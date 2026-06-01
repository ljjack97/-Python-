# CAD 图像转代码工具

将建筑平面图 / 园林景观设计图自动识别并转换为 AutoCAD 脚本代码。

## 功能

- **图像识别**：自动检测墙体、门、窗、直线、圆、圆弧、树木、道路、水体
- **代码生成**：将识别结果转换为 AutoCAD `.scr` 脚本
- **三种导出模式**：
  - **COM 自动控制** — 直接连接 AutoCAD 自动执行绘图
  - **剪贴板复制** — 一键复制脚本路径，粘贴到 AutoCAD 执行
  - **文件保存** — 保存为 .scr 文件，手动加载

## 系统要求

- Windows 10/11
- Python 3.10+
- AutoCAD 2020+（仅 COM 模式需要）

## 安装

```bash
# 1. 克隆或下载项目
cd "E:\Python后端项目"

# 2. 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 使用流程

1. **打开图像** — 点击工具栏 [打开图像] 或按 `Ctrl+O`，选择 PNG/JPG/BMP 格式的图纸
2. **检测特征** — 点击 [检测特征] 或按 `Ctrl+D`，自动识别图中的几何元素
3. **生成代码** — 点击 [生成代码] 或按 `Ctrl+G`，生成 AutoCAD 脚本
4. **导出** — 选择导出模式后点击 [导出] 或按 `Ctrl+E`

## 支持的图纸类型

- ✅ 建筑平面图（墙体、门、窗）
- ✅ 园林景观设计图（树木、道路、水体）
- ⚠️ 复杂标注密集的工程图（准确率可能下降）
- ⚠️ 手绘草图（识别效果较差）

## 识别效果提示

- 图像越清晰、线条越干净，识别准确率越高
- 建议使用扫描或导出的矢量转换图，而非照片
- 比例尺自动检测失败时可手动设置（设置 → 导出设置 → 默认比例）

## 目录结构

```
├── main.py              # 程序入口
├── requirements.txt     # Python 依赖
├── config/              # 配置
│   ├── app_config.py    # 应用配置（检测参数、AutoCAD 版本等）
│   └── cad_templates.py # AutoCAD 模板
├── core/                # 图像识别核心
│   ├── geometry.py      # 几何数据类
│   ├── image_loader.py  # 图片加载
│   ├── preprocessor.py  # 图像预处理
│   ├── line_detector.py # 直线检测
│   ├── circle_detector.py    # 圆/圆弧检测
│   ├── contour_detector.py   # 轮廓检测
│   ├── scale_estimator.py    # 比例尺识别
│   ├── wall_detector.py      # 墙体检测
│   ├── door_window_detector.py # 门窗检测
│   └── landscape_detector.py   # 景观检测
├── cad/                 # CAD 代码生成
│   ├── cad_commands.py  # 命令模板
│   ├── layer_manager.py # 图层管理
│   ├── code_generator.py # 代码生成器
│   └── scr_builder.py   # SCR 组装
├── automation/          # 导出
│   ├── base_exporter.py
│   ├── com_exporter.py
│   ├── clipboard_exporter.py
│   └── file_exporter.py
├── ui/                  # 用户界面
│   ├── main_window.py
│   ├── image_panel.py
│   ├── code_panel.py
│   ├── toolbar.py
│   ├── settings_dialog.py
│   ├── workers.py
│   └── theme.py
└── i18n/
    └── zh_CN.py         # 中文字符串
```

## 技术栈

- **Python 3.13** + **PyQt5** — 桌面 GUI
- **OpenCV** — 图像识别（边缘检测、霍夫变换、轮廓分析）
- **pywin32** — AutoCAD COM 自动化
