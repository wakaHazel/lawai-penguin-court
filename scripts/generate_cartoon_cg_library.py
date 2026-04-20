from __future__ import annotations

import base64
from pathlib import Path

from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]
API_ENV_FILE = ROOT / "apps" / "api" / ".env.local"
OUTPUT_DIR = ROOT / "data" / "cg-library" / "cartoon-court"


SCENE_SPECS = [
    {
        "key": "prepare",
        "filename": "stage_prepare.png",
        "prompt": (
            "中国民事法庭题材卡通插画，拟人化企鹅法官敲响法槌，准备宣布开庭，"
            "企鹅原告、企鹅被告、企鹅书记员都已就位，桌面上摆有卷宗与诉状。"
            "二维卡通插画，绘本感，清晰描边，柔和暖米色光影，轻微日系法庭冒险感，"
            "可爱但专业庄重，绝对不要写实照片风，绝对不要3D渲染。"
            "横版首屏构图，画面简洁，空间层次明确。无文字、无水印、无界面元素、无英文。"
        ),
    },
    {
        "key": "investigation",
        "filename": "stage_investigation.png",
        "prompt": (
            "中国民事法庭题材卡通插画，法官企鹅前倾发问，企鹅原告正在陈述事实经过，"
            "被告席认真听，书记员记录，法庭进入法庭调查阶段。"
            "二维卡通插画，绘本感，清晰描边，柔和暖色，故事感强，"
            "绝对不要写实，绝对不要3D。横版，适合网页首屏。"
            "无文字、无水印、无界面元素、无英文。"
        ),
    },
    {
        "key": "evidence",
        "filename": "stage_evidence.png",
        "prompt": (
            "中国民事法庭题材卡通插画，企鹅原告一侧展示证据材料，桌面中央摆着证据文件、聊天记录、工资流水等纸质材料，"
            "法官企鹅严肃审视，被告企鹅神情紧张，法庭处于举证质证阶段。"
            "二维卡通插画，绘本感，清晰描边，柔和暖棕色法庭环境，"
            "可爱但有攻防张力，不要写实，不要3D。横版构图。"
            "无文字、无水印、无界面元素、无英文。"
        ),
    },
    {
        "key": "debate",
        "filename": "stage_debate.png",
        "prompt": (
            "中国民事法庭题材卡通插画，企鹅原告代理人与企鹅被告代理人正在法庭辩论，"
            "双方姿态紧绷、桌面有提纲和案卷，法官企鹅居中观察，气氛集中。"
            "二维卡通插画，绘本感，清晰描边，柔和但更有对峙张力的光影，"
            "绝对不要写实照片风，绝对不要3D渲染。横版。"
            "无文字、无水印、无界面元素、无英文。"
        ),
    },
    {
        "key": "final_statement",
        "filename": "stage_final_statement.png",
        "prompt": (
            "中国民事法庭题材卡通插画，企鹅当事人站起做最后陈述，双手握着陈述稿，"
            "法官企鹅安静聆听，整个法庭进入收束时刻，气氛克制而凝重。"
            "二维卡通插画，绘本感，清晰描边，温暖光影，带一点情绪收束感，"
            "不要写实，不要3D。横版首屏插画。"
            "无文字、无水印、无界面元素、无英文。"
        ),
    },
    {
        "key": "mediation_or_judgment",
        "filename": "stage_mediation_or_judgment.png",
        "prompt": (
            "中国民事法庭题材卡通插画，企鹅法官居中宣布结果或组织调解，"
            "原被告企鹅分别露出紧张与思考表情，法庭进入结果阶段。"
            "二维卡通插画，绘本感，清晰描边，柔和庄重的金棕色光影，"
            "画面有结果来临的仪式感，但保持卡通感，不要写实，不要3D。横版。"
            "无文字、无水印、无界面元素、无英文。"
        ),
    },
    {
        "key": "report_ready",
        "filename": "stage_report_ready.png",
        "prompt": (
            "中国法庭题材卡通插画，审理结束后的法庭空镜头，桌面上留下整理好的案卷、法槌和证据材料，"
            "带有复盘与回看感，整体安静、整洁、温和。"
            "二维卡通插画，绘本感，清晰描边，柔和暖色，绝对不要写实，不要3D。"
            "横版，适合网页报告阶段背景。无文字、无水印、无界面元素、无英文。"
        ),
    },
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
    client = create_client()

    for spec in SCENE_SPECS:
        target_path = OUTPUT_DIR / spec["filename"]
        print(f"generating {spec['key']} -> {target_path.name}")
        response = client.images.generate(
            model="gemini-3-pro-image-preview-2k",
            prompt=spec["prompt"],
            n=1,
            size="2752x1536",
            response_format="b64_json",
        )
        image_bytes = base64.b64decode(response.data[0].b64_json)
        target_path.write_bytes(image_bytes)


if __name__ == "__main__":
    generate_library()
