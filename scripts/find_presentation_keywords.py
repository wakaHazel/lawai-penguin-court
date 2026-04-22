import os
import docx

def find_presentation_keywords(file_path):
    print(f"--- 深度搜索 {os.path.basename(file_path)} ---")
    doc = docx.Document(file_path)
    keywords = ["展示", "演示", "答辩", "评委", "评审", "提交材料", "比赛", "初赛", "参赛", "区域赛"]
    
    for i, p in enumerate(doc.paragraphs):
        text = p.text
        for kw in keywords:
            if kw in text:
                print(f"段落 {i} [包含 '{kw}']: {text}")
                break

files = [
    r"E:\lawai\output\doc\区域初赛提交材料_项目简介_企鹅法庭_去比赛痕迹_纯净版.docx",
    r"E:\lawai\output\doc\区域初赛提交材料_项目Demo与补充材料_企鹅法庭_去比赛痕迹_纯净版.docx"
]

for f in files:
    find_presentation_keywords(f)
