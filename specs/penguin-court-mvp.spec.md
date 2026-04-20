# Feature: 企鹅法庭 MVP 技术蓝图与实施计划

## Overview
`企鹅法庭` 的 MVP 不是一个泛化“法律问答机器人”，而是一个可演示、可交互、可复盘的 `庭审模拟系统`。它要在 15 天内完成一个足够稳定、足够新颖、足够像产品的 Demo：用户输入案件信息后，系统以企鹅职业角色驱动完整庭审流程，用分支剧情模拟法官、对方律师、证人、调解节点和突发证据，并生成胜诉率分析与诉前准备报告。

我们的技术目标不是追求“大而全”，而是交付一个 `主链路闭环完整、输出具体、交互新颖、现场可稳演示` 的作品。换句话说，系统必须优先保证：

- 输入是结构化的，不靠用户长篇自由发挥；
- 过程是可编排的，不让模型胡乱发散；
- 输出是可解释的，不只给一句模糊建议；
- 演示是稳定的，不因为接口、上下文、提示词失控而翻车。

## Project Goal
在 `2026-04-07` 到 `2026-04-21` 内，完成一套可运行的庭审模拟 MVP，满足以下交付标准：

- 支持至少 2 类高频民事案件进入完整流程
- 支持“案件录入 -> 庭审互动 -> 分支推进 -> 结果报告”的闭环
- 支持 3 组可直接演示的标准 demo 案例
- 输出《庭审模拟复盘报告》和《庭前备战清单》
- 能够在比赛展示时以稳定剧本完成 5 到 8 分钟核心演示

## Success Metrics

### Demo Success
- 评委可在 1 分钟内理解项目区别于普通法律问答产品的创新点
- 主演示链路在单机环境下成功率 >= 95%
- 任一演示案例从录入到出报告总耗时 <= 90 秒

### Product Success
- 用户可以感受到明确的“庭审阶段推进”
- 每一轮互动都有可点击的策略分支，而不是纯聊天
- 报告能指出风险点、证据不足、建议动作，而不只是结论

### Technical Success
- 后端所有关键步骤都能返回结构化 JSON
- 模型输出经过解析和兜底，不直接裸渲染
- 法律引用和类案参考可以在报告中体现出处类别

## In Scope

### P0: 必须交付
- 民事案件支持至少 2 类：
  - 民间借贷
  - 劳动争议
- 案件信息录入页面
- 企鹅角色驱动的庭审模拟页面
- 状态机驱动的庭审分支推进
- 对方策略/证据/质证意见模拟
- 胜诉率多维度打分
- 庭审复盘报告生成
- 庭前备战清单生成
- 3 组预置 demo 案例
- 单机演示部署方案

### P1: 有余力再做
- 第 3、第 4 类案件支持：
  - 离婚纠纷
  - 侵权责任
- 报告导出 PDF
- 更丰富的角色立绘/主题 UI
- 类案引用结果可展开

### P2: 明确延后
- 立法沙盘完整版本
- 用户账号体系
- 多租户协作
- 大规模历史案件持久化
- 刑事/行政诉讼全覆盖

## Out of Scope
- 自训练法律大模型
- 复杂知识图谱构建
- 真正具备司法预测准确性的专业判决引擎
- 面向真实生产环境的隐私合规体系

## Primary Users

### User Type 1: 普通诉讼参与人
- 目标：知道怎么准备、对方可能怎么说、自己哪里弱
- 关注点：低门槛、可理解、建议具体

### User Type 2: 法学生/教师
- 目标：体验法庭流程、练习论证、对比不同策略结果
- 关注点：流程完整、节点真实、分支清晰

### User Type 3: 评委/答辩观众
- 目标：快速感知产品创新性与技术落地能力
- 关注点：可视化、稳定性、完成度、报告质量

## Product Strategy
产品设计上必须坚持四个原则：

1. `流程优先于生成`
   - 先定义法庭阶段、状态、可选动作，再让模型在受控边界内生成台词和内容。

2. `结构优先于自然语言`
   - 模型先输出结构化对象，再转成前端展示文本，避免“像聊天但不能控”。

3. `模板优先于自由发挥`
   - 报告、提示词、法条引用、对方证据生成都必须有模板骨架。

