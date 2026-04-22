import os
import base64
import time
from pathlib import Path
from openai import OpenAI

ROOT = Path("E:/lawai")
API_ENV_FILE = ROOT / "apps" / "api" / ".env.local"
OUTPUT_DIR = ROOT / "data" / "cg-library" / "cartoon-court"

# 提取所有图片必须严格遵守的公共样式限制：
# 1. 扁平化矢量插画（Flat vector illustration）
# 2. 现代专业感
# 3. 绝对不含任何乱码、文字、数字、水印、字母（非常重要）
# 4. 去除3D和写实、古风
COMMON_STYLE = (
    " 高端现代的扁平化矢量插画风格(Flat vector illustration)，几何线条极简干净，色彩专业、明亮且严肃。"
    "绝对不要写实照片，绝对不要3D渲染，绝对不要古装毛笔。"
    "横版构图。画面中绝对不能出现任何文字、字母、数字、乱码或水印（No text, no letters, no numbers, no gibberish, no watermarks）。"
)

SCENE_SPECS = [
    {
        "key": "prepare",
        "filename": "stage_prepare.png",
        "prompt": "中国现代律师事务所办公室场景，一只戴着眼镜、穿着现代黑色西装的可爱企鹅坐在宽大的办公桌前。桌面上摆放着整齐的纸质案卷和一台现代电脑显示器。" + COMMON_STYLE
    },
    {
        "key": "investigation",
        "filename": "stage_investigation.png",
        "prompt": "中国现代标准民事法庭场景，法庭调查阶段。一只穿着黑色法袍的企鹅法官前倾身子发问，下方原告席上一只穿着现代西装的企鹅正在陈述事实，被告席的西装企鹅认真倾听。背景是带有木质墙板的现代真实法庭内部，庄重肃穆。" + COMMON_STYLE
    },
    {
        "key": "evidence",
        "filename": "stage_evidence.png",
        "prompt": "中国现代标准民事法庭场景，举证质证阶段。原告席的现代西装企鹅向法庭展示证据，桌面上摆放着纸质文件、银行流水等材料（纯图形）。法官企鹅严肃审视，被告西装企鹅神情紧张。背景为现代真实法庭内部。" + COMMON_STYLE
    },
    {
        "key": "debate",
        "filename": "stage_debate.png",
        "prompt": "中国现代标准民事法庭场景，一只穿着黑色法袍的企鹅法官端坐在高高的木质审判台后。下方原告席和被告席上，两只穿着现代西装的企鹅代理人正在严肃对峙。背景是带有木质墙板的现代真实法庭内部，庄重肃穆。" + COMMON_STYLE
    },
    {
        "key": "final_statement",
        "filename": "stage_final_statement.png",
        "prompt": "中国现代标准民事法庭场景，最后陈述阶段。一只穿西装的企鹅当事人站立做最后陈述，双手拿着陈述稿（无文字）。法袍企鹅法官安静聆听，整个法庭气氛克制而凝重。背景为现代真实法庭内部。" + COMMON_STYLE
    },
    {
        "key": "mediation_or_judgment",
        "filename": "stage_mediation_or_judgment.png",
        "prompt": "中国现代标准民事法庭场景，宣判与调解阶段。穿着法袍的企鹅法官居中严肃宣布结果。下方原被告西装企鹅分别露出紧张与思考的表情。背景为现代真实法庭内部，光影柔和庄重。" + COMMON_STYLE
    },
    {
        "key": "report_ready",
        "filename": "stage_report_ready.png",
        "prompt": "中国现代会议室场景，一只穿着现代西装的企鹅手里拿着一份带有绿色对勾标识的分析报告文件夹。背景是一块干净的白板，白板上只有简单的饼状图和上升的折线图（纯图形）。" + COMMON_STYLE
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
