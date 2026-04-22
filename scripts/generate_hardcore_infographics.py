import os

def create_svg(filename, content):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 成功生成高阶技术信息图 SVG (真实代码核对版): {filename}")

def main():
    out_dir = r"E:\lawai\output\doc\diagrams\infographics"
    os.makedirs(out_dir, exist_ok=True)

    # ==========================================
    # 1. 真实技术栈生态矩阵 (Tech Stack Matrix)
    # 依据实际代码：React/Vite/TS, FastAPI/SQLite, 元器/CodeBuddy/得理/智谱, Render部署
    # ==========================================
    tech_stack_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="960" height="480" viewBox="0 0 960 480" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="box-shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="6" stdDeviation="12" flood-color="#0f172a" flood-opacity="0.06"/>
    </filter>
    <linearGradient id="grad-front" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="100%" stop-color="#0284c7" />
    </linearGradient>
    <linearGradient id="grad-back" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#a78bfa" />
      <stop offset="100%" stop-color="#7c3aed" />
    </linearGradient>
    <linearGradient id="grad-ai" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fb923c" />
      <stop offset="100%" stop-color="#ea580c" />
    </linearGradient>
    <linearGradient id="grad-data" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#34d399" />
      <stop offset="100%" stop-color="#059669" />
    </linearGradient>
    <linearGradient id="grad-core" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e40af" />
      <stop offset="100%" stop-color="#1e3a8a" />
    </linearGradient>
  </defs>

  <rect width="960" height="480" fill="#f8fafc" rx="20"/>

  <g font-family="system-ui, -apple-system, sans-serif">
    <text x="480" y="50" font-size="28" font-weight="700" fill="#0f172a" text-anchor="middle" letter-spacing="1">全栈技术架构与生态矩阵</text>
    <text x="480" y="80" font-size="14" font-weight="400" fill="#64748b" text-anchor="middle" letter-spacing="2">FULL-STACK TECHNOLOGY &amp; ECOSYSTEM</text>

    <!-- (Central node and its connections removed) -->

    <!-- Column 1: 前端表现层 -->
    <g transform="translate(40, 130)">
      <rect width="200" height="300" rx="16" fill="#ffffff" filter="url(#box-shadow)"/>
      <path d="M0 16 Q0 0 16 0 L184 0 Q200 0 200 16 L200 50 L0 50 Z" fill="url(#grad-front)"/>
      <text x="100" y="32" font-size="18" font-weight="700" fill="#ffffff" text-anchor="middle">前端表现层</text>
      
      <rect x="20" y="80" width="160" height="40" rx="8" fill="#f0f9ff" stroke="#bae6fd" stroke-width="1"/>
      <text x="100" y="105" font-size="14" font-weight="600" fill="#0369a1" text-anchor="middle">React 18</text>
      
      <rect x="20" y="135" width="160" height="40" rx="8" fill="#f0f9ff" stroke="#bae6fd" stroke-width="1"/>
      <text x="100" y="160" font-size="14" font-weight="600" fill="#0369a1" text-anchor="middle">Vite 构建工具</text>
      
      <rect x="20" y="190" width="160" height="40" rx="8" fill="#f0f9ff" stroke="#bae6fd" stroke-width="1"/>
      <text x="100" y="215" font-size="14" font-weight="600" fill="#0369a1" text-anchor="middle">TypeScript 强类型</text>
      
      <rect x="20" y="245" width="160" height="40" rx="8" fill="#f0f9ff" stroke="#bae6fd" stroke-width="1"/>
      <text x="100" y="270" font-size="14" font-weight="600" fill="#0369a1" text-anchor="middle">Vanilla CSS 模块</text>
    </g>

    <!-- Column 2: 后端逻辑层 -->
    <g transform="translate(265, 130)">
      <rect width="200" height="300" rx="16" fill="#ffffff" filter="url(#box-shadow)"/>
      <path d="M0 16 Q0 0 16 0 L184 0 Q200 0 200 16 L200 50 L0 50 Z" fill="url(#grad-back)"/>
      <text x="100" y="32" font-size="18" font-weight="700" fill="#ffffff" text-anchor="middle">后端逻辑层</text>
      
      <rect x="20" y="80" width="160" height="40" rx="8" fill="#f5f3ff" stroke="#ddd6fe" stroke-width="1"/>
      <text x="100" y="105" font-size="14" font-weight="600" fill="#6d28d9" text-anchor="middle">FastAPI 框架</text>
      
      <rect x="20" y="135" width="160" height="40" rx="8" fill="#f5f3ff" stroke="#ddd6fe" stroke-width="1"/>
      <text x="100" y="160" font-size="14" font-weight="600" fill="#6d28d9" text-anchor="middle">Pydantic 数据验证</text>
      
      <rect x="20" y="190" width="160" height="40" rx="8" fill="#f5f3ff" stroke="#ddd6fe" stroke-width="1"/>
      <text x="100" y="215" font-size="14" font-weight="600" fill="#6d28d9" text-anchor="middle">庭审状态机引擎</text>
      
      <rect x="20" y="245" width="160" height="40" rx="8" fill="#f5f3ff" stroke="#ddd6fe" stroke-width="1"/>
      <text x="100" y="270" font-size="14" font-weight="600" fill="#6d28d9" text-anchor="middle">RESTful API</text>
    </g>

    <!-- Column 3: AI 大模型基座 -->
    <g transform="translate(490, 130)">
      <rect width="200" height="300" rx="16" fill="#ffffff" filter="url(#box-shadow)"/>
      <path d="M0 16 Q0 0 16 0 L184 0 Q200 0 200 16 L200 50 L0 50 Z" fill="url(#grad-ai)"/>
      <text x="100" y="32" font-size="18" font-weight="700" fill="#ffffff" text-anchor="middle">AI 模型与工作流</text>
      
      <rect x="20" y="80" width="160" height="40" rx="8" fill="#fff7ed" stroke="#fed7aa" stroke-width="1"/>
      <text x="100" y="105" font-size="14" font-weight="600" fill="#c2410c" text-anchor="middle">CodeBuddy LLM</text>
      
      <rect x="20" y="135" width="160" height="40" rx="8" fill="#fff7ed" stroke="#fed7aa" stroke-width="1"/>
      <text x="100" y="160" font-size="14" font-weight="600" fill="#c2410c" text-anchor="middle">腾讯元器工作流</text>
      
      <rect x="20" y="190" width="160" height="40" rx="8" fill="#fff7ed" stroke="#fed7aa" stroke-width="1"/>
      <text x="100" y="215" font-size="14" font-weight="600" fill="#c2410c" text-anchor="middle">得理 API 检索</text>
      
      <rect x="20" y="245" width="160" height="40" rx="8" fill="#fff7ed" stroke="#fed7aa" stroke-width="1"/>
      <text x="100" y="270" font-size="14" font-weight="600" fill="#c2410c" text-anchor="middle">智谱 AI</text>
    </g>

    <!-- Column 4: 数据层与基座 -->
    <g transform="translate(715, 130)">
      <rect width="200" height="300" rx="16" fill="#ffffff" filter="url(#box-shadow)"/>
      <path d="M0 16 Q0 0 16 0 L184 0 Q200 0 200 16 L200 50 L0 50 Z" fill="url(#grad-data)"/>
      <text x="100" y="32" font-size="18" font-weight="700" fill="#ffffff" text-anchor="middle">数据层与基座</text>
      
      <rect x="20" y="80" width="160" height="40" rx="8" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1"/>
      <text x="100" y="105" font-size="14" font-weight="600" fill="#047857" text-anchor="middle">SQLite 轻量级库</text>
      
      <rect x="20" y="135" width="160" height="40" rx="8" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1"/>
      <text x="100" y="160" font-size="14" font-weight="600" fill="#047857" text-anchor="middle">本地案卷材料</text>
      
      <rect x="20" y="190" width="160" height="40" rx="8" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1"/>
      <text x="100" y="215" font-size="14" font-weight="600" fill="#047857" text-anchor="middle">Docker 容器化</text>
      
      <rect x="20" y="245" width="160" height="40" rx="8" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1"/>
      <text x="100" y="270" font-size="14" font-weight="600" fill="#047857" text-anchor="middle">Render 云部署</text>
    </g>
  </g>