4. `演示优先于完整性`
   - 如果时间紧，优先保证主链路稳定，不追求所有案件类型和所有细节。

## Technical Architecture

### Architecture Summary
系统采用 `前端展示层 + 后端编排层 + 模型服务层 + 法律检索层 + 本地数据层` 的五层结构。

```text
Web Frontend (React/Vite)
    ->
API Layer (FastAPI)
    ->
Simulation Orchestrator / State Machine
    ->
LLM Agent Adapters + Legal Retrieval Adapter
    ->
SQLite + JSON Templates + Demo Data
```

### Why This Architecture
- React + Vite：开发快，交互表现好，适合做“事件卡 + 选项按钮 + 剧情推进”
- FastAPI：Python 生态方便接法律接口、处理 JSON、做 Prompt 编排
- SQLite：本地演示足够稳定，零部署成本
- JSON 状态机：把法庭流程固定下来，避免 AI 失控
- Prompt Adapter：可切换腾讯元器/元宝，便于比赛环境应对

## Core System Modules

### Module A: 案件录入模块
作用：把用户的案情、诉求、证据、对方信息转换成可供模拟引擎消费的结构化案件档案。

#### Input Blocks
- 案件类型
- 原告/被告身份
- 基本事实
- 诉讼请求/答辩意见
- 证据清单
- 对方信息与预判人设
- 己方企鹅律师风格

#### Output
- `CaseProfile` JSON
- `EvidenceBundle`
- `SimulationSeed`

### Module B: 庭审状态机模块
作用：把一次模拟拆成明确阶段，每阶段控制角色出场、可选策略、可触发事件和上下文注入。

#### Fixed Stages
- `PREPARE` 开庭准备
- `INVESTIGATION` 法庭调查
- `EVIDENCE` 举证质证
- `DEBATE` 法庭辩论
- `FINAL_STATEMENT` 最后陈述
- `MEDIATION_OR_JUDGMENT` 调解/宣判
- `REPORT_READY` 报告生成

#### Each Stage Contains
- 阶段说明
- 出场角色
- 事件文本模板
- 用户可选动作
- 模型生成槽位
- 风险分更新规则

### Module C: 角色模拟模块
作用：让不同企鹅角色在受控身份设定下输出文本和动作。

#### Roles
- 企鹅法官
- 己方企鹅律师
- 对方企鹅律师
- 企鹅证人
- 企鹅书记员/旁白

#### Constraints
- 每个角色只输出本角色该说的话
- 法官不直接替任何一方做实质辩护
- 对方律师必须围绕已有案情和允许的“突袭事件池”行动
- 证人证言必须与设定身份和案件事实一致

### Module D: 法律检索与支持模块
作用：为分支推演和报告补充法条、类案和规则依据。

#### Retrieval Targets
- 相关法条
- 常见争议焦点
- 类案裁判要点
- 证据规则说明

#### Fallback Strategy
- 若外部法律接口超时：
  - 使用本地预置规则库
  - 继续生成报告，但标记“接口降级”

### Module E: 胜诉率与风险分析模块
作用：不是给绝对司法预测，而是给 `模拟意义上的相对胜率与准备建议`。

#### Scoring Dimensions
- 诉讼请求支持率
- 证据采信风险
- 对方抗辩压力
- 程序风险
- 调解可行性

#### Scoring Method
- 规则分：根据证据完整度、争议焦点覆盖度、程序异常打基础分
- 模型分：根据当前剧情走向、对抗表现、风险暴露调整分值
- 最终用区间化表达：
  - 高
  - 中高
  - 中
  - 中低
  - 低

### Module F: 报告生成模块
作用：把全流程输出整理成比赛可展示的文档化成果。

#### Report Types
- 《庭审模拟复盘报告》
- 《庭前备战清单》

#### Report Sections
- 案件摘要
- 本次模拟关键节点
- 高风险点
- 证据补强建议
- 推荐抗辩/应对话术
- 对方可能追加动作
- 参考法条/类案
- 总体准备建议

## Repo Blueprint

