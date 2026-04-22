import os
import docx

def extract_tables(file_path):
    print(f"--- 提取 {os.path.basename(file_path)} 的表格 ---")
    doc = docx.Document(file_path)
    
    for i, table in enumerate(doc.tables):
        print(f"\n[表格 {i + 1}]")
        for r_idx, row in enumerate(table.rows):
            row_data = []
            for cell in row.cells:
                text = cell.text.replace('\n', ' ').strip()
                if text not in row_data: # 简单去重合并单元格
                    row_data.append(text)
            print(f"  行 {r_idx + 1}: {' | '.join(row_data)}")

files = [
    r"E:\lawai\output\doc\区域初赛提交材料_项目简介_企鹅法庭_科创展示版_最终定稿.docx",
    r"E:\lawai\output\doc\区域初赛提交材料_项目Demo与补充材料_企鹅法庭_科创展示版_最终定稿.docx"
]

for f in files:
    extract_tables(f)
