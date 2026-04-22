import os

def create_svg(filename, content):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 成功生成高质量 SVG: {filename}")

def main():
    out_dir = r"E:\lawai\output\doc\diagrams"
    os.makedirs(out_dir, exist_ok=True)

    # ==========================================
    # 1. System Architecture SVG
    # ==========================================
    sys_arch_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="840" height="700" viewBox="0 0 840 700" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Definitions for gradients and shadows -->
  <defs>
    <filter id="shadow-sm" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#0f172a" flood-opacity="0.06"/>
    </filter>
    <filter id="shadow-md" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="16" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
    <filter id="shadow-lg" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="12" stdDeviation="24" flood-color="#0f172a" flood-opacity="0.1"/>
    </filter>

    <linearGradient id="grad-layer-1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#eff6ff" />
      <stop offset="100%" stop-color="#dbeafe" />
    </linearGradient>
    <linearGradient id="grad-layer-2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f0fdf4" />
      <stop offset="100%" stop-color="#dcfce7" />
    </linearGradient>
    <linearGradient id="grad-layer-3" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#faf5ff" />
      <stop offset="100%" stop-color="#f3e8ff" />
    </linearGradient>
    <linearGradient id="grad-layer-4" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fff7ed" />
      <stop offset="100%" stop-color="#ffedd5" />
    </linearGradient>

    <linearGradient id="grad-block-blue" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3b82f6" />
      <stop offset="100%" stop-color="#2563eb" />
    </linearGradient>
    <linearGradient id="grad-block-purple" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8b5cf6" />
      <stop offset="100%" stop-color="#7c3aed" />
    </linearGradient>
    <linearGradient id="grad-block-indigo" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6366f1" />
      <stop offset="100%" stop-color="#4f46e5" />
    </linearGradient>
  </defs>

  <!-- Global Background -->
  <rect width="840" height="700" fill="#f8fafc" rx="24"/>

  <g font-family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'">
    
    <!-- Title -->
    <text x="420" y="50" font-size="28" font-weight="700" fill="#0f172a" text-anchor="middle" letter-spacing="2">企鹅法庭 - 核心系统架构</text>
    <text x="420" y="80" font-size="14" font-weight="400" fill="#64748b" text-anchor="middle" letter-spacing="1">PENGUIN COURT - CORE ARCHITECTURE</text>

    <!-- LAYER 1: 表现层 -->
    <g transform="translate(40, 110)">
      <!-- Layer Container -->
      <rect width="760" height="110" rx="16" fill="url(#grad-layer-1)" filter="url(#shadow-sm)"/>
      <rect width="760" height="110" rx="16" fill="none" stroke="#bfdbfe" stroke-width="2"/>
      <text x="30" y="60" font-size="18" font-weight="600" fill="#1e3a8a" transform="rotate(-90 30,60)">表现层</text>
      
      <!-- Blocks -->
      <g transform="translate(90, 25)">
        <rect width="310" height="60" rx="12" fill="#ffffff" filter="url(#shadow-sm)"/>
        <text x="155" y="36" font-size="16" font-weight="600" fill="#334155" text-anchor="middle">Web 交互端 (React/Vue)</text>
      </g>
      <g transform="translate(420, 25)">
        <rect width="310" height="60" rx="12" fill="#ffffff" filter="url(#shadow-sm)"/>
        <text x="155" y="36" font-size="16" font-weight="600" fill="#334155" text-anchor="middle">微信小程序端</text>
      </g>
    </g>

    <!-- Connecting Arrows 1 -> 2 -->
    <path d="M 420 220 L 420 240" stroke="#cbd5e1" stroke-width="3" stroke-dasharray="6,6" marker-end="url(#arrow)"/>

    <!-- LAYER 2: 接入与路由层 -->
    <g transform="translate(40, 250)">
      <rect width="760" height="110" rx="16" fill="url(#grad-layer-2)" filter="url(#shadow-sm)"/>
      <rect width="760" height="110" rx="16" fill="none" stroke="#bbf7d0" stroke-width="2"/>
      <text x="30" y="70" font-size="18" font-weight="600" fill="#166534" transform="rotate(-90 30,70)">接入层</text>

      <g transform="translate(90, 25)">
        <rect width="200" height="60" rx="12" fill="#ffffff" filter="url(#shadow-sm)"/>
        <text x="100" y="36" font-size="16" font-weight="600" fill="#334155" text-anchor="middle">FastAPI 路由网关</text>
      </g>
      <g transform="translate(310, 25)">
        <rect width="200" height="60" rx="12" fill="#ffffff" filter="url(#shadow-sm)"/>
        <text x="100" y="36" font-size="16" font-weight="600" fill="#334155" text-anchor="middle">WebSocket 实时流</text>
      </g>
      <g transform="translate(530, 25)">
        <rect width="200" height="60" rx="12" fill="#ffffff" filter="url(#shadow-sm)"/>
        <text x="100" y="36" font-size="16" font-weight="600" fill="#334155" text-anchor="middle">权限与会话管理</text>
      </g>
    </g>

    <!-- Connecting Arrows 2 -> 3 -->
    <path d="M 420 360 L 420 380" stroke="#cbd5e1" stroke-width="3" stroke-dasharray="6,6"/>

    <!-- LAYER 3: 核心逻辑层 -->
    <g transform="translate(40, 390)">
      <rect width="760" height="150" rx="16" fill="url(#grad-layer-3)" filter="url(#shadow-sm)"/>
      <rect width="760" height="150" rx="16" fill="none" stroke="#e9d5ff" stroke-width="2"/>
      <text x="30" y="95" font-size="18" font-weight="600" fill="#581c87" transform="rotate(-90 30,95)">核心逻辑层</text>

      <g transform="translate(90, 25)">
        <rect width="310" height="100" rx="16" fill="url(#grad-block-indigo)" filter="url(#shadow-md)"/>
        <text x="155" y="45" font-size="18" font-weight="700" fill="#ffffff" text-anchor="middle">庭审工作流引擎</text>
        <text x="155" y="75" font-size="14" font-weight="400" fill="#e0e7ff" text-anchor="middle">Trial Workflow Engine</text>
      </g>

      <g transform="translate(420, 25)">
        <rect width="145" height="100" rx="16" fill="url(#grad-block-purple)" filter="url(#shadow-md)"/>
        <text x="72.5" y="45" font-size="16" font-weight="700" fill="#ffffff" text-anchor="middle">Agent 调度</text>
        <text x="72.5" y="75" font-size="13" font-weight="400" fill="#ede9fe" text-anchor="middle">Orchestration</text>
      </g>

      <g transform="translate(585, 25)">
        <rect width="145" height="100" rx="16" fill="url(#grad-block-blue)" filter="url(#shadow-md)"/>
        <text x="72.5" y="45" font-size="16" font-weight="700" fill="#ffffff" text-anchor="middle">检索增强 RAG</text>
        <text x="72.5" y="75" font-size="13" font-weight="400" fill="#dbeafe" text-anchor="middle">Knowledge Base</text>
      </g>
    </g>

    <!-- Connecting Arrows 3 -> 4 -->
    <path d="M 420 540 L 420 560" stroke="#cbd5e1" stroke-width="3" stroke-dasharray="6,6"/>

    <!-- LAYER 4: 数据与基座层 -->
    <g transform="translate(40, 570)">
      <rect width="760" height="100" rx="16" fill="url(#grad-layer-4)" filter="url(#shadow-sm)"/>
      <rect width="760" height="100" rx="16" fill="none" stroke="#fed7aa" stroke-width="2"/>
      <text x="30" y="65" font-size="18" font-weight="600" fill="#9a3412" transform="rotate(-90 30,65)">数据与模型基座</text>

      <g transform="translate(90, 20)">
        <rect width="200" height="60" rx="12" fill="#ffffff" filter="url(#shadow-sm)"/>
        <text x="100" y="36" font-size="16" font-weight="600" fill="#334155" text-anchor="middle">CodeBuddy LLM</text>
      </g>
      <g transform="translate(310, 20)">
        <rect width="200" height="60" rx="12" fill="#ffffff" filter="url(#shadow-sm)"/>
        <text x="100" y="36" font-size="16" font-weight="600" fill="#334155" text-anchor="middle">向量数据库 (Milvus/FAISS)</text>
      </g>
      <g transform="translate(530, 20)">
        <rect width="200" height="60" rx="12" fill="#ffffff" filter="url(#shadow-sm)"/>
        <text x="100" y="36" font-size="16" font-weight="600" fill="#334155" text-anchor="middle">关系型数据库 (PostgreSQL)</text>
      </g>
    </g>
  </g>