```text
E:\lawai\
  apps\
    web\                  # React 前端
    api\                  # FastAPI 后端
  packages\
    shared\               # 类型、常量、共享 schema
    prompts\              # Prompt 模板
    rules\                # 本地法律规则、评分规则
    templates\            # 报告模板、剧情模板
  data\
    demo_cases\           # 预置 demo 输入
    legal_seed\           # 本地法条/规则摘录
  docs\
    architecture.md
    api-contract.md
    prompt-design.md
    demo-script.md
  specs\
    penguin-court-mvp.spec.md
```

## Suggested Tech Stack

### Frontend
- React
- Vite
- TypeScript
- Tailwind CSS
- Zustand 或 Context 管理模拟会话状态

### Backend
- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy 或 SQLModel

### Storage
- SQLite
- JSON 文件存储 demo 与模板

### Integration
- 腾讯元器 / 腾讯元宝模型调用
- 得理法律 API 或同类法律检索接口

### Export/Display
- Markdown -> HTML 模板
- 必要时用浏览器打印为 PDF

## Two-Engineer Ownership Plan

### 技术同学 1: 全栈与系统编排负责人
负责项目“能跑起来”的骨架。

#### Ownership
- 前端页面开发
- 后端基础接口
- 庭审状态机
- 数据模型与存储
- 部署与本地运行环境

#### Files/Modules Owned
- `apps/web/**`
- `apps/api/routes/**`
- `packages/shared/**`
- `packages/templates/flow-config/**`

### 技术同学 2: Agent 与智能推演负责人
负责项目“像 AI 产品”的核心体验。

#### Ownership
- Prompt 设计
- 角色 Agent 约束
- 法律接口对接
- 胜诉率评分逻辑
- 报告生成逻辑

#### Files/Modules Owned
- `packages/prompts/**`
- `packages/rules/**`
- `apps/api/services/llm/**`
- `apps/api/services/legal/**`

### Shared Ownership
- Demo 样例打磨
- 联调
- Bug 修复
- 比赛演示流程固化
- 答辩技术材料

## Functional Requirements

### FR-001: 案件创建
When the user starts a new simulation, the system shall create a case session with a unique case ID and default stage `PREPARE`.

### FR-002: 分步录入
While the user is in the intake flow, when they complete each required section, the system shall validate and persist the section before allowing the next step.

### FR-003: 案件类型限制
When the user selects an unsupported case type, the system shall block simulation start and show the currently supported case categories.

### FR-004: 证据结构化
When the user submits evidence items, the system shall store each item with evidence type, purpose, source, and confidence level.

### FR-005: 人设选择
When the user selects a己方企鹅律师风格, the system shall inject the matching style profile into subsequent simulation prompts.

### FR-006: 模拟启动
While all required intake fields are complete, when the user clicks “开始模拟”, the system shall generate the first stage event and available branch actions.

### FR-007: 阶段推进
When the user selects a branch option, the system shall advance the simulation state, update scores, and generate the next stage content.

### FR-008: 对方行为模拟
While a simulation stage requires confrontation, when the next event is generated, the system shall produce opponent behavior consistent with case facts, role constraints, and allowed surprise-event rules.

### FR-009: 法官主持逻辑
While the active role is judge, the system shall output procedural guidance, issue focus prompts, and stage transitions without acting as an advocate.

### FR-010: 分支控制
When the model response is received, the system shall parse it into predefined structured fields instead of directly rendering raw text.

### FR-011: 失败兜底
When the model fails to return valid structured output, the system shall retry once and then fall back to a template-based event.

### FR-012: 法律依据补足
When a report is generated, the system shall include related legal basis and case-type-specific rule references from API or local fallback data.

### FR-013: 风险评分
When a simulation turn ends, the system shall update the case risk profile across evidence, procedure, confrontation, and outcome dimensions.

### FR-014: 复盘报告
When the simulation reaches report stage, the system shall generate a replay summary, risk analysis, suggestions, and branch explanation.

### FR-015: 庭前备战清单
When the user requests preparation output, the system shall generate a checklist of missing evidence, speaking points, likely attacks, and recommended next actions.

### FR-016: Demo 案例加载
When the operator chooses a preset demo case, the system shall prefill the intake form and allow simulation start within one click.

### FR-017: 会话恢复
While a case session exists locally, when the user reopens the session, the system shall restore stage state, inputs, and generated turns.

