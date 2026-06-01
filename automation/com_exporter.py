"""COM 自动化导出模式 — 通过 COM 接口直接控制 AutoCAD"""

import os
import time
import tempfile
from pathlib import Path
from typing import Optional

from automation.base_exporter import BaseExporter
from config.app_config import AppConfig


class ComExporter(BaseExporter):
    """通过 COM 接口自动控制 AutoCAD

    工作流程:
    1. 尝试连接已运行的 AutoCAD 实例
    2. 如果没有运行，尝试启动 AutoCAD
    3. 将 SCR 脚本写入临时文件
    4. 通过 SendCommand 执行 SCRIPT 命令加载脚本
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self._acad = None
        self._doc = None

    def name(self) -> str:
        return "COM 自动控制"

    def description(self) -> str:
        return "自动连接 AutoCAD 并执行脚本，无需手动操作（需要安装 AutoCAD）"

    def is_autocad_available(self) -> bool:
        """检查 AutoCAD 是否可用"""
        try:
            import win32com.client
            # 尝试获取或创建 AutoCAD 实例
            acad = win32com.client.Dispatch(self.config.get_progid())
            return acad is not None
        except Exception:
            return False

    def export(self, scr_text: str) -> bool:
        """通过 COM 自动执行脚本

        Args:
            scr_text: SCR 脚本文本

        Returns:
            是否成功
        """
        try:
            import pythoncom
            import win32com.client

            # 初始化 COM
            pythoncom.CoInitialize()

            try:
                # 尝试连接到 AutoCAD
                self._acad = self._connect_autocad(win32com.client)

                if self._acad is None:
                    return False

                # 确保 AutoCAD 可见
                try:
                    self._acad.Visible = True
                except Exception:
                    pass

                # 获取或创建文档
                self._doc = self._get_document()

                if self._doc is None:
                    return False

                # 写入临时 SCR 文件
                temp_path = self._write_temp_scr(scr_text)

                # 执行 SCRIPT 命令
                script_path = temp_path.replace('\\', '\\\\')
                # AutoCAD 的 SCRIPT 命令接受文件路径
                command = f'SCRIPT\n"{script_path}"\n'
                self._doc.SendCommand(command)

                # 等待脚本执行
                time.sleep(0.5)

                return True

            finally:
                pythoncom.CoUninitialize()

        except ImportError:
            raise ImportError("pywin32 未安装，请运行: pip install pywin32")
        except Exception as e:
            raise ConnectionError(f"COM 连接失败: {e}")

    def _connect_autocad(self, win32com_client):
        """连接到 AutoCAD

        策略:
        1. 先尝试 GetObject（连接已运行的实例）
        2. 失败则 Dispatch（启动新实例）
        """
        # 尝试 ProgID 列表
        prog_ids = [
            self.config.get_progid(),
            "AutoCAD.Application.24",
            "AutoCAD.Application.24.1",
            "AutoCAD.Application.24.2",
            "AutoCAD.Application.24.3",
            "AutoCAD.Application.24.4",
            "AutoCAD.Application.25",
            "AutoCAD.Application",
        ]

        # 先尝试连接已运行的实例
        for prog_id in prog_ids:
            try:
                acad = win32com_client.GetObject(None, prog_id)
                if acad is not None:
                    return acad
            except Exception:
                continue

        # 再尝试启动新实例
        for prog_id in prog_ids:
            try:
                acad = win32com_client.Dispatch(prog_id)
                if acad is not None:
                    return acad
            except Exception:
                continue

        return None

    def _get_document(self):
        """获取或创建 AutoCAD 文档"""
        if self._acad is None:
            return None

        try:
            # 尝试获取当前活动文档
            doc = self._acad.ActiveDocument
            if doc is not None:
                return doc
        except Exception:
            pass

        try:
            # 尝试获取 Documents 集合中的第一个
            docs = self._acad.Documents
            if docs.Count > 0:
                return docs.Item(0)
            # 创建新文档
            return docs.Add()
        except Exception:
            return None

    def _write_temp_scr(self, scr_text: str) -> str:
        """写入临时 SCR 文件"""
        fd, temp_path = tempfile.mkstemp(suffix=".scr", prefix="cad_auto_")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(scr_text)
        return temp_path

    def disconnect(self):
        """断开与 AutoCAD 的连接"""
        self._doc = None
        self._acad = None