</svg>"""

    # ==========================================
    # 2. Core Workflow SVG
    # ==========================================
    core_workflow_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="1000" height="360" viewBox="0 0 1000 360" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="shadow-flow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="6" stdDeviation="12" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
    
    <!-- Arrows definition -->
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
    </marker>

    <!-- Node Gradients -->
    <linearGradient id="grad-n1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3b82f6" />
      <stop offset="100%" stop-color="#2563eb" />
    </linearGradient>
    <linearGradient id="grad-n2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0ea5e9" />
      <stop offset="100%" stop-color="#0284c7" />
    </linearGradient>
    <linearGradient id="grad-n3" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8b5cf6" />
      <stop offset="100%" stop-color="#7c3aed" />
    </linearGradient>
    <linearGradient id="grad-n4" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f59e0b" />
      <stop offset="100%" stop-color="#d97706" />
    </linearGradient>
    <linearGradient id="grad-n5" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10b981" />
      <stop offset="100%" stop-color="#059669" />
    </linearGradient>
  </defs>

  <rect width="1000" height="360" fill="#f8fafc" rx="24"/>

  <g font-family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'">
    
    <!-- Title -->
    <text x="500" y="50" font-size="26" font-weight="700" fill="#0f172a" text-anchor="middle" letter-spacing="1">企鹅法庭 - 核心业务流转图</text>
    <text x="500" y="80" font-size="14" font-weight="400" fill="#64748b" text-anchor="middle" letter-spacing="1">CORE BUSINESS WORKFLOW</text>

    <!-- Node 1 -->
    <g transform="translate(40, 140)">
      <rect width="140" height="120" rx="16" fill="url(#grad-n1)" filter="url(#shadow-flow)"/>
      <circle cx="70" cy="40" r="16" fill="#ffffff" fill-opacity="0.2"/>
      <text x="70" y="46" font-size="16" font-weight="700" fill="#ffffff" text-anchor="middle">1</text>
      <text x="70" y="85" font-size="18" font-weight="600" fill="#ffffff" text-anchor="middle">案件资料导入</text>
      <text x="70" y="105" font-size="12" font-weight="400" fill="#e0e7ff" text-anchor="middle">OCR / Docx 解析</text>
    </g>

    <path d="M 180 200 L 220 200" stroke="#cbd5e1" stroke-width="4" marker-end="url(#arrow)"/>

    <!-- Node 2 -->
    <g transform="translate(230, 140)">
      <rect width="140" height="120" rx="16" fill="url(#grad-n2)" filter="url(#shadow-flow)"/>
      <circle cx="70" cy="40" r="16" fill="#ffffff" fill-opacity="0.2"/>
      <text x="70" y="46" font-size="16" font-weight="700" fill="#ffffff" text-anchor="middle">2</text>
      <text x="70" y="85" font-size="18" font-weight="600" fill="#ffffff" text-anchor="middle">争议焦点归纳</text>
      <text x="70" y="105" font-size="12" font-weight="400" fill="#e0e7ff" text-anchor="middle">大模型智能总结</text>
    </g>

    <path d="M 370 200 L 410 200" stroke="#cbd5e1" stroke-width="4" marker-end="url(#arrow)"/>

    <!-- Node 3 -->
    <g transform="translate(420, 120)">
      <rect width="180" height="160" rx="20" fill="url(#grad-n3)" filter="url(#shadow-flow)"/>
      <circle cx="90" cy="45" r="20" fill="#ffffff" fill-opacity="0.2"/>
      <text x="90" y="52" font-size="18" font-weight="700" fill="#ffffff" text-anchor="middle">3</text>
      <text x="90" y="95" font-size="20" font-weight="700" fill="#ffffff" text-anchor="middle">智能庭审推演</text>
      <text x="90" y="120" font-size="13" font-weight="400" fill="#ede9fe" text-anchor="middle">多 Agent 角色扮演</text>
      <text x="90" y="140" font-size="13" font-weight="400" fill="#ede9fe" text-anchor="middle">法官 / 原告 / 被告</text>
    </g>

    <path d="M 600 200 L 640 200" stroke="#cbd5e1" stroke-width="4" marker-end="url(#arrow)"/>

    <!-- Node 4 -->
    <g transform="translate(650, 140)">
      <rect width="140" height="120" rx="16" fill="url(#grad-n4)" filter="url(#shadow-flow)"/>
      <circle cx="70" cy="40" r="16" fill="#ffffff" fill-opacity="0.2"/>
      <text x="70" y="46" font-size="16" font-weight="700" fill="#ffffff" text-anchor="middle">4</text>
      <text x="70" y="85" font-size="18" font-weight="600" fill="#ffffff" text-anchor="middle">结果复盘与反馈</text>
      <text x="70" y="105" font-size="12" font-weight="400" fill="#ffedd5" text-anchor="middle">逻辑漏洞与建议</text>
    </g>

    <path d="M 790 200 L 830 200" stroke="#cbd5e1" stroke-width="4" marker-end="url(#arrow)"/>

    <!-- Node 5 -->
    <g transform="translate(840, 140)">
      <rect width="120" height="120" rx="16" fill="url(#grad-n5)" filter="url(#shadow-flow)"/>
      <circle cx="60" cy="40" r="16" fill="#ffffff" fill-opacity="0.2"/>
      <text x="60" y="46" font-size="16" font-weight="700" fill="#ffffff" text-anchor="middle">5</text>
      <text x="60" y="85" font-size="18" font-weight="600" fill="#ffffff" text-anchor="middle">诉状生成</text>
      <text x="60" y="105" font-size="12" font-weight="400" fill="#d1fae5" text-anchor="middle">一键导出文书</text>
    </g>

    <!-- Decorative background path representing data flow -->
    <path d="M 110 260 C 200 320, 800 320, 900 260" fill="none" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="4,8" opacity="0.5"/>
  </g>
</svg>"""

    create_svg(os.path.join(out_dir, "system_architecture.svg"), sys_arch_svg)
    create_svg(os.path.join(out_dir, "core_workflow.svg"), core_workflow_svg)

if __name__ == "__main__":
    main()