### FR-018: 日志记录
When any model or external API call is made, the system shall record request metadata, latency, and result status for debugging.

### FR-019: 演示模式
Where demo mode is enabled, the system shall prioritize stable templates and preset branch flows over highly random generation.

### FR-020: 报告下载
When the user views a completed report, the system shall support exporting or printing it in a presentation-friendly format.

## Non-Functional Requirements

### Performance
- Intake page first load <= 2s on local machine
- Single model interaction target <= 8s
- 完整演示链路目标 <= 90s
- 报告生成 <= 15s

### Stability
- 所有关键 API 返回统一错误结构
- 模型调用失败后至少有 1 次重试和 1 次模板兜底
- 外部法律接口不可用时，系统仍可完成演示主流程

### Security
- 不采集真实身份证号、手机号等敏感个人信息作为必填项
- 所有日志默认脱敏显示
- Prompt 中不直接拼接原始长文本到高权限系统指令段

### Observability
- 记录每次阶段推进日志
- 记录模型输出解析失败原因
- 记录胜诉率评分构成

### Maintainability
- Prompt 模板、规则模板、报告模板独立存储
- 前后端共享 schema，避免字段漂移
- 分支剧情事件池可通过 JSON 配置扩展

## Data Model Draft

### CaseSession
- `id`
- `case_type`
- `plaintiff_role`
- `defendant_role`
- `claims`
- `facts_summary`
- `current_stage`
- `lawyer_persona`
- `opponent_persona`
- `status`
- `created_at`
- `updated_at`

### EvidenceItem
- `id`
- `case_id`
- `title`
- `evidence_type`
- `purpose`
- `source`
- `strength_level`
- `notes`

### SimulationTurn
- `id`
- `case_id`
- `stage`
- `speaker_role`
- `scene_text`
- `branch_options_json`
- `selected_option`
- `score_delta_json`

### RiskProfile
- `case_id`
- `claim_support_score`
- `evidence_score`
- `procedure_risk_score`
- `debate_score`
- `settlement_score`
- `overall_level`

### ReportArtifact
- `case_id`
- `report_markdown`
- `prep_checklist_markdown`
- `legal_refs_json`
- `generated_at`

## API Contract Draft

### `POST /api/cases`
作用：创建案件会话

### `POST /api/cases/{id}/intake`
作用：保存案件录入信息

### `POST /api/cases/{id}/simulate/start`
作用：启动模拟，返回首轮剧情

### `POST /api/cases/{id}/simulate/turn`
作用：提交一个策略选项并获取下一轮剧情

### `GET /api/cases/{id}/timeline`
作用：获取当前会话完整进展

### `POST /api/cases/{id}/report/generate`
作用：生成复盘报告和备战清单

### `GET /api/demo-cases`
作用：获取预置 demo 案例

## Prompt Design Strategy

### Prompt Layers
1. `System Layer`
   - 定义角色、边界、输出格式、禁止事项
2. `Case Context Layer`
   - 注入案件结构化摘要
3. `Stage Context Layer`
   - 当前庭审阶段、可允许动作、上一轮结果
4. `Output Schema Layer`
   - 强制模型按 JSON 输出

### Prompt Principles
- 不要求模型“自由模拟一场完整法庭”，而是一次只生成一个阶段事件
- 不让模型自行决定流程顺序，流程由状态机决定
- 不让模型自己发明过多事实，只能在允许的 surprise pool 中取材

### Structured Output Example
```json
{
  "speaker_role": "opponent_lawyer",
  "scene_summary": "对方律师提交一份聊天记录并主张其证明借款已部分归还",
  "narrative_text": "企鹅对方律师推了推眼镜，递上一份新证据……",
  "branch_options": [
    {
      "id": "challenge_authenticity",
      "label": "质疑真实性",
      "impact_hint": "提高程序掌控，可能延长争议"
    },
    {
      "id": "accept_partial",
      "label": "承认部分事实",
      "impact_hint": "降低冲突，但可能压缩请求空间"
    }
  ],
  "score_delta": {
    "evidence_score": -8,
    "procedure_risk_score": 3
  }
}
```

## Acceptance Criteria

### AC-001: 用户成功创建并录入案件
Given 用户选择了支持的案件类型  
When 用户完成必填表单并点击开始模拟  
Then 系统成功创建案件会话  
And 返回首个庭审阶段剧情  
And 页面显示可点击的策略分支

