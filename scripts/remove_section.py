import os
from docx import Document

def remove_section(doc_path):
    if not os.path.exists(doc_path):
        print(f"File not found: {doc_path}")
        return False

    doc = Document(doc_path)
    deleting = False
    elements_to_remove = []
    
    # Target keywords that might be formatted with either half-width or full-width parentheses
    target_keywords = ["(四)比赛展示与答辩场景", "（四）比赛展示与答辩场景", "四、比赛展示与答辩场景", "(四) 比赛展示与答辩场景", "（四） 比赛展示与答辩场景"]

    for p in doc.paragraphs:
        text = p.text.replace(" ", "")  # 去除空格以便匹配
        
        # 判断是否进入需要删除的章节
        if not deleting:
            for kw in target_keywords:
                if kw.replace(" ", "") in text:
                    deleting = True
                    print(f"✅ Found target section in {os.path.basename(doc_path)}: {p.text}")
                    break
        else:
            # 如果当前在删除模式，需要判断何时停止（遇到下一个同级或高级标题）
            # 例如遇到 (五)、五、六、等
            if text.startswith("(五)") or text.startswith("（五）") or text.startswith("五、") or text.startswith("六、"):
                deleting = False
                print(f"🛑 Stopped deleting at next section: {p.text}")
                
        if deleting:
            elements_to_remove.append(p._element)

    if elements_to_remove:
        # Delete elements from XML tree
        for el in elements_to_remove:
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)
                
        doc.save(doc_path)
        print(f"✅ Successfully removed {len(elements_to_remove)} paragraphs from {os.path.basename(doc_path)}")
        return True
    else:
        print(f"⚠️ Target section not found in {os.path.basename(doc_path)}")
        return False

def main():
    intro_doc = "E:/lawai/output/doc/区域初赛提交材料_项目简介_企鹅法庭_图文并茂版.docx"
    demo_doc = "E:/lawai/output/doc/区域初赛提交材料_项目Demo与补充材料_企鹅法庭_图文并茂版.docx"
    
    print("Checking intro document...")
    remove_section(intro_doc)
    
    print("\nChecking demo document...")
    remove_section(demo_doc)

if __name__ == "__main__":
    main()
