import os

def create_svg(filename, content):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 成功生成精美信息图 SVG: {filename}")

def main():
    out_dir = r"E:\lawai\output\doc\diagrams\infographics"
    os.makedirs(out_dir, exist_ok=True)

    # ==========================================
    # 1. 目标用户与核心价值 (替换《项目简介》表3)
    # ==========================================
    user_personas_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="900" height="420" viewBox="0 0 900 420" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="card-shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="6" stdDeviation="12" flood-color="#0f172a" flood-opacity="0.06"/>
    </filter>
    <linearGradient id="grad-p1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3b82f6" />
      <stop offset="100%" stop-color="#2563eb" />
    </linearGradient>
    <linearGradient id="grad-p2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8b5cf6" />
      <stop offset="100%" stop-color="#7c3aed" />
    </linearGradient>
    <linearGradient id="grad-p3" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10b981" />
      <stop offset="100%" stop-color="#059669" />
    </linearGradient>
  </defs>

  <rect width="900" height="420" fill="#f8fafc" rx="20"/>

  <g font-family="system-ui, -apple-system, sans-serif">
    <text x="450" y="45" font-size="24" font-weight="700" fill="#0f172a" text-anchor="middle" letter-spacing="1">目标用户画像与核心价值交付</text>
    <text x="450" y="70" font-size="13" font-weight="400" fill="#64748b" text-anchor="middle" letter-spacing="1">TARGET PERSONAS &amp; VALUE DELIVERY</text>

    <!-- Card 1 -->
    <g transform="translate(40, 110)">
      <rect width="250" height="260" rx="16" fill="#ffffff" filter="url(#card-shadow)"/>
      <path d="M0 16 Q0 0 16 0 L234 0 Q250 0 250 16 L250 60 L0 60 Z" fill="url(#grad-p1)"/>
      <text x="125" y="32" font-size="18" font-weight="700" fill="#ffffff" text-anchor="middle">普通诉讼参与人</text>

      <circle cx="125" cy="60" r="20" fill="#eff6ff" stroke="#ffffff" stroke-width="3"/>
      <text x="125" y="65" font-size="14" font-weight="700" fill="#2563eb" text-anchor="middle">01</text>

      <text x="25" y="115" font-size="14" font-weight="700" fill="#334155">主要特征</text>
      <text x="25" y="140" font-size="13" font-weight="400" fill="#64748b">缺乏系统法律训练，案情</text>
      <text x="25" y="160" font-size="13" font-weight="400" fill="#64748b">掌握零散，证据判断力弱</text>

      <text x="25" y="195" font-size="14" font-weight="700" fill="#334155">核心诉求</text>
      <text x="25" y="220" font-size="13" font-weight="400" fill="#64748b">看懂案子、预判上庭风险</text>

      <rect x="20" y="250" width="210" height="40" rx="8" fill="#eff6ff"/>
      <text x="125" y="275" font-size="13" font-weight="600" fill="#1e3a8a" text-anchor="middle">输出证据缺口与备战建议</text>
    </g>

    <!-- Card 2 -->
    <g transform="translate(325, 110)">
      <rect width="250" height="260" rx="16" fill="#ffffff" filter="url(#card-shadow)"/>
      <path d="M0 16 Q0 0 16 0 L234 0 Q250 0 250 16 L250 60 L0 60 Z" fill="url(#grad-p2)"/>
      <text x="125" y="32" font-size="18" font-weight="700" fill="#ffffff" text-anchor="middle">法学生与模拟法庭</text>

      <circle cx="125" cy="60" r="20" fill="#faf5ff" stroke="#ffffff" stroke-width="3"/>
      <text x="125" y="65" font-size="14" font-weight="700" fill="#7c3aed" text-anchor="middle">02</text>

      <text x="25" y="115" font-size="14" font-weight="700" fill="#334155">主要特征</text>
      <text x="25" y="140" font-size="13" font-weight="400" fill="#64748b">有一定法律知识储备，但</text>
      <text x="25" y="160" font-size="13" font-weight="400" fill="#64748b">缺乏真实的庭审对抗经验</text>

      <text x="25" y="195" font-size="14" font-weight="700" fill="#334155">核心诉求</text>
      <text x="25" y="220" font-size="13" font-weight="400" fill="#64748b">训练表达、验证策略差异</text>

      <rect x="20" y="250" width="210" height="40" rx="8" fill="#faf5ff"/>
      <text x="125" y="275" font-size="13" font-weight="600" fill="#581c87" text-anchor="middle">提供阶段化推演与复盘报告</text>
    </g>

    <!-- Card 3 -->
    <g transform="translate(610, 110)">
      <rect width="250" height="260" rx="16" fill="#ffffff" filter="url(#card-shadow)"/>
      <path d="M0 16 Q0 0 16 0 L234 0 Q250 0 250 16 L250 60 L0 60 Z" fill="url(#grad-p3)"/>
      <text x="125" y="32" font-size="18" font-weight="700" fill="#ffffff" text-anchor="middle">普法与展示人群</text>

      <circle cx="125" cy="60" r="20" fill="#ecfdf5" stroke="#ffffff" stroke-width="3"/>
      <text x="125" y="65" font-size="14" font-weight="700" fill="#059669" text-anchor="middle">03</text>

      <text x="25" y="115" font-size="14" font-weight="700" fill="#334155">主要特征</text>
      <text x="25" y="140" font-size="13" font-weight="400" fill="#64748b">需要可视化、可演示、可</text>
      <text x="25" y="160" font-size="13" font-weight="400" fill="#64748b">讲解的智慧法律系统样例</text>

      <text x="25" y="195" font-size="14" font-weight="700" fill="#334155">核心诉求</text>
      <text x="25" y="220" font-size="13" font-weight="400" fill="#64748b">用一个系统展示AI结合形态</text>

      <rect x="20" y="250" width="210" height="40" rx="8" fill="#ecfdf5"/>
      <text x="125" y="275" font-size="13" font-weight="600" fill="#065f46" text-anchor="middle">形成完整主链路与成果展示</text>
    </g>
  </g>
