import os
import glob
import subprocess
import time

def render_svg_to_png():
    svg_dir = r"E:\lawai\output\doc\diagrams\tables"
    svg_files = glob.glob(os.path.join(svg_dir, "*.svg"))
    
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    if not os.path.exists(edge_path):
        print("未找到 Edge 浏览器")
        return
        
    for svg_file in svg_files:
        png_file = svg_file.replace(".svg", ".png")
        html_file = svg_file.replace(".svg", ".html")
        
        # 1. 包装为 HTML，去掉 margin 和 padding，设置白色背景
        with open(svg_file, "r", encoding="utf-8") as f:
            svg_content = f.read()
            
        # 从 SVG 中提取宽高（粗略）
        # <svg width="900" height="250"
        import re
        width_match = re.search(r'width="(\d+)"', svg_content)
        height_match = re.search(r'height="(\d+)"', svg_content)
        w = int(width_match.group(1)) if width_match else 900
        h = int(height_match.group(1)) if height_match else 500
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ margin: 0; padding: 0; background: white; overflow: hidden; }}
                svg {{ display: block; }}
            </style>
        </head>
        <body>
            {svg_content}
        </body>
        </html>
        """
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        # 2. 调用 Edge headless 截图
        # 注意：--window-size 需要比内容大一点，或者刚好
        cmd = [
            edge_path,
            "--headless",
            "--disable-gpu",
            f"--window-size={w},{h}",
            f"--screenshot={png_file}",
            f"file:///{html_file.replace(chr(92), '/')}"
        ]
        
        print(f"正在渲染: {os.path.basename(svg_file)} -> {os.path.basename(png_file)}")
        subprocess.run(cmd, check=True)
        
        # 稍微等一下防止 IO 冲突
        time.sleep(0.5)
        
        # 3. 清理临时 HTML
        if os.path.exists(html_file):
            os.remove(html_file)
            
    print("✅ 全部渲染完成！")

if __name__ == "__main__":
    render_svg_to_png()