### AC-002: 庭审阶段按法定顺序推进
Given 一个已启动的模拟案件  
When 用户连续完成多个阶段选择  
Then 系统按 `开庭准备 -> 法庭调查 -> 举证质证 -> 法庭辩论 -> 最后陈述 -> 调解/宣判` 顺序推进  
And 不跳阶段  
And 每阶段都有明确的当前状态展示

### AC-003: 对方行为可感知且不失控
Given 一个民间借贷案件模拟进行中  
When 系统生成对方律师发言  
Then 内容与案件事实相关  
And 不出现完全无关的新事实  
And 至少给出 2 个应对策略选项

### AC-004: 模型输出异常时系统不崩溃
Given 模型接口超时或返回非法 JSON  
When 后端处理该轮生成  
Then 系统自动重试  
And 重试失败后切换为模板事件  
And 前端仍然可以继续下一步操作

### AC-005: 报告可供比赛展示
Given 一个模拟案件完成  
When 用户进入报告页  
Then 页面展示案件摘要、风险点、建议动作、法条依据和备战清单  
And 报告内容不少于空泛结论  
And 可以作为比赛演示材料直接展示

### AC-006: Demo 案例可快速加载
Given 操作员在演示现场  
When 选择预置 demo 案例  
Then 表单在 1 次点击内完成预填  
And 30 秒内能进入第一轮庭审互动

### AC-007: 胜诉率分析可解释
Given 用户完成了一条分支模拟  
When 查看结果分析  
Then 系统展示至少 3 个评分维度  
And 每个维度都有文字解释  
And 给出至少 3 条可执行建议

### AC-008: 降级后仍可交付 MVP
Given 立法沙盘模块尚未完成  
When 系统准备比赛提交  
Then 庭审模拟主链路仍然完整可运行  
And 所有提交样例均可围绕 MVP 展示  
And 不因二期模块缺失影响答辩完整性

## Error Handling

| Error Condition | Source | System Response | User Message |
|-----------------|--------|----------------|--------------|
| 表单字段缺失 | 前端/后端校验 | 阻止进入下一步 | 请补充必填案件信息 |
| 不支持的案件类型 | 业务规则 | 返回 400 | 当前版本暂支持民间借贷、劳动争议 |
| 模型超时 | LLM 服务 | 自动重试一次，失败则模板兜底 | 智能推演较忙，已切换稳定模式 |
| 模型返回非法结构 | LLM 服务 | 记录日志并兜底 | 当前轮结果已采用稳定生成策略 |
| 法律接口不可用 | 外部 API | 使用本地规则数据 | 法律检索服务暂不可用，已切换本地规则 |
| 会话找不到 | 数据层 | 返回 404 | 当前会话不存在，请重新开始 |
| 报告生成失败 | 模板/服务 | 返回重试按钮 | 报告生成失败，请重试 |

## 15-Day Execution Plan

### 2026-04-07
- 明确最终范围，只锁 `庭审模拟 MVP`
- 建 repo、目录结构、开发规范、分支策略
- 输出：
  - `architecture.md`
  - `repo bootstrap`

### 2026-04-08
- 技术同学 1：
  - 起 React 前端和 FastAPI 后端
  - 定共享 schema
- 技术同学 2：
  - 写 Prompt 初版
  - 设计阶段状态机字段
- 输出：
  - 可运行空壳页面
  - `prompt-design.md v1`

### 2026-04-09
- 完成案件录入表单与数据结构
- 完成 2 类案件字段差异设计
- 输出：
  - 表单页面
  - `CaseProfile` schema

### 2026-04-10
- 完成庭审状态机主干
- 每阶段定义输入、输出、分支按钮
- 输出：
  - `flow-config.json`
  - 状态推进服务

### 2026-04-11
- 对接腾讯模型服务
- 打通“启动模拟 -> 返回首轮结构化事件”
- 输出：
  - `simulate/start` 可用

### 2026-04-12
- 做每轮分支推进接口
- 接入对方律师/法官两类角色输出
- 输出：
  - `simulate/turn` 可用

