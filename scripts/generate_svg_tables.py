import os
import docx

def create_table_svg(headers, rows, width, row_height, title=""):
    """生成具有现代 UI 风格的 SVG 表格"""
    
    col_widths = []
    # 简单的列宽自适应：根据每列字符数估算比例
    num_cols = len(headers)
    if num_cols == 2:
        col_widths = [0.3, 0.7]
    elif num_cols == 3:
        col_widths = [0.2, 0.3, 0.5]
    elif num_cols == 4:
        col_widths = [0.15, 0.25, 0.25, 0.35]
    elif num_cols == 5:
        col_widths = [0.15, 0.2, 0.2, 0.2, 0.25]
    else:
        col_widths = [1.0/num_cols] * num_cols

    total_height = 40 + row_height + len(rows) * row_height + 40
    if title:
        total_height += 30

    svg_parts = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg width="{width}" height="{total_height}" viewBox="0 0 {width} {total_height}" fill="none" xmlns="http://www.w3.org/2000/svg">',
        '  <defs>',
        '    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">',
        '      <feDropShadow dx="0" dy="4" stdDeviation="12" flood-color="#0f172a" flood-opacity="0.05"/>',
        '    </filter>',
        '    <linearGradient id="header-grad" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#eff6ff" />',
        '      <stop offset="100%" stop-color="#dbeafe" />',
        '    </linearGradient>',
        '  </defs>',
        f'  <rect width="{width}" height="{total_height}" fill="#f8fafc" rx="16"/>',
        f'  <g font-family="system-ui, -apple-system, sans-serif">'
    ]

    current_y = 20

    if title:
        svg_parts.append(f'    <text x="{width/2}" y="{current_y + 15}" font-size="16" font-weight="700" fill="#1e293b" text-anchor="middle">{title}</text>')
        current_y += 40

    # 表格主容器
    table_x = 20
    table_w = width - 40
    
    svg_parts.append(f'    <g transform="translate({table_x}, {current_y})" filter="url(#shadow)">')
    
    # 绘制表头背景
    svg_parts.append(f'      <path d="M0 12 Q0 0 12 0 L{table_w - 12} 0 Q{table_w} 0 {table_w} 12 L{table_w} {row_height} L0 {row_height} Z" fill="url(#header-grad)"/>')
    
    # 绘制表头文字
    x_offset = 0
    for i, h in enumerate(headers):
        cw = table_w * col_widths[i]
        svg_parts.append(f'      <text x="{x_offset + cw/2}" y="{row_height/2 + 6}" font-size="14" font-weight="700" fill="#1e3a8a" text-anchor="middle">{h}</text>')
        x_offset += cw

    # 绘制内容行
    y_offset = row_height
    for r_idx, row in enumerate(rows):
        bg_color = "#ffffff" if r_idx % 2 == 0 else "#f8fafc"
        # 底部圆角
        if r_idx == len(rows) - 1:
            svg_parts.append(f'      <path d="M0 {y_offset} L{table_w} {y_offset} L{table_w} {y_offset + row_height - 12} Q{table_w} {y_offset + row_height} {table_w - 12} {y_offset + row_height} L12 {y_offset + row_height} Q0 {y_offset + row_height} 0 {y_offset + row_height - 12} Z" fill="{bg_color}"/>')
        else:
            svg_parts.append(f'      <rect x="0" y="{y_offset}" width="{table_w}" height="{row_height}" fill="{bg_color}"/>')
        
        # 分割线
        if r_idx < len(rows):
             svg_parts.append(f'      <line x1="0" y1="{y_offset}" x2="{table_w}" y2="{y_offset}" stroke="#e2e8f0" stroke-width="1"/>')

        x_offset = 0
        for i, cell in enumerate(row):
            cw = table_w * col_widths[i] if i < len(col_widths) else 100
            
            # 简单处理过长文本的截断/换行 (这里为了美观，缩短字体或省略)
            text_str = cell
            if len(text_str) > 30 and num_cols > 2:
                 text_str = text_str[:28] + "..."
                 
            # 如果是两列的表格，右侧列可能很长，做个简单的拆分
            if num_cols == 2 and i == 1 and len(text_str) > 40:
                line1 = text_str[:40]
                line2 = text_str[40:80] + ("..." if len(text_str) > 80 else "")
                svg_parts.append(f'      <text x="{x_offset + cw/2}" y="{y_offset + row_height/2 - 2}" font-size="13" font-weight="400" fill="#334155" text-anchor="middle">{line1}</text>')
                svg_parts.append(f'      <text x="{x_offset + cw/2}" y="{y_offset + row_height/2 + 14}" font-size="13" font-weight="400" fill="#334155" text-anchor="middle">{line2}</text>')
            else:
                svg_parts.append(f'      <text x="{x_offset + cw/2}" y="{y_offset + row_height/2 + 5}" font-size="13" font-weight="400" fill="#334155" text-anchor="middle">{text_str}</text>')
            
            x_offset += cw

        y_offset += row_height

    # 绘制列分割线
    x_offset = 0
    for i in range(num_cols - 1):
        cw = table_w * col_widths[i]
        x_offset += cw
        svg_parts.append(f'      <line x1="{x_offset}" y1="0" x2="{x_offset}" y2="{y_offset}" stroke="#e2e8f0" stroke-width="1"/>')

    # 外边框
    svg_parts.append(f'      <rect x="0" y="0" width="{table_w}" height="{y_offset}" rx="12" fill="none" stroke="#cbd5e1" stroke-width="1"/>')
    svg_parts.append('    </g>')
    svg_parts.append('  </g>')
    svg_parts.append('</svg>')

    return "\n".join(svg_parts)


def process_docx_tables(file_path, out_dir, prefix):
    print(f"\n--- 处理 {os.path.basename(file_path)} ---")
    doc = docx.Document(file_path)
    
    os.makedirs(out_dir, exist_ok=True)
    
    svg_files = []
    
    for i, table in enumerate(doc.tables):
        if len(table.rows) == 0:
            continue
            
        headers = []
        for cell in table.rows[0].cells:
            text = cell.text.replace('\n', ' ').strip()
            if text not in headers:
                headers.append(text)
                
        rows = []
        for r_idx in range(1, len(table.rows)):
            row_data = []
            for cell in table.rows[r_idx].cells:
                text = cell.text.replace('\n', ' ').strip()
                if text not in row_data:
                    row_data.append(text)
            
            # 补齐列数
            while len(row_data) < len(headers):
                row_data.append("-")
            rows.append(row_data[:len(headers)])
            
        if not headers or not rows:
            continue
            
        svg_content = create_table_svg(headers, rows, width=900, row_height=50, title=f"表格 {i+1}")
        
        svg_filename = f"{prefix}_table_{i+1}.svg"
        svg_path = os.path.join(out_dir, svg_filename)
        
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
            
        svg_files.append(svg_path)
        print(f"✅ 生成 SVG: {svg_filename}")
        
    return svg_files

files_to_process = {
    r"E:\lawai\output\doc\区域初赛提交材料_项目简介_企鹅法庭_科创展示版_最终定稿.docx": "intro",
    r"E:\lawai\output\doc\区域初赛提交材料_项目Demo与补充材料_企鹅法庭_科创展示版_最终定稿.docx": "demo"
}

out_directory = r"E:\lawai\output\doc\diagrams\tables"

for f_path, prefix in files_to_process.items():
    process_docx_tables(f_path, out_directory, prefix)
