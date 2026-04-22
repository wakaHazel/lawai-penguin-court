import os
import base64
import time
from pathlib import Path
from openai import OpenAI

ROOT = Path("E:/lawai")
API_ENV_FILE = ROOT / "apps" / "api" / ".env.local"
OUTPUT_DIR = ROOT / "data" / "cg-library" / "cartoon-court"

# 更新风格约束：
# 1. 降低过度幼态化（去掉超大眼睛、极度可爱等词）。
# 2. 追求一种“轻量化、专业且带有一点亲和力的矢量插画”或“等距微缩模型风（Isometric/Flat Vector）”。
# 3. 企鹅造型是标准的拟人化企鹅，有职场感。
# 4. 依然严格保持“无文字、无乱码”红线。
COMMON_STYLE = (
    " 高端现代的扁平化轻量插画风格(Clean flat vector illustration, corporate style)。"
    "主角是拟人化的企鹅，身穿合体的西装或法袍，造型简洁大方，带有一点亲和力但不要过度幼态（正常眼睛比例，不要夸张的大眼睛）。"
    "法庭和办公室背景现代且专业，线条干净，色彩明亮柔和。"
    "绝对不要写实照片，绝对不要3D过度渲染，绝对不要古装毛笔。"
    "横版构图。画面中绝对不能出现任何文字、字母、数字、乱码或水印（No text, no letters, no numbers, no gibberish, no watermarks）。"
)

SCENE_SPECS = [
    {
        "key": "prepare",
        "filename": "stage_prepare.png",
        "prompt": "现代律师事务所办公室场景。一只穿着现代黑色西装的企鹅坐在办公桌前。桌面上整齐地摆放着纸质案卷和一台现代电脑显示器。画面表现出专业的职场氛围。" + COMMON_STYLE
    },
    {
        "key": "investigation",
        "filename": "stage_investigation.png",
        "prompt": "现代标准民事法庭场景，法庭调查阶段。一只穿着黑色法袍的企鹅法官坐在审判台后发问。下方原告席上一只穿着现代西装的企鹅正在陈述事实。背景是带有木质墙板的现代法庭内部，庄重且明亮。" + COMMON_STYLE
    },
    {
        "key": "evidence",
        "filename": "stage_evidence.png",
        "prompt": "现代标准民事法庭场景，举证质证阶段。原告席的西装企鹅向法庭展示证据，桌面上摆放着纸质文件、银行流水等材料（纯图形）。法官企鹅专注审视，被告西装企鹅在倾听。背景为现代法庭内部。" + COMMON_STYLE
    },
    {
        "key": "debate",
        "filename": "stage_debate.png",
        "prompt": "现代标准民事法庭场景。一只穿着黑色法袍的企鹅法官端坐在木质审判台后。下方原告席和被告席上，两只穿着现代西装的企鹅代理人正在专业对峙。背景是现代法庭内部。" + COMMON_STYLE
    },
    {
        "key": "final_statement",
        "filename": "stage_final_statement.png",
        "prompt": "现代标准民事法庭场景，最后陈述阶段。一只穿西装的企鹅站立着，双手拿着一份陈述稿（无文字）。法袍企鹅法官安静聆听，法庭气氛专业而平和。背景为现代法庭内部。" + COMMON_STYLE
    },
    {
        "key": "mediation_or_judgment",
        "filename": "stage_mediation_or_judgment.png",
        "prompt": "现代标准民事法庭场景，宣判与调解阶段。穿着法袍的企鹅法官站在中间宣布结果，手里拿着一份判决书（纯图形无文字）。下方原被告两只西装企鹅互相握手。光影柔和庄重。" + COMMON_STYLE
    },
    {
        "key": "report_ready",
        "filename": "stage_report_ready.png",
        "prompt": "现代企业会议室场景。一只穿着现代西装的企鹅手里拿着一份带有绿色对勾标识的分析报告文件夹。背景是一块干净的白板，上面画着简单的饼状图和折线图（纯图形）。" + COMMON_STYLE
    }
]

def load_env_value(path: Path, key: str) -> str:
    if not path.exists():
        return ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        current_key, value = line.split("=", 1)
        if current_key.strip() == key:
            return value.strip().strip('"').strip("'")
    return ""

def create_client() -> OpenAI:
    api_key = load_env_value(API_ENV_FILE, "V3CM_API_KEY")
    base_url = load_env_value(API_ENV_FILE, "V3CM_BASE_URL") or "https://api.v3.cm/v1"
    if not api_key:
        raise RuntimeError("V3CM_API_KEY missing in apps/api/.env.local")
    return OpenAI(api_key=api_key, base_url=base_url)

def generate_library() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        client = create_client()
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    for spec in SCENE_SPECS:
        target_path = OUTPUT_DIR / spec["filename"]
        print(f"generating {spec['key']} -> {target_path.name}")
        try:
            response = client.images.generate(
                model="gemini-3-pro-image-preview-2k",
                prompt=spec["prompt"],
                n=1,
                size="2752x1536",
                response_format="b64_json",
            )
            image_bytes = base64.b64decode(response.data[0].b64_json)
            target_path.write_bytes(image_bytes)
            print(f"✅ Success: {target_path.name}")
            time.sleep(2) # 稍微暂停一下，避免触发限流
        except Exception as e:
            print(f"❌ Failed to generate {spec['key']}: {e}")

if __name__ == "__main__":
    generate_library()