</svg>"""

    # ==========================================
    # 2. AI 工具链矩阵 (替换《项目简介》表7)
    # ==========================================
    ai_toolchain_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="900" height="500" viewBox="0 0 900 500" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="node-shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="16" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
    <linearGradient id="grad-core" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e40af" />
      <stop offset="100%" stop-color="#1e3a8a" />
    </linearGradient>
  </defs>

  <rect width="900" height="500" fill="#f8fafc" rx="24"/>

  <g font-family="system-ui, -apple-system, sans-serif">
    <text x="450" y="45" font-size="26" font-weight="700" fill="#0f172a" text-anchor="middle" letter-spacing="1">AI 工具链与生态矩阵</text>
    <text x="450" y="70" font-size="14" font-weight="400" fill="#64748b" text-anchor="middle" letter-spacing="1">AI TOOLCHAIN &amp; ECOSYSTEM MATRIX</text>

    <!-- Connections -->
    <path d="M 450 250 L 220 160" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="6,6"/>
    <path d="M 450 250 L 680 160" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="6,6"/>
    <path d="M 450 250 L 220 380" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="6,6"/>
    <path d="M 450 250 L 680 380" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="6,6"/>
    <path d="M 450 250 L 450 160" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="6,6"/>

    <!-- Central Node -->
    <g transform="translate(350, 200)" filter="url(#node-shadow)">
      <rect width="200" height="100" rx="20" fill="url(#grad-core)"/>
      <text x="100" y="45" font-size="20" font-weight="700" fill="#ffffff" text-anchor="middle">企鹅法庭</text>
      <text x="100" y="70" font-size="14" font-weight="400" fill="#bfdbfe" text-anchor="middle">核心控制层</text>
    </g>

    <!-- Node 1: 腾讯元器 -->
    <g transform="translate(360, 100)" filter="url(#node-shadow)">
      <rect width="180" height="60" rx="12" fill="#ffffff"/>
      <rect x="0" y="0" width="8" height="60" rx="4" fill="#3b82f6"/>
      <text x="25" y="26" font-size="16" font-weight="700" fill="#1e293b">腾讯元器</text>
      <text x="25" y="46" font-size="12" font-weight="400" fill="#64748b">智能体工作流编排基座</text>
    </g>

    <!-- Node 2: CodeBuddy -->
    <g transform="translate(80, 130)" filter="url(#node-shadow)">
      <rect width="180" height="60" rx="12" fill="#ffffff"/>
      <rect x="0" y="0" width="8" height="60" rx="4" fill="#8b5cf6"/>
      <text x="25" y="26" font-size="16" font-weight="700" fill="#1e293b">CodeBuddy</text>
      <text x="25" y="46" font-size="12" font-weight="400" fill="#64748b">工程开发与接口联调</text>
    </g>

    <!-- Node 3: 腾讯元宝/小理AI -->
    <g transform="translate(640, 130)" filter="url(#node-shadow)">
      <rect width="180" height="60" rx="12" fill="#ffffff"/>
      <rect x="0" y="0" width="8" height="60" rx="4" fill="#10b981"/>
      <text x="25" y="26" font-size="16" font-weight="700" fill="#1e293b">腾讯元宝 / 小理AI</text>
      <text x="25" y="46" font-size="12" font-weight="400" fill="#64748b">Prompt调优与实务对齐</text>
    </g>

    <!-- Node 4: 腾讯开悟 -->
    <g transform="translate(80, 350)" filter="url(#node-shadow)">
      <rect width="180" height="60" rx="12" fill="#ffffff"/>
      <rect x="0" y="0" width="8" height="60" rx="4" fill="#f59e0b"/>
      <text x="25" y="26" font-size="16" font-weight="700" fill="#1e293b">腾讯开悟</text>
      <text x="25" y="46" font-size="12" font-weight="400" fill="#64748b">赛事平台与云端工具链</text>
    </g>

    <!-- Node 5: 得理 API -->
    <g transform="translate(640, 350)" filter="url(#node-shadow)">
      <rect width="180" height="60" rx="12" fill="#ffffff"/>
      <rect x="0" y="0" width="8" height="60" rx="4" fill="#ef4444"/>
      <text x="25" y="26" font-size="16" font-weight="700" fill="#1e293b">得理开放平台 API</text>
      <text x="25" y="46" font-size="12" font-weight="400" fill="#64748b">法律原子能力与类案检索</text>
    </g>
  </g>
</svg>"""

    # ==========================================
    # 3. 核心 Prompt 工程架构 (替换《项目简介》表9)
    # ==========================================
    prompt_arch_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="900" height="460" viewBox="0 0 900 460" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="prompt-shadow" x="-2%" y="-5%" width="104%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#0f172a" flood-opacity="0.05"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
    </marker>
  </defs>

  <rect width="900" height="460" fill="#f8fafc" rx="20"/>

  <g font-family="system-ui, -apple-system, sans-serif">
    <text x="450" y="45" font-size="24" font-weight="700" fill="#0f172a" text-anchor="middle" letter-spacing="1">核心 Prompt 工程架构设计</text>
    <text x="450" y="70" font-size="13" font-weight="400" fill="#64748b" text-anchor="middle" letter-spacing="1">CORE PROMPT ENGINEERING ARCHITECTURE</text>

    <!-- Headers -->
    <text x="160" y="110" font-size="14" font-weight="700" fill="#475569" text-anchor="middle">关键输入 (Inputs)</text>
    <text x="450" y="110" font-size="14" font-weight="700" fill="#475569" text-anchor="middle">智能体与职责 (Agents &amp; Roles)</text>
    <text x="740" y="110" font-size="14" font-weight="700" fill="#475569" text-anchor="middle">预期输出 (Outputs)</text>

    <!-- Row 1 -->
    <g transform="translate(40, 130)">
      <rect width="240" height="80" rx="12" fill="#ffffff" filter="url(#prompt-shadow)"/>
      <text x="120" y="35" font-size="14" font-weight="600" fill="#334155" text-anchor="middle">案件摘要 / 当前阶段</text>
      <text x="120" y="55" font-size="13" font-weight="400" fill="#64748b" text-anchor="middle">上轮交互结果 / 争议焦点</text>
      
      <path d="M 250 40 L 290 40" stroke="#cbd5e1" stroke-width="2" marker-end="url(#arrow)"/>
      
      <rect x="300" y="0" width="220" height="80" rx="12" fill="#eff6ff" stroke="#bfdbfe" stroke-width="2"/>
      <text x="410" y="35" font-size="16" font-weight="700" fill="#1e40af" text-anchor="middle">庭审流程交互 Prompt</text>
      <text x="410" y="55" font-size="12" font-weight="400" fill="#3b82f6" text-anchor="middle">生成阶段叙事与策略动作</text>

      <path d="M 530 40 L 570 40" stroke="#cbd5e1" stroke-width="2" marker-end="url(#arrow)"/>

      <rect x="580" y="0" width="240" height="80" rx="12" fill="#ffffff" filter="url(#prompt-shadow)"/>
      <text x="700" y="35" font-size="14" font-weight="600" fill="#059669" text-anchor="middle">场景标题 / 场景描述</text>
      <text x="700" y="55" font-size="13" font-weight="400" fill="#64748b" text-anchor="middle">用户可选行动 / 法官提示</text>
    </g>

    <!-- Row 2 -->
    <g transform="translate(40, 230)">
      <rect width="240" height="80" rx="12" fill="#ffffff" filter="url(#prompt-shadow)"/>
      <text x="120" y="35" font-size="14" font-weight="600" fill="#334155" text-anchor="middle">对方画像 / 当前焦点</text>
      <text x="120" y="55" font-size="13" font-weight="400" fill="#64748b" text-anchor="middle">己方证据状态</text>
      
      <path d="M 250 40 L 290 40" stroke="#cbd5e1" stroke-width="2" marker-end="url(#arrow)"/>
      
      <rect x="300" y="0" width="220" height="80" rx="12" fill="#faf5ff" stroke="#e9d5ff" stroke-width="2"/>
      <text x="410" y="35" font-size="16" font-weight="700" fill="#6b21a8" text-anchor="middle">对方行为模拟 Prompt</text>
      <text x="410" y="55" font-size="12" font-weight="400" fill="#8b5cf6" text-anchor="middle">模拟对手抗辩与质证路径</text>

      <path d="M 530 40 L 570 40" stroke="#cbd5e1" stroke-width="2" marker-end="url(#arrow)"/>

      <rect x="580" y="0" width="240" height="80" rx="12" fill="#ffffff" filter="url(#prompt-shadow)"/>
      <text x="700" y="35" font-size="14" font-weight="600" fill="#059669" text-anchor="middle">抗辩意见 / 质证方向</text>
      <text x="700" y="55" font-size="13" font-weight="400" fill="#64748b" text-anchor="middle">突袭证据 / 程序动作</text>
    </g>

    <!-- Row 3 -->
    <g transform="translate(40, 330)">
      <rect width="240" height="80" rx="12" fill="#ffffff" filter="url(#prompt-shadow)"/>
      <text x="120" y="35" font-size="14" font-weight="600" fill="#334155" text-anchor="middle">全流程模拟记录 / 证据链</text>
      <text x="120" y="55" font-size="13" font-weight="400" fill="#64748b" text-anchor="middle">相关法条与类案</text>
      
      <path d="M 250 40 L 290 40" stroke="#cbd5e1" stroke-width="2" marker-end="url(#arrow)"/>
      
      <rect x="300" y="0" width="220" height="80" rx="12" fill="#fff7ed" stroke="#fed7aa" stroke-width="2"/>
      <text x="410" y="35" font-size="16" font-weight="700" fill="#9a3412" text-anchor="middle">胜诉率分析 Prompt</text>
      <text x="410" y="55" font-size="12" font-weight="400" fill="#f97316" text-anchor="middle">基于全流程输出胜算评估</text>

      <path d="M 530 40 L 570 40" stroke="#cbd5e1" stroke-width="2" marker-end="url(#arrow)"/>

      <rect x="580" y="0" width="240" height="80" rx="12" fill="#ffffff" filter="url(#prompt-shadow)"/>
      <text x="700" y="35" font-size="14" font-weight="600" fill="#059669" text-anchor="middle">分维度胜算判断 / 风险点</text>
      <text x="700" y="55" font-size="13" font-weight="400" fill="#64748b" text-anchor="middle">证据缺口 / 下一步建议</text>
    </g>
  </g>
</svg>"""

    create_svg(os.path.join(out_dir, "user_personas.svg"), user_personas_svg)
    create_svg(os.path.join(out_dir, "ai_toolchain.svg"), ai_toolchain_svg)
    create_svg(os.path.join(out_dir, "prompt_architecture.svg"), prompt_arch_svg)

if __name__ == "__main__":
    main()