</svg>"""

    # ==========================================
    # 2. 真实庭审状态机 (Trial State Machine)
    # 依据实际代码 TrialStage: PREPARE, INVESTIGATION, DEBATE, MEDIATION_OR_JUDGMENT, FINAL_STATEMENT, REPORT_READY
    # ==========================================
    state_machine_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="1000" height="520" viewBox="0 0 1000 520" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="state-shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
    <marker id="arrow-sm" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
    </marker>
    <linearGradient id="grad-state" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4f46e5" />
      <stop offset="100%" stop-color="#3730a3" />
    </linearGradient>
  </defs>

  <rect width="1000" height="520" fill="#f8fafc" rx="20"/>

  <g font-family="system-ui, -apple-system, sans-serif">
    <text x="500" y="50" font-size="26" font-weight="700" fill="#0f172a" text-anchor="middle" letter-spacing="1">庭审核心状态机引擎 (Trial State Machine)</text>
    <text x="500" y="80" font-size="14" font-weight="400" fill="#64748b" text-anchor="middle" letter-spacing="2">TRIAL WORKFLOW STATE TRANSITIONS</text>

    <!-- Grid / Background Areas -->
    <rect x="40" y="120" width="180" height="340" rx="12" fill="#eff6ff" stroke="#bfdbfe" stroke-dasharray="4,4"/>
    <text x="130" y="150" font-size="16" font-weight="700" fill="#1e40af" text-anchor="middle">开庭准备</text>

    <rect x="240" y="120" width="500" height="340" rx="12" fill="#faf5ff" stroke="#e9d5ff" stroke-dasharray="4,4"/>
    <text x="490" y="150" font-size="16" font-weight="700" fill="#6b21a8" text-anchor="middle">庭审核心循环 (Trial Loop)</text>

    <rect x="760" y="120" width="200" height="340" rx="12" fill="#f0fdf4" stroke="#bbf7d0" stroke-dasharray="4,4"/>
    <text x="860" y="150" font-size="16" font-weight="700" fill="#166534" text-anchor="middle">裁判与复盘</text>

    <!-- State 1: PREPARE -->
    <g transform="translate(70, 200)" filter="url(#state-shadow)">
      <rect width="120" height="60" rx="12" fill="#ffffff" stroke="#3b82f6" stroke-width="2"/>
      <text x="60" y="28" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">PREPARE</text>
      <text x="60" y="46" font-size="12" font-weight="400" fill="#64748b" text-anchor="middle">争点与边界确认</text>
    </g>

    <!-- State 2: INVESTIGATION -->
    <g transform="translate(270, 200)" filter="url(#state-shadow)">
      <rect width="140" height="60" rx="12" fill="#ffffff" stroke="#8b5cf6" stroke-width="2"/>
      <text x="70" y="28" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">INVESTIGATION</text>
      <text x="70" y="46" font-size="12" font-weight="400" fill="#64748b" text-anchor="middle">法庭调查与举证</text>
    </g>

    <!-- State 3: DEBATE -->
    <g transform="translate(570, 200)" filter="url(#state-shadow)">
      <rect width="140" height="60" rx="12" fill="#ffffff" stroke="#8b5cf6" stroke-width="2"/>
      <text x="70" y="28" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">DEBATE</text>
      <text x="70" y="46" font-size="12" font-weight="400" fill="#64748b" text-anchor="middle">法庭辩论阶段</text>
    </g>

    <!-- State 4: FINAL_STATEMENT -->
    <g transform="translate(420, 320)" filter="url(#state-shadow)">
      <rect width="160" height="60" rx="12" fill="url(#grad-state)"/>
      <text x="80" y="28" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">FINAL_STATEMENT</text>
      <text x="80" y="46" font-size="12" font-weight="400" fill="#c7d2fe" text-anchor="middle">最后陈述与补充</text>
    </g>

    <!-- State 5: MEDIATION_OR_JUDGMENT -->
    <g transform="translate(800, 200)" filter="url(#state-shadow)">
      <rect width="150" height="60" rx="12" fill="#ffffff" stroke="#10b981" stroke-width="2"/>
      <text x="75" y="28" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">MEDIATION / JUDGMENT</text>
      <text x="75" y="46" font-size="12" font-weight="400" fill="#64748b" text-anchor="middle">调解与判决</text>
    </g>

    <!-- State 6: REPORT_READY -->
    <g transform="translate(800, 320)" filter="url(#state-shadow)">
      <rect width="150" height="60" rx="12" fill="#ffffff" stroke="#10b981" stroke-width="2"/>
      <text x="75" y="28" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">REPORT_READY</text>
      <text x="75" y="46" font-size="12" font-weight="400" fill="#64748b" text-anchor="middle">生成复盘报告</text>
    </g>

    <!-- Connections / Arrows -->
    <!-- PREPARE to INVESTIGATION -->
    <path d="M 190 230 L 260 230" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrow-sm)"/>
    
    <!-- INVESTIGATION to DEBATE -->
    <path d="M 410 230 L 560 230" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrow-sm)"/>
    
    <!-- DEBATE to FINAL_STATEMENT -->
    <path d="M 640 260 C 640 300, 560 300, 560 320" stroke="#94a3b8" stroke-width="2" fill="none" marker-end="url(#arrow-sm)"/>

    <!-- FINAL_STATEMENT to INVESTIGATION (Loopback / Supplement) -->
    <path d="M 420 350 C 340 350, 340 270, 340 260" stroke="#8b5cf6" stroke-width="2" stroke-dasharray="4,4" fill="none" marker-end="url(#arrow-sm)"/>
    <text x="360" y="310" font-size="12" fill="#8b5cf6" font-weight="600">质证触发/多轮循环</text>

    <!-- DEBATE to MEDIATION_OR_JUDGMENT -->
    <path d="M 710 230 L 790 230" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrow-sm)"/>

    <!-- MEDIATION_OR_JUDGMENT to REPORT_READY -->
    <path d="M 875 260 L 875 310" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrow-sm)"/>

  </g>
</svg>"""

    # ==========================================
    # 3. 真实外部 API 链路 (RAG Pipeline 替代版)
    # 依据实际代码：调用腾讯元器、得理API检索、智谱、CodeBuddy
    # ==========================================
    rag_pipeline_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="960" height="420" viewBox="0 0 960 420" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="rag-shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
    <marker id="arrow-rag" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6" />
    </marker>
    <linearGradient id="grad-db" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0ea5e9" />
      <stop offset="100%" stop-color="#0369a1" />
    </linearGradient>
  </defs>

  <rect width="960" height="420" fill="#f8fafc" rx="20"/>

  <g font-family="system-ui, -apple-system, sans-serif">
    <text x="480" y="40" font-size="24" font-weight="700" fill="#0f172a" text-anchor="middle" letter-spacing="1">多模型调度与知识检索链路 (Multi-Agent Pipeline)</text>
    <text x="480" y="65" font-size="13" font-weight="400" fill="#64748b" text-anchor="middle" letter-spacing="2">LLM ROUTING &amp; KNOWLEDGE RETRIEVAL</text>

    <!-- Context Store (Left) -->
    <rect x="40" y="100" width="240" height="260" rx="12" fill="#eff6ff" stroke="#bfdbfe" stroke-dasharray="4,4"/>
    <text x="160" y="130" font-size="14" font-weight="700" fill="#1e40af" text-anchor="middle">上下文与状态注入</text>

    <g transform="translate(90, 160)" filter="url(#rag-shadow)">
      <rect width="140" height="60" rx="8" fill="#ffffff" stroke="#cbd5e1"/>
      <text x="70" y="28" font-size="14" font-weight="600" fill="#334155" text-anchor="middle">本地案卷与设定</text>
      <text x="70" y="46" font-size="12" font-weight="400" fill="#64748b" text-anchor="middle">JSON/Markdown</text>
    </g>

    <g transform="translate(90, 260)" filter="url(#rag-shadow)">
      <rect width="140" height="60" rx="8" fill="#ffffff" stroke="#cbd5e1"/>
      <text x="70" y="28" font-size="14" font-weight="600" fill="#334155" text-anchor="middle">庭审历史记录</text>
      <text x="70" y="46" font-size="12" font-weight="400" fill="#64748b" text-anchor="middle">SQLite 实时状态</text>
    </g>

    <!-- Deli API (Top Center) -->
    <g transform="translate(380, 110)" filter="url(#rag-shadow)">
      <rect width="140" height="60" rx="8" fill="#f59e0b"/>
      <text x="70" y="28" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">得理 API</text>
      <text x="70" y="46" font-size="12" font-weight="400" fill="#fffbeb" text-anchor="middle">法条/类案检索</text>
    </g>

    <!-- Orchestrator (Center) -->
    <g transform="translate(380, 220)" filter="url(#rag-shadow)">
      <rect width="140" height="100" rx="16" fill="url(#grad-db)"/>
      <path d="M 20 30 C 20 15, 120 15, 120 30 C 120 45, 20 45, 20 30" fill="#bae6fd" opacity="0.3"/>
      <text x="70" y="55" font-size="18" font-weight="700" fill="#ffffff" text-anchor="middle">后台调度器</text>
      <text x="70" y="75" font-size="12" font-weight="400" fill="#e0f2fe" text-anchor="middle">FastAPI</text>
    </g>

    <!-- Arrows into Orchestrator -->
    <path d="M 230 190 C 300 190, 300 270, 370 270" stroke="#3b82f6" stroke-width="2" fill="none" marker-end="url(#arrow-rag)"/>
    <path d="M 230 290 C 300 290, 300 270, 370 270" stroke="#3b82f6" stroke-width="2" fill="none" marker-end="url(#arrow-rag)"/>
    <path d="M 450 170 L 450 210" stroke="#3b82f6" stroke-width="2" marker-end="url(#arrow-rag)"/>

    <!-- Online Retrieval (Right) -->
    <rect x="600" y="100" width="320" height="260" rx="12" fill="#faf5ff" stroke="#e9d5ff" stroke-dasharray="4,4"/>
    <text x="760" y="130" font-size="14" font-weight="700" fill="#6b21a8" text-anchor="middle">多模型 Agent 生成层</text>

    <!-- Yuanqi / Zhipu -->
    <g transform="translate(630, 160)" filter="url(#rag-shadow)">
      <rect width="120" height="60" rx="8" fill="#ffffff" stroke="#cbd5e1"/>
      <text x="60" y="28" font-size="14" font-weight="600" fill="#334155" text-anchor="middle">腾讯元器</text>
      <text x="60" y="46" font-size="12" font-weight="400" fill="#64748b" text-anchor="middle">Agent工作流</text>
    </g>

    <g transform="translate(630, 260)" filter="url(#rag-shadow)">
      <rect width="120" height="60" rx="8" fill="#ffffff" stroke="#cbd5e1"/>
      <text x="60" y="28" font-size="14" font-weight="600" fill="#334155" text-anchor="middle">智谱 AI</text>
      <text x="60" y="46" font-size="12" font-weight="400" fill="#64748b" text-anchor="middle">辅助生成</text>
    </g>

    <!-- LLM Node -->
    <g transform="translate(780, 210)" filter="url(#rag-shadow)">
      <rect width="120" height="60" rx="8" fill="#8b5cf6"/>
      <text x="60" y="28" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">CodeBuddy</text>
      <text x="60" y="46" font-size="12" font-weight="400" fill="#ede9fe" text-anchor="middle">底层基座模型</text>
    </g>

    <!-- Arrows from Orchestrator out -->
    <path d="M 520 270 C 570 270, 570 190, 620 190" stroke="#3b82f6" stroke-width="2" fill="none" marker-end="url(#arrow-rag)"/>
    <path d="M 520 270 C 570 270, 570 290, 620 290" stroke="#3b82f6" stroke-width="2" fill="none" marker-end="url(#arrow-rag)"/>
    
    <!-- Arrows to CodeBuddy -->
    <path d="M 750 190 C 765 190, 765 240, 770 240" stroke="#10b981" stroke-width="2" stroke-dasharray="4,4" fill="none" marker-end="url(#arrow-rag)"/>
    <path d="M 750 290 C 765 290, 765 240, 770 240" stroke="#10b981" stroke-width="2" stroke-dasharray="4,4" fill="none" marker-end="url(#arrow-rag)"/>
  </g>
</svg>"""

    create_svg(os.path.join(out_dir, "tech_stack.svg"), tech_stack_svg)
    create_svg(os.path.join(out_dir, "state_machine.svg"), state_machine_svg)
    create_svg(os.path.join(out_dir, "rag_pipeline.svg"), rag_pipeline_svg)

if __name__ == "__main__":
    main()
