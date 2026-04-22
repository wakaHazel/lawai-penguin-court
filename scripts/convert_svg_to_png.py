import os
import glob
import subprocess

def install_and_run():
    # 使用 Python 原生绘制 PNG 也可以，不过 cairosvg 往往需要系统依赖（如 cairo）。
    # 这里我们用最轻量的工具：`svglib` 或者直接让用户手动将生成的 SVG 转成 PNG 并替换，
    # 或者，我们编写一段能把表格直接写回 Word 的提示，
    # 鉴于 python-docx 插入图片不支持 SVG，我们将提供一个手动替换的说明。
    pass
