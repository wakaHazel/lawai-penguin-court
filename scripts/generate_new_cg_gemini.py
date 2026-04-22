import os
import base64
from pathlib import Path
from openai import OpenAI

ROOT = Path("E:/lawai")
API_ENV_FILE = ROOT / "apps" / "api" / ".env.local"
OUTPUT_DIR = ROOT / "data" / "cg-library" / "cartoon-court"

# 更新提示词，去除“日系法庭冒险感”、“绘本感”，确保：
# 1. 完全现代中国法庭真实严肃的布局（国徽、木质审判台、西装/法袍）。
# 2. 完全没有乱码文字（No text, no gibberish, no letters, no watermarks）。
# 3. 拟人化企鹅造型（符合IP），但是呈现出现代高级感和专业感（类似扁平化矢量插画）。

SCENE_SPECS = [
    {
        "key": "prepare",
        "filename": "stage_prepare.png",
        "prompt": (
            "中国现代律师事务所办公室场景，一只戴着眼镜、穿着现代黑色西装的可爱企鹅坐在宽大的办公桌前。"
            "桌面上摆放着整齐的纸质案卷和一台现代电脑显示器。"
            "高端现代的扁平化矢量插画风格(Flat vector illustration)，几何线条极简干净，色彩专业、明亮且严肃。"
            "绝对不要写实照片，绝对不要3D渲染，绝对不要古装毛笔。"
            "横版构图，空间层次明确。画面中绝对不能出现任何文字、字母、乱码或水印（No text, no letters, no gibberish）。"
        ),
    },
    {
        "key": "debate",
        "filename": "stage_debate.png",
        "prompt": (
            "中国现代标准民事法庭场景，一只穿着黑色法袍的企鹅法官端坐在高高的木质审判台后。"
            "下方原告席和被告席上，两只穿着现代西装的企鹅代理人正在严肃对峙。"
            "背景是带有木质墙板的现代真实法庭内部，庄重肃穆。"
            "高端现代的扁平化矢量插画风格(Flat vector illustration)，色彩克制，强调法庭的对抗感与专业感。"
            "绝对不要古装，不要毛笔，不要写实照片，绝对不要3D渲染。"
            "横版构图。画面中绝对不能出现任何文字、字母、数字、乱码或水印（No text, no gibberish, no letters）。"
        ),
    },
    {
        "key": "report_ready",
        "filename": "stage_report_ready.png",
        "prompt": (
            "中国现代会议室场景，一只穿着现代西装的企鹅手里拿着一份带有绿色对勾标识的分析报告文件夹。"
            "背景是一块干净的白板，白板上只有简单的饼状图和上升的折线图（纯图形，无数字无文字）。"
            "高端现代的扁平化矢量插画风格(Flat vector illustration)，科技感与专业感并存，色调冷静明亮。"
            "绝对不要古装毛笔，绝对不要写实照片，绝对不要3D渲染。"
            "横版构图。画面中绝对不能出现任何文字、字母、数字、乱码或水印（No text, no numbers, no gibberish）。"
        ),
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
        except Exception as e:
            print(f"❌ Failed to generate {spec['key']}: {e}")

if __name__ == "__main__":
    generate_library()
