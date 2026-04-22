import os
import sys
from docx import Document

def print_full_text(file_path):
    doc = Document(file_path)
    print(f"\n==== EXAMINING: {file_path} ====\n")
    # Only print first 50 paragraphs that have actual text to see what else needs polishing
    count = 0
    for p in doc.paragraphs:
        text = p.text.strip()
        if text:
            print(f"P: {text}")
            count += 1
        if count > 30:
            break
    print("===========================================\n")

if __name__ == "__main__":
    file1 = "E:/lawai/output/doc/区域初赛提交材料_项目简介_企鹅法庭_论文标准版_修订版.docx"
    file2 = "E:/lawai/output/doc/区域初赛提交材料_项目Demo与补充材料_企鹅法庭_论文标准版_修订版.docx"
    
    print_full_text(file1)
    print_full_text(file2)