### 2026-04-13
- 接入本地规则库与法律检索接口
- 初版胜诉率维度评分逻辑
- 输出：
  - `legal adapter`
  - `risk scorer v1`

### 2026-04-14
- 做报告生成模块
- 前端接报告页与时间线页
- 输出：
  - 报告页面
  - 复盘文本初版

### 2026-04-15
- 完成 3 组 demo 案例
- 为每组案例准备稳定分支路径
- 输出：
  - `data/demo_cases/*.json`
  - `demo-script.md`

### 2026-04-16
- 全链路联调
- 修复 JSON 解析、状态跳转、前端渲染问题
- 输出：
  - MVP alpha

### 2026-04-17
- 做稳定性强化
- 加模型失败兜底与日志
- 输出：
  - MVP beta

### 2026-04-18
- 打磨 UI 表现
- 优化剧情文字、角色表现、报告可读性
- 输出：
  - MVP release candidate

### 2026-04-19
- 压测 3 组 demo
- 固化答辩演示脚本
- 输出：
  - `demo dry-run checklist`

### 2026-04-20
- 处理最终 bug
- 打包演示环境
- 输出：
  - 可交付 demo 包

### 2026-04-21
- 冻结代码
- 检查说明书、输入输出样例、PPT 技术部分
- 输出：
  - 正式提交版

## Daily Sync Mechanism
- 每天上午 10:00 站会，10 分钟
- 每天晚上 22:00 日结，记录：
  - 今天完成什么
  - 卡在哪
  - 明天第一优先级是什么
- 每 2 天一次“可演示检查”，不是看代码量，而是看功能是否能演示

## Implementation TODO

### Backend
- [ ] 建立 FastAPI 项目骨架
- [ ] 设计 Pydantic schema
- [ ] 建立 SQLite 表结构
- [ ] 实现案件录入接口
- [ ] 实现模拟启动接口
- [ ] 实现模拟推进接口
- [ ] 实现报告生成接口
- [ ] 实现 demo 案例加载接口
- [ ] 接入 LLM adapter
- [ ] 接入法律检索 adapter
- [ ] 实现评分器
- [ ] 实现模板兜底逻辑
- [ ] 实现日志和错误结构

### Frontend
- [ ] 案件录入页
- [ ] 庭审模拟页
- [ ] 分支选项组件
- [ ] 剧情时间线组件
- [ ] 角色卡组件
- [ ] 报告页
- [ ] demo 案例加载入口
- [ ] 错误提示和 loading 态
- [ ] 打印/导出报告样式

### Prompt / AI
- [ ] 角色系统提示词
- [ ] 阶段事件生成提示词
- [ ] 结构化输出约束
- [ ] Surprise event 池
- [ ] 报告生成提示词
- [ ] 降级模板库
- [ ] 3 组 demo 专用稳定提示词

### Testing
- [ ] 表单校验测试
- [ ] 状态机推进测试
- [ ] JSON 解析失败测试
- [ ] 模型超时兜底测试
- [ ] 报告生成测试
- [ ] 3 组 demo 全链路测试

## Biggest Risks and Mitigations

### Risk 1: 模型输出不稳定
- 解决：
  - 强制 JSON 结构
  - 减少单次生成长度
  - 模板兜底
  - demo 模式稳定化

### Risk 2: 庭审流程过于复杂导致开发爆炸
- 解决：
  - 只做主链路
  - 每阶段限制 2 到 3 个核心策略选项
  - 不追求无限分支

### Risk 3: 法律内容显得不专业
- 解决：
  - 用法学同学提供的规则先行
  - 报告引用明确写“依据类型”
  - 高风险表述采用保守语言

### Risk 4: 演示现场网络/接口不稳定
- 解决：
  - 提前缓存 demo 输入
  - 预置稳定剧情路径
  - 本地规则库兜底
  - 本地部署优先

## Final Recommendation
本项目的正确打法不是“做一个万能法律 AI”，而是“做一个结构化、可控、可展示的庭审模拟产品”。技术上要坚定选择 `状态机 + Prompt + 模板 + 本地规则 + 外部接口补强` 的路线。只要我们在 2026-04-14 前跑通主链路、在 2026-04-17 前把稳定性打住，后面三天主要就是把它打磨成一个让评委觉得“这已经是产品”的作品。
