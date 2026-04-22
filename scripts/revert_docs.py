import os
import shutil

def revert_documents():
    # 之前保存了一份纯文字版的“流畅严谨版”，我们只需要把这个版本重新复制为最终提交版，就能清除掉所有后来加进去的插图了。
    
    intro_source = "E:/lawai/output/doc/区域初赛提交材料_项目简介_企鹅法庭_流畅严谨版.docx"
    demo_source = "E:/lawai/output/doc/区域初赛提交材料_项目Demo与补充材料_企鹅法庭_流畅严谨版.docx"
    
    intro_target = "E:/lawai/output/doc/区域初赛提交材料_项目简介_企鹅法庭_最终提交版.docx"
    demo_target = "E:/lawai/output/doc/区域初赛提交材料_项目Demo与补充材料_企鹅法庭_最终提交版.docx"
    
    if os.path.exists(intro_source):
        shutil.copy2(intro_source, intro_target)
        print(f"✅ Reverted and saved to: {intro_target}")
    
    if os.path.exists(demo_source):
        shutil.copy2(demo_source, demo_target)
        print(f"✅ Reverted and saved to: {demo_target}")
        
    # 我们还需要把之前删除 "(四)比赛展示与答辩场景" 的脚本在最终版上跑一下
    from docx import Document
    def remove_section(doc_path):
        doc = Document(doc_path)
        deleting = False
        elements_to_remove = []
        target_keywords = ["(四)比赛展示与答辩场景", "（四）比赛展示与答辩场景", "四、比赛展示与答辩场景", "(四) 比赛展示与答辩场景", "（四） 比赛展示与答辩场景"]
        for p in doc.paragraphs:
            text = p.text.replace(" ", "")
            if not deleting:
                for kw in target_keywords:
                    if kw.replace(" ", "") in text:
                        deleting = True
                        break
            else:
                if text.startswith("(五)") or text.startswith("（五）") or text.startswith("五、") or text.startswith("六、"):
                    deleting = False
            if deleting:
                elements_to_remove.append(p._element)
        if elements_to_remove:
            for el in elements_to_remove:
                parent = el.getparent()
                if parent is not None:
                    parent.remove(el)
            doc.save(doc_path)
            print(f"Removed section from {doc_path}")

    remove_section(intro_target)
    remove_section(demo_target)

if __name__ == "__main__":
    revert_documents()
