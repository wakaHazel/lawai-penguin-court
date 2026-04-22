import os
import base64
import time
from pathlib import Path
from openai import OpenAI

ROOT = Path("E:/lawai")
API_ENV_FILE = ROOT / "apps" / "api" / ".env.local"
OUTPUT_DIR = ROOT / "data" / "cg-library" / "cartoon-court"

# 终极平衡版提示词：
# 1. 恢复企鹅的“萌感”和“治愈系”属性（圆润可爱的造型）。
# 2. 整体画风采用“精美的现代治愈系插画（Beautiful modern healing illustration）”风格。
# 3. 场景和衣服保持专业（西装、法袍、现代法庭），但通过光影、柔和的线条和可爱的表情来冲淡死板感。
# 4. 绝对不含任何乱码、文字、数字、水印、字母（非常重要）。
COMMON_STYLE = (
    " 精美的现代治愈系矢量插画风格(Beautiful modern healing vector illustration)。"
    "主角是圆滚滚、表情生动可爱的拟人化企鹅，身穿合体的小西装或小法袍，造型萌趣治愈，让人觉得很亲切。"
    "法庭和办公室背景现代且干净，光影温暖柔和，色彩明亮治愈，既专业又不失可爱。"
    "绝对不要写实照片，绝对不要3D过度渲染，绝对不要古装毛笔。"
    "横版构图。画面中绝对不能出现任何文字、字母、数字、乱码或水印（No text, no letters, no numbers, no gibberish, no watermarks）。"
)

SCENE_SPECS = [
    {
        "key": "prepare",
        "filename": "stage_prepare.png",
        "prompt": "现代律师事务所办公室场景。一只戴着眼镜、穿着小西装的可爱企鹅正坐在办公桌前，小翅膀托着下巴思考。桌面上整齐地摆放着纸质案卷和一台现代电脑显示器。画面温馨治愈。" + COMMON_STYLE
    },
    {
        "key": "investigation",
        "filename": "stage_investigation.png",
        "prompt": "现代法庭调查阶段。一只穿着小法袍的可爱企鹅法官坐在木质审判台后，正好奇地倾听。下方原告席上一只穿着西装的萌企鹅正在认真陈述。背景是带有木质墙板的现代法庭内部，光影温暖。" + COMMON_STYLE
    },
    {
        "key": "evidence",
        "filename": "stage_evidence.png",
        "prompt": "现代法庭举证质证阶段。原告席的西装小企鹅举起一份画着图表的纸质文件（纯图形）展示证据。法官企鹅专注地看着，被告西装企鹅在一旁紧张得流了一滴汗。背景为明亮温暖的法庭内部。" + COMMON_STYLE
    },
    {
        "key": "debate",
        "filename": "stage_debate.png",
        "prompt": "现代法庭辩论阶段。一只穿着小法袍的企鹅法官端坐在审判台后。下方原告席和被告席上，两只穿着小西装的企鹅正气鼓鼓地互相指着对方辩论，表情生动可爱。背景是现代法庭内部。" + COMMON_STYLE
    },
    {
        "key": "final_statement",
        "filename": "stage_final_statement.png",
        "prompt": "现代法庭最后陈述阶段。一只穿西装的可爱企鹅站立着，双手紧紧拿着一份陈述稿（无文字），表情真挚。法袍企鹅法官安静温柔地聆听，法庭气氛治愈且平和。背景为现代法庭内部。" + COMMON_STYLE
    },
    {
        "key": "mediation_or_judgment",
        "filename": "stage_mediation_or_judgment.png",
        "prompt": "现代法庭宣判与调解阶段。穿着小法袍的企鹅法官开心地宣布结果。下方原被告两只西装小企鹅也如释重负，互相握手言和。背景光影柔和温暖，充满治愈感。" + COMMON_STYLE
    },
    {
        "key": "report_ready",
        "filename": "stage_report_ready.png",
        "prompt": "现代会议室场景。一只穿着小西装的可爱企鹅正开心地抱着一份带有绿色对勾标识的报告文件夹。背景是一块干净的白板，上面画着简单的彩色饼状图和折线图（纯图形）。" + COMMON_STYLE
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
