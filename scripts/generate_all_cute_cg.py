import os
import base64
import time
from pathlib import Path
from openai import OpenAI

ROOT = Path("E:/lawai")
API_ENV_FILE = ROOT / "apps" / "api" / ".env.local"
OUTPUT_DIR = ROOT / "data" / "cg-library" / "cartoon-court"

# 提取所有图片必须严格遵守的公共样式限制：
# 1. 现代背景，但画风是“可爱的卡通插画”、“绘本风”
# 2. 企鹅要Q萌可爱（大眼睛、圆滚滚）
# 3. 绝对不含任何乱码、文字、数字、水印、字母（非常重要）
# 4. 去除3D和写实、古风
COMMON_STYLE = (
    " 极度可爱的二维卡通绘本插画风格(Cute 2D cartoon illustration, picture book style)。"
    "主角是圆滚滚、大眼睛的超萌拟人化企鹅。线条柔和圆润，色彩温暖明亮且治愈。"
    "法庭和办公室背景要现代化，但经过卡通化、温馨化的处理。"
    "绝对不要写实照片，绝对不要3D渲染，绝对不要古装毛笔。"
    "横版构图。画面中绝对不能出现任何文字、字母、数字、乱码或水印（No text, no letters, no numbers, no gibberish, no watermarks）。"
)

SCENE_SPECS = [
    {
        "key": "prepare",
        "filename": "stage_prepare.png",
        "prompt": "现代律师事务所的温馨卡通场景。一只戴着超大黑框眼镜、穿着小西装的超萌胖企鹅坐在办公桌前。桌面上堆着可爱的卡通案卷本和一台卡通电脑显示器。" + COMMON_STYLE
    },
    {
        "key": "investigation",
        "filename": "stage_investigation.png",
        "prompt": "现代卡通法庭场景，法庭调查阶段。一只穿着小法袍的超萌企鹅法官正举着卡通小木槌发问。下方原告席上一只穿着小西装的企鹅正在认真陈述。背景是温暖木质色调的现代卡通法庭。" + COMMON_STYLE
    },
    {
        "key": "evidence",
        "filename": "stage_evidence.png",
        "prompt": "现代卡通法庭场景，举证质证阶段。原告席的西装小企鹅正举起一份画着图表的纸质材料（纯图形）。法官小企鹅戴着眼镜仔细看，被告小企鹅在一旁紧张地流汗。背景为温暖的卡通法庭内部。" + COMMON_STYLE
    },
    {
        "key": "debate",
        "filename": "stage_debate.png",
        "prompt": "现代卡通法庭场景。一只穿着小法袍的企鹅法官端坐在木质审判台后。下方原告席和被告席上，两只穿着小西装的企鹅正气鼓鼓地互相指着对方辩论。背景是温暖明亮的卡通法庭内部。" + COMMON_STYLE
    },
    {
        "key": "final_statement",
        "filename": "stage_final_statement.png",
        "prompt": "现代卡通法庭场景，最后陈述阶段。一只穿西装的超萌企鹅站立着，双手紧紧拿着一份陈述稿（无文字）。法袍小企鹅法官安静地托着下巴聆听。画面温馨且有故事感。背景为现代卡通法庭内部。" + COMMON_STYLE
    },
    {
        "key": "mediation_or_judgment",
        "filename": "stage_mediation_or_judgment.png",
        "prompt": "现代卡通法庭场景。穿着小法袍的企鹅法官站在中间，拿着一张写满绿色对勾的判决纸（无文字），看起来非常开心。下方原被告两只小企鹅也握手言和。光影温暖治愈。" + COMMON_STYLE
    },
    {
        "key": "report_ready",
        "filename": "stage_report_ready.png",
        "prompt": "现代卡通会议室场景。一只穿着小西装的超萌胖企鹅正开心地抱着一份带有大绿色对勾的报告文件夹。背景是一块卡通白板，上面画着可爱的彩色饼状图和折线图（纯图形）。" + COMMON_STYLE
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
