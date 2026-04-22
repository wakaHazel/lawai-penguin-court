import os
import docx

def find_keywords(file_path):
    print(f"--- 搜索 {os.path.basename(file_path)} ---")
    doc = docx.Document(file_path)
    keywords = ["答辩", "评审", "评委", "比赛", "初赛", "参赛", "区域赛"]
    
    for i, p in enumerate(doc.paragraphs):
        text = p.text
        for kw in keywords:
            if kw in text:
                print(f"段落 {i}: {text}")
                break

files = [
    r"E:\lawai\output\doc\区域初赛提交材料_项目简介_企鹅法庭_架构图文版.docx",
    r"E:\lawai\output\doc\区域初赛提交材料_项目Demo与补充材料_企鹅法庭_架构图文版.docx"
]

for f in files:
    find_keywords(f)
