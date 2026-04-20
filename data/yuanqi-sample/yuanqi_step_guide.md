# 元器一步一步搭建指南（企鹅法庭）

> 版本：2026-04-07  
> 适用项目：企鹅法庭·沉浸式庭审模拟与立法沙盘推演 AI 智能体系统  
> 用途：正式搭元器时，只看这一份，照着做  
> 当前主轴：`案件录入 -> 庭审模拟 -> 对方行为模拟 -> 胜诉率分析 -> 复盘报告`

> 只看这一份的意思：
> 如果你现在要正式在元器里动手搭，下面这份文档已经把“规则 + 顺序 + 字段 + 工作流配置动作”合在一起了。
> `元器工作流联动契约（企鹅法庭）.md` 和 `元器接入实操手册（企鹅法庭）.md` 属于我内部拆解时留下的支撑文档，你正式搭建时可以先不看。

## 0. 先认元器页面长什么样

我这版说明按腾讯元器官方帮助中心 2025-12 到 2026-03 的页面说明重写过，先把你实际会看到的页面说清楚：

### 0.1 智能体应用配置页

你点进一个智能体后，先看到的是应用配置页。

- 左边是配置区
- 右边是调试区
- 应用名称附近可以点开“编辑应用”弹窗
- 模式切换就在这里改

### 0.2 工作流管理入口

在智能体应用详情页上方，有一个明显的 `工作流管理` 按钮。

点进去以后，你会进入工作流管理页。这里能做：

- 新建
- 配置
- 启用
- 删除
- 导入
- 导出

### 0.3 工作流画布页

你新建一个工作流以后，会进入工作流画布页。这个页面通常这样看：

- 左边：节点面板
- 中间：画布
- 右边：当前节点配置区
- 右上：整体调试入口

你往画布里拖节点，连线以后，如果想在两节点中间插一个节点，可以把鼠标放到连线上，点 `➕` 插入。

### 0.4 插件创建页

插件不是在工作流画布里创建的，而是走单独的插件创建流程。

你会经过一个类似向导的页面：

1. 填插件名称、描述、图标
2. 选授权方式：`无需授权` 或 `API Key`
3. 配工具名称、调用地址、入参出参
4. 点 `解析为工具`
5. 点 `去校验`
6. 校验通过再保存

### 0.5 这套项目正式版只会用到这些节点

你搭这套“企鹅法庭”正式版时，画布里基本只会反复用到这几种：

- `开始节点`
- `代码节点`
- `大模型节点`
- `插件节点`
- `工作流节点`
- `条件判断节点`
- `回复节点`
- `结束节点`

你如果在左侧节点面板里一眼没看到，先展开节点分类再找。

### 0.6 这份手册里哪些是官方确认，哪些必须首轮实测

为了避免你把“平台事实”和“项目设计”混在一起，这里直接分 3 类：

#### A 类：官方帮助中心已明确确认

这些我可以明确说“平台层面基本确定”：

- 应用详情页可以通过 `编辑应用` 切应用模式
- `单工作流模式` 下可以进入 `工作流管理`
- `工作流管理` 页支持 `新建 / 配置 / 启用 / 删除 / 导入导出`
- 工作流画布左侧拖节点，中间画布编排，右上可调试
- `开始节点` 的 `API 参数` 会接收 `custom_variables`
- `代码节点` 支持写 `Python`
- `代码节点` 官方建议保留函数名 `main`，输入输出都是 `dict`
- `工作流节点` 会根据被引用工作流自动展示输入变量
- 被引用工作流真正返回给主工作流的是 `结束节点` 输出变量
- `回复节点` 是给用户输出内容，不是给主工作流传结构化结果
- 插件创建流程里有 `API Key`、`解析为工具`、`去校验`
- 插件节点可以在工作流里直接引用已创建好的插件工具
- 插件节点的 `API 参数` 支持 `header / query / body`

#### A+ 类：你这份导出样例已经实锤的真实平台细节

这是我刚从你给的导出样例 `7f1cbac9-0d7f-413b-84cb-1f8f32c3fe6f_workflow.json` 里直接确认到的：

- 代码节点内部默认提示明确写着：
  - `请保存函数名为 main`
  - `输入输出均为 dict`
- 代码节点内部类型名确实是 `CODE_EXECUTOR`
- 条件判断节点内部类型名确实是 `LOGIC_EVALUATOR`
- 回复节点内部类型名确实是 `ANSWER`
- 结束节点内部类型名确实是 `END`
- 知识检索节点内部类型名确实是 `KNOWLEDGE_RETRIEVER`
- 大模型节点在 `LLM_OUTPUT_JSON` 模式下，导出里明确出现：
  - `Output`
  - `Output.Thought`
  - `Output.Content`

这意味着一个非常重要的操作结论：

- 你在代码节点里引用大模型结果时，第一优先要找的是类似 `Output.Content` 这种实际输出路径
- 不要想当然写成我随口起的 `llm_output`
- 文档里后面凡是写到 `llm_output` 的地方，你都应该在元器右侧变量引用面板里，优先去找大模型节点的 `Output.Content`

#### B 类：这是本项目的设计约定，不是平台强制字段

这些不是腾讯元器官方固定写死的，而是我为了你的“企鹅法庭”主链专门定的项目契约：

- `W01 / W02 / W03 / W04 / W00` 这一组命名
- `scene_title / legal_support_summary / win_rate_estimate` 这些输出字段名
- `focus_issues_json / claims_json / recommended_laws_json` 这些入参名
- `W00` 里按 `prepare -> debate -> report_ready` 去分流
- `W01` 只出 `suggested_actions`，不直接出正式 `available_actions`

这部分不是“平台要求如此”，而是“为了让你的后端、元器、比赛主轴能稳定联起来，必须这样约定”。

#### C 类：我现在不能说 100% 已实机验证，必须首轮调试确认

这些地方我现在只能说“高概率对，但你第一次搭时必须看页面和调试结果确认”：

- 你账号当前页面上的按钮文案是否和帮助中心截图完全一致
- 插件页面里 `API Key` 的具体录入交互，是直接填值还是先建参数再引用
- `解析为工具` 后，得理接口的入参与出参是否被自动识别得足够完整
- 代码节点里你最终选择的输出变量名，和下游引用时的变量路径是否一字不差
- `W02` 插件返回的原始字段结构，是否和我整理提示词时假设的一致
- `W00` 合并时，各工作流节点的 `payload_json` 实际引用路径

所以你可以把这份手册理解成：

- 平台骨架：已经核官方
- 项目链路：已经按你的主轴锁死
- 最后一层字段映射：仍然需要你在元器里跑第一轮调试确认

## 1. 为什么这个项目正式选单工作流模式

腾讯元器官方给的判断方法其实就两个问题：

1. 一个工作流能不能解决全部问题
2. 这个应用是否要求用户 100% 进入工作流

你的项目正式链路是：

`案件录入 -> 庭审模拟 -> 对方行为模拟 -> 胜诉率分析 -> 复盘报告`

它就是一个固定主链，而且你不希望用户问天气、闲聊、跳流程时把主链打散，所以正式方案要选：

`单工作流模式`

别把正式交付主链放到 `Multi-Agent 模式` 上，原因很直接：

- 官方模式说明里，`Multi-Agent 模式` 不支持工作流
- 你的项目正式交付又必须依赖工作流编排
- 所以正式版主链不能建立在 Multi-Agent 上

## 2. 先记住这一句

正式搭建时，你只按这一条链路做：

`每个庭审回合只调用一次 W00_企鹅法庭主控编排`

然后由 `W00` 内部按阶段顺序调用：

- `W01_庭审场景生成`
- `W02_法律支持检索`
- `W03_对方行为模拟`
- `W04_结果分析复盘`

不要正式按“每个子工作流各调一次”去搭。

## 3. 你最终要搭出来的东西

元器里总共搭这 6 个：

1. `得理法律检索插件（企鹅法庭）`
2. `W01_庭审场景生成`
3. `W02_法律支持检索`
4. `W03_对方行为模拟`
5. `W04_结果分析复盘`
6. `W00_企鹅法庭主控编排`

顺序也必须按这个来。

## 4. 正式搭建前先锁死的 5 条规则

你搭的时候不要边搭边重新发明规则，先直接照这个认：

### 规则 1：阶段只能后端决定

元器不能自己决定：

- 从 `prepare` 跳到 `investigation`
- 从 `debate` 直接结束
- 修改 `current_stage`

元器只能根据后端传来的 `current_stage` 生成内容。

### 规则 2：第一版 `W01` 不负责正式动作按钮

当前后端还在自己校验：

- `selected_action`
- `available_actions`

所以第一版必须这样做：

- 后端负责正式 `available_actions`
- 元器 `W01` 只输出 `suggested_actions`

不要让 `W01` 直接产出系统正式动作列表。

### 规则 3：`W04` 必须吃 `W02` 的结果

如果法律检索结果没有传到复盘分析，工作流就是断的。

所以正式搭的时候必须认：

- `W02` 输出的 `legal_support_summary`
- `recommended_laws`
- `recommended_cases`
- `issue_mapping`

都要继续进 `W04`

### 规则 4：角色字段只能用后端枚举值

所有角色相关字段只能输出这些值：

- `plaintiff`
- `defendant`
- `applicant`
- `respondent`
- `agent`
- `witness`
- `judge`
- `other`

不要输出：

- 审判长
- 原告律师
- 被告代理律师
- 原告方

这些自然语言标签后面会把联调搞乱。

### 规则 5：子工作流正式回传统一走 `结束节点`

这是这次补课后必须加上的平台规则：

- `回复节点` 是给用户看的
- `结束节点` 是给工作流返回结构化变量的
- `W01 / W02 / W03 / W04` 既然要被 `W00` 通过 `工作流节点` 引用，正式版就必须在最后配置 `结束节点`

你如果想单独调某个子工作流：

- 可以临时加一个 `回复节点` 看效果
- 但正式联调前，要确认 `结束节点` 已经把下游要吃的变量全部配好

## 5. 先准备你手里的信息

在开始搭之前，你先准备好：

### 元器侧

- 元器工作流编排权限
- 元器发布 API 权限
- 发布后能拿到 `assistant_id`

### 得理侧

- `appid`
- `secret`
- `base_url`

建议你自己本地记成：

```env
DELILEGAL_APP_ID=
DELILEGAL_APP_SECRET=
DELILEGAL_BASE_URL=https://openapi.delilegal.com
```

### 当前项目侧

你要知道当前后端主要会给你这些变量：

- `case_id`
- `current_stage`
- `turn_index`
- `selected_action`
- `branch_focus`
- `case_type`
- `title`
- `summary`
- `claims`
- `focus_issues`
- `missing_evidence`
- `opponent_profile`

## 5.1 正式开搭前先把应用模式切对

这一步先做，不然你后面进去容易发现按钮和我写的不一样。

### 你就按这个点

1. 进入你的元器智能体应用详情页
2. 找到应用名称附近的 `编辑应用`
3. 打开后找到 `应用模式`
4. 在模式列表里选 `单工作流模式`
5. 点 `确认` 或 `保存`
6. 回到应用详情页
7. 确认页面上能看到 `工作流管理`

### 如果你没看到 `工作流管理`

优先排这 3 个原因：

1. 你还没切到 `单工作流模式`
2. 你当前账号没有工作流编排权限
3. 你还停在应用编辑弹窗里，没有回到应用详情页

## 6. 第一步：先搭得理插件

### 你就按这个点

1. 进入元器插件创建入口
2. 点 `创建插件`
3. 在基础信息页填写：
   - 插件名称：`得理法律检索插件（企鹅法庭）`
   - 插件描述：`给企鹅法庭工作流提供法条检索、案例检索、法规详情查询能力`
4. 点下一步，进入授权配置
5. 这里推荐先选 `无需授权`
6. 不要在这一步强行用平台自带的 `API Key` 授权位去硬塞 `appid + secret`
7. 原因很简单：元器官方文档把 `ApiKey` 授权描述成单个密钥参数，而得理这里是双 header 认证
8. 所以这套项目更稳的做法是：
   - 插件层先不使用平台统一 `ApiKey` 授权位
   - 在具体工具的 `header` 参数里手工配置 `appid` 和 `secret`
9. 保存后进入工具配置页

### 工具页先建这 3 个工具

如果页面上是 `添加工具` 就点它；如果文案写成 `新增工具`，点同位置那个按钮也行。

你要依次建：

1. `search_case`
2. `search_law`
3. `get_law_info`

### 方法 1：`search_case`

#### 你就按这个点

1. 点 `添加工具`
2. 工具名称填 `search_case`
3. 工具描述填 `按关键词检索案例列表`
4. 请求方式选 `POST`
5. 请求地址填下面这个 URL
6. 在 API 参数里找到 `header`
7. 手工新增这 2 个 header 参数：
   - `appid`
   - `secret`
8. `appid` 和 `secret` 暂时先留空也可以
9. Body 类型选 `JSON`
10. 把下面这段请求体贴进去
11. 点 `解析为工具`
12. 检查是否自动识别出了 `keyword`
13. 点 `去校验`
14. 校验通过后保存这个工具

- Method: `POST`
- URL:

```text
https://openapi.delilegal.com/api/qa/v3/search/queryListCase
```

Header 需要：

- `appid`
- `secret`

Body 先写成：

```json
{
  "pageNo": 1,
  "pageSize": 5,
  "sortField": "correlation",
  "sortOrder": "desc",
  "condition": {
    "keywordArr": ["{{keyword}}"]
  }
}
```

### 方法 2：`search_law`

#### 你就按这个点

1. 再点一次 `添加工具`
2. 工具名称填 `search_law`
3. 工具描述填 `按关键词检索法律法规`
4. 请求方式选 `POST`
5. 请求地址填下面这个 URL
6. 在 API 参数的 `header` 里继续配置：
   - `appid`
   - `secret`
7. Body 类型选 `JSON`
8. 把下面这段请求体贴进去
9. 点 `解析为工具`
10. 检查是否自动识别出了 `keyword`
11. 点 `去校验`
12. 校验通过后保存这个工具

- Method: `POST`
- URL:

```text
https://openapi.delilegal.com/api/qa/v3/search/queryListLaw
```

Header 需要：

- `appid`
- `secret`

Body 先写成：

```json
{
  "pageNo": 1,
  "pageSize": 5,
  "sortField": "correlation",
  "sortOrder": "desc",
  "condition": {
    "keywords": ["{{keyword}}"],
    "fieldName": "semantic"
  }
}
```

### 方法 3：`get_law_info`

#### 你就按这个点

1. 再点一次 `添加工具`
2. 工具名称填 `get_law_info`
3. 工具描述填 `根据 law_id 查询法规详情`
4. 请求方式选 `GET`
5. 请求地址填下面这个 URL
6. 在 API 参数的 `header` 里继续配置：
   - `appid`
   - `secret`
7. 点 `解析为工具`
8. 检查是否自动识别出了 `law_id`
9. 点 `去校验`
10. 校验通过后保存这个工具

- Method: `GET`
- URL:

```text
https://openapi.delilegal.com/api/qa/v3/search/lawInfo?lawId={{law_id}}&merge=true
```

### 这一阶段你要特别注意

文档里的：

- `{{keyword}}`
- `{{law_id}}`
- `{{appid}}`
- `{{secret}}`

都只是占位写法。

你只要保证最终请求头里真的有：

- `appid`
- `secret`

就行。

### 为什么这里不再写“插件授权方式一定选 API Key”

因为我重新核了腾讯元器官方帮助中心后，平台明确写清楚的是：

- 插件/工具支持 `ApiKey` 授权
- `ApiKey` 文档示例是单个 `密钥参数名 + 密钥值`
- 插件节点本身还支持在 `API 参数` 里手工配置 `header / query / body`

而得理开放平台这次比赛给你的调用方式是：

- `appid`
- `secret`

两个 header 同时传。

所以对这套项目来说，更稳的正式做法是：

- 不把双 header 认证赌在平台统一 `ApiKey` 授权位上
- 直接把 `appid` 和 `secret` 当成工具级 `header` 参数配置

### 插件整体保存前最后检查一次

1. 看 3 个工具是不是都已经在插件里了
2. 看每个工具是不是都校验通过
3. 看 `appid` 和 `secret` 有没有真绑到 Header
4. 点插件页的 `保存`
5. 回到插件列表，确认能看到 `得理法律检索插件（企鹅法庭）`

### 这一阶段的完成标准

你单独测试插件时，能做到：

- 输入一个法律关键词，`search_law` 能回结果
- 输入一个案例关键词，`search_case` 能回结果
- 输入一个 `law_id`，`get_law_info` 能回法规详情

## 7. 第二步：搭 `W01_庭审场景生成`

### 你就按这个点

1. 回到智能体应用详情页
2. 点 `工作流管理`
3. 点 `新建`
4. 如果页面让你选创建方式，选 `手动录入`
5. 工作流名称填 `W01_庭审场景生成`
6. 工作流描述填 `根据当前庭审阶段生成场景文案和展示建议`
7. 点确认，进入工作流画布

### 画布上按这个顺序拖节点

正式版按这个顺序搭：

1. `开始节点`
2. `代码节点`
3. `大模型节点`
4. `代码节点`
5. `结束节点`

如果你想单独调试看文案，可以临时再加一个 `回复节点` 放在最后一个代码节点和结束节点之间。

正式联调前，保留 `结束节点`，`回复节点` 可删。

### 开始节点变量

点一下 `开始节点`，在右侧找到 `API 参数`，点 `管理`，把下面这些参数逐个加进去：

- `case_id`
- `current_stage`
- `turn_index`
- `selected_action`
- `next_stage`
- `branch_focus`
- `v_case_type`
- `v_case_title`
- `v_case_summary`
- `v_notes`
- `focus_issues_json`
- `claims_json`
- `missing_evidence_json`
- `opponent_arguments_json`

### 代码节点要做什么

点第一个 `代码节点`，右侧先选运行语言：

- 推荐选 `Python`

然后做这 4 件事：

1. 在输入变量区引用开始节点的这些字段
2. 把 JSON 字符串还原成数组
3. 产出给大模型节点可直接引用的清洗变量
4. 保留原始 `current_stage` 和 `selected_action`

例如：

- `focus_issues_json`
- `claims_json`
- `missing_evidence_json`
- `opponent_arguments_json`

### 大模型提示词直接这样写

点 `大模型节点`，在右侧做这几件事：

1. 选择一个你当前可用的大模型
2. 在输入变量区引用上一个代码节点的清洗结果
3. 如果有 `输出格式` 或 `结构化输出`，优先选择 `JSON`
4. 把下面这段提示词整段贴进去

```text
你是“企鹅法庭”的庭审场景生成器，不是自由聊天助手。

你只负责生成当前回合的场景文案和展示建议。
你不能决定系统正式动作列表，也不能修改庭审阶段。

必须遵守：
1. 不得脱离 current_stage。
2. 不得替后端决定是否跳阶段。
3. suggested_actions 只是建议，不是系统最终可点击动作。
4. 输出必须是 JSON。
5. 文风要像模拟法庭现场，而不是法律论文。
6. 不得编造明显违法、荒谬、失真的司法程序。
7. speaker_role 只能输出这些值之一：
   plaintiff、defendant、applicant、respondent、agent、witness、judge、other。

输出 JSON：
{
  "scene_title": "",
  "scene_text": "",
  "speaker_role": "",
  "suggested_actions": [],
  "branch_focus": "",
  "next_stage_hint": ""
}
```

### 第二个代码节点要做什么

点第二个 `代码节点`，只做两件事：

1. 检查大模型是不是返回了合法 JSON
2. 统一生成这 3 个输出变量：
   - `workflow_key`
   - `status`
   - `payload_json`

这里固定这样认：

- `workflow_key = courtroom_scene_generation`
- `status = ok`
- `payload_json` 里再包真正的场景结果

### `payload_json` 的内容结构

这个结构你在第二个代码节点里组出来：

```json
{
  "scene_title": "",
  "scene_text": "",
  "speaker_role": "",
  "suggested_actions": [],
  "branch_focus": "",
  "next_stage_hint": ""
}
```

### 结束节点怎么配

点 `结束节点`，在右侧输出变量里新增并绑定：

- `workflow_key`
- `status`
- `payload_json`

如果你临时加了 `回复节点` 调试，就让它直接输出 `payload_json`。

### 这一阶段完成标准

你单独测 `W01` 时，必须看到：

- 有 `scene_title`
- 有 `scene_text`
- 有 `suggested_actions`
- `speaker_role` 是枚举值

如果它吐出“审判长”“原告方”，就不算过。

## 8. 第三步：搭 `W02_法律支持检索`

### 你就按这个点

1. 回到 `工作流管理`
2. 点 `新建`
3. 选 `手动录入`
4. 工作流名称填 `W02_法律支持检索`
5. 工作流描述填 `调用得理插件完成法条和案例检索，并整理法律支持摘要`
6. 点确认进入画布

### 画布上按这个顺序拖节点

1. `开始节点`
2. `代码节点`
3. `插件节点`
4. `插件节点`
5. `插件节点`
6. `大模型节点`
7. `代码节点`
8. `结束节点`

第 5 个插件节点 `get_law_info` 是可选增强版。

如果你今天只想先跑通主链，可以先不接第 5 个插件节点。

### 开始节点变量

点 `开始节点`，在右侧 `API 参数 -> 管理` 里新增：

- `case_id`
- `case_type`
- `focus_issues_json`
- `fact_keywords_json`

### 代码节点要做什么

点第一个 `代码节点`，运行语言选 `Python`，然后只做 3 件事：

1. 解析 JSON 字符串数组
2. 生成 1 到 3 个检索关键词
3. 没有关键词时给兜底关键词

关键词规则：

- 优先用 `focus_issues_json`
- 不够时补 `fact_keywords_json`
- 一次不要喂太多，控制在 1 到 3 个

### 第一个插件节点怎么配

1. 点第一个 `插件节点`
2. 在右侧选择插件：`得理法律检索插件（企鹅法庭）`
3. 工具选择：`search_law`
4. 把上一个代码节点产出的主关键词绑定到插件参数 `keyword`
5. 在 `header` 参数里填：
   - `appid = 你的得理 appid`
   - `secret = 你的得理 secret`
6. 如果页面支持 `默认值` 与 `模型可见`，就把这两个 header 设成：
   - 有默认值
   - 模型不可见
7. 保存这个节点

### 第二个插件节点怎么配

1. 点第二个 `插件节点`
2. 插件仍然选：`得理法律检索插件（企鹅法庭）`
3. 工具选择：`search_case`
4. 同样把关键词绑定到 `keyword`
5. 在 `header` 参数里填：
   - `appid = 你的得理 appid`
   - `secret = 你的得理 secret`
6. 如页面支持，把这两个 header 设成模型不可见
7. 保存这个节点

### 第三个插件节点怎么配

只有当你准备增强法规详情时才接它：

1. 点第三个 `插件节点`
2. 插件仍然选：`得理法律检索插件（企鹅法庭）`
3. 工具选择：`get_law_info`
4. 把上游挑出来的 `law_id` 绑定进去
5. 在 `header` 参数里填：
   - `appid = 你的得理 appid`
   - `secret = 你的得理 secret`
6. 如页面支持，把这两个 header 设成模型不可见
7. 保存这个节点

### 大模型提示词直接这样写

点 `大模型节点`，在右侧做这几件事：

1. 选择可用大模型
2. 输入变量里引用：
   - 检索关键词
   - `search_law` 返回结果
   - `search_case` 返回结果
   - 如果接了增强节点，再引用 `get_law_info` 返回结果
3. 如果有 `结构化输出`，优先打开 JSON
4. 把下面提示词贴进去

```text
你是“企鹅法庭”的法律支持整理器。

你只负责整理得理插件返回的结果，不得凭空捏造法条。

必须遵守：
1. 输出必须是 JSON。
2. 每条法律支持尽量对应争议焦点。
3. 要指出当前事实和证据还不足的地方。
4. 输出结果后面还要继续传给对方行为模拟和结果分析。

输出 JSON：
{
  "legal_support_summary": "",
  "recommended_laws": [],
  "recommended_cases": [],
  "issue_mapping": [],
  "missing_points": []
}
```

### 第二个代码节点要做什么

点第二个 `代码节点`，把模型结果统一转成：

- `workflow_key`
- `status`
- `payload_json`

固定这样认：

- `workflow_key = legal_support_retrieval`
- `status = ok`

### `payload_json` 的内容结构

第二个代码节点里组这个：

```json
{
  "legal_support_summary": "",
  "recommended_laws": [],
  "recommended_cases": [],
  "issue_mapping": [],
  "missing_points": []
}
```

### 结束节点怎么配

点 `结束节点`，输出变量绑定：

- `workflow_key`
- `status`
- `payload_json`

### 这一阶段完成标准

你单独测 `W02` 时，必须看到：

- 得理插件能正常回数据
- 有 `legal_support_summary`
- 没有 `null`
- `recommended_laws` 和 `recommended_cases` 不是乱编的

## 9. 第四步：搭 `W03_对方行为模拟`

### 你就按这个点

1. 回到 `工作流管理`
2. 点 `新建`
3. 选 `手动录入`
4. 工作流名称填 `W03_对方行为模拟`
5. 工作流描述填 `在辩论与陈述阶段模拟对方的抗辩、动作和施压点`
6. 点确认进入画布

### 画布上按这个顺序拖节点

1. `开始节点`
2. `代码节点`
3. `大模型节点`
4. `代码节点`
5. `结束节点`

### 开始节点变量

点 `开始节点`，在 `API 参数 -> 管理` 里新增：

- `case_id`
- `current_stage`
- `selected_action`
- `branch_focus`
- `opponent_role`
- `opponent_name`
- `focus_issues_json`
- `claims_json`
- `likely_arguments_json`
- `likely_evidence_json`
- `likely_strategies_json`
- `legal_support_summary`

### 第一个代码节点要做什么

点第一个 `代码节点`，运行语言选 `Python`，然后：

1. 解析数组字符串
2. 整理出对方画像
3. 把 `legal_support_summary` 一并透传给大模型节点

### 大模型提示词直接这样写

点 `大模型节点`，输入变量里引用上一个代码节点的结果，然后贴下面提示词：

```text
你是“企鹅法庭”的对方行为模拟器。

你要在当前庭审阶段，结合案件信息和法律支持摘要，模拟对方最可能采取的动作与抗辩。

必须遵守：
1. 输出必须是 JSON。
2. opponent_role 只能输出：
   plaintiff、defendant、applicant、respondent、agent、witness、judge、other。
3. 不得写成戏剧化夸张冲突。

输出 JSON：
{
  "opponent_role": "",
  "opponent_action": "",
  "opponent_argument": "",
  "opponent_evidence": [],
  "risk_delta": "",
  "next_pressure": ""
}
```

### 第二个代码节点要做什么

点第二个 `代码节点`，把模型输出收口成：

- `workflow_key`
- `status`
- `payload_json`

固定这样认：

- `workflow_key = opponent_behavior_simulation`
- `status = ok`

### `payload_json` 的内容结构

第二个代码节点里组这个：

```json
{
  "opponent_role": "",
  "opponent_action": "",
  "opponent_argument": "",
  "opponent_evidence": [],
  "risk_delta": "",
  "next_pressure": ""
}
```

### 结束节点怎么配

点 `结束节点`，输出变量绑定：

- `workflow_key`
- `status`
- `payload_json`

### 这一阶段完成标准

你单独测 `W03` 时，必须看到：

- 有 `opponent_action`
- 有 `opponent_argument`
- `opponent_role` 不乱写
- 输出逻辑和当前阶段匹配

## 10. 第五步：搭 `W04_结果分析复盘`

### 你就按这个点

1. 回到 `工作流管理`
2. 点 `新建`
3. 选 `手动录入`
4. 工作流名称填 `W04_结果分析复盘`
5. 工作流描述填 `结合案件争议、证据缺口、对方抗辩和法律支持，输出胜诉率分析与复盘建议`
6. 点确认进入画布

### 画布上按这个顺序拖节点

1. `开始节点`
2. `代码节点`
3. `大模型节点`
4. `代码节点`
5. `结束节点`

### 开始节点变量

点 `开始节点`，在右侧 `API 参数 -> 管理` 里新增这些参数。

正式模式下，至少有这些：

- `case_id`
- `case_type`
- `current_stage`
- `turn_index`
- `branch_focus`
- `focus_issues_json`
- `claims_json`
- `missing_evidence_json`
- `opponent_arguments_json`
- `legal_support_summary`
- `recommended_laws_json`
- `recommended_cases_json`
- `issue_mapping_json`

增强变量：

- `opponent_action`
- `opponent_argument`
- `opponent_evidence_json`
- `risk_delta`

### 大模型提示词直接这样写

点第一个 `代码节点`，运行语言选 `Python`，先做两件事：

1. 把所有数组字符串恢复成数组
2. 把 `legal_support_summary / recommended_laws_json / recommended_cases_json / issue_mapping_json` 整理成模型好引用的变量

然后点 `大模型节点`，引用上一个代码节点的清洗变量，再贴下面提示词：

```text
你是“企鹅法庭”的结果分析与复盘生成器。

请基于案件争议点、证据缺口、对方抗辩，以及上游法律支持结果，输出结构化复盘。

必须遵守：
1. 不要给绝对化结论。
2. 胜诉率只给区间或倾向性判断。
3. 必须指出支持点和薄弱点。
4. 输出必须是 JSON。

输出 JSON：
{
  "win_rate_estimate": "",
  "issue_assessment": [],
  "risk_points": [],
  "evidence_gaps": [],
  "next_steps": [],
  "report_markdown": ""
}
```

### 第二个代码节点要做什么

点第二个 `代码节点`，把模型结果统一转成：

- `workflow_key`
- `status`
- `payload_json`

固定这样认：

- `workflow_key = outcome_analysis_report`
- `status = ok`

### `payload_json` 的内容结构

第二个代码节点里组这个：

```json
{
  "win_rate_estimate": "",
  "issue_assessment": [],
  "risk_points": [],
  "evidence_gaps": [],
  "next_steps": [],
  "report_markdown": ""
}
```

### 结束节点怎么配

点 `结束节点`，输出变量绑定：

- `workflow_key`
- `status`
- `payload_json`

### 这一阶段完成标准

你单独测 `W04` 时，必须看到：

- 有 `win_rate_estimate`
- 有 `risk_points`
- 有 `evidence_gaps`
- 它明显参考了 `W02` 的法律支持结果

如果它没吃法律支持结果，这条链就是断的。

## 11. 第六步：最后搭 `W00_企鹅法庭主控编排`

### 你就按这个点

1. 回到 `工作流管理`
2. 点 `新建`
3. 选 `手动录入`
4. 工作流名称填 `W00_企鹅法庭主控编排`
5. 工作流描述填 `按庭审阶段调度 W01/W02/W03/W04，并统一回传当前回合结果`
6. 点确认进入画布

### 先记住它只干什么

`W00` 不创造法律内容，它只负责：

- 接收当前回合变量
- 判断当前阶段
- 顺序调用子工作流
- 合并结果
- 返回统一 JSON

### 开始节点变量

点 `开始节点`，在右侧 `API 参数 -> 管理` 里至少建这些：

- `case_id`
- `simulation_id`
- `current_stage`
- `turn_index`
- `selected_action`
- `branch_focus`
- `case_type`
- `v_case_type`
- `v_case_title`
- `v_case_summary`
- `v_notes`
- `focus_issues_json`
- `claims_json`
- `missing_evidence_json`
- `fact_keywords_json`
- `opponent_arguments_json`
- `opponent_role`
- `opponent_name`
- `likely_arguments_json`
- `likely_evidence_json`
- `likely_strategies_json`

### 节点顺序

正式模式按这个顺序拖节点：

1. 开始节点
2. 代码节点：标准化输入
3. 子工作流节点：`W01`
4. 子工作流节点：`W02`
5. 代码节点：解析上游结果
6. 条件判断节点
7. 子工作流节点：`W03`
8. 子工作流节点：`W04`
9. 代码节点：统一合并结果
10. 回复节点
11. 结束节点

### 你就按这个顺序连线

1. `开始节点 -> 标准化输入代码节点`
2. `标准化输入代码节点 -> W01`
3. `W01 -> W02`
4. `W02 -> 解析上游结果代码节点`
5. `解析上游结果代码节点 -> 条件判断节点`
6. 条件判断节点分 3 条：
   - `prepare / investigation / evidence` 直接去 `统一合并结果`
   - `debate / final_statement` 先去 `W03`，再去 `统一合并结果`
   - `mediation_or_judgment / report_ready` 先去 `W04`，再去 `统一合并结果`
7. `统一合并结果 -> 回复节点 -> 结束节点`

### 第一个代码节点怎么配

点 `标准化输入` 这个代码节点，运行语言选 `Python`，做这 3 件事：

1. 统一把空值补齐
2. 把所有数组字段保证成 JSON 字符串
3. 把要传给 `W01/W02/W03/W04` 的公共变量一次性整理好

### `W01` 工作流节点怎么配

1. 点 `W01` 这个工作流节点
2. 右侧选择引用工作流：`W01_庭审场景生成`
3. 把需要的输入变量一一绑定给它
4. 绑定完成后，确认它能拿到：
   - `current_stage`
   - `selected_action`
   - `branch_focus`
   - 以及场景生成需要的案件基础字段

### `W02` 工作流节点怎么配

1. 点 `W02` 这个工作流节点
2. 选择引用工作流：`W02_法律支持检索`
3. 把案件类型、争议焦点、事实关键词绑定进去

### `解析上游结果` 代码节点怎么配

点这个代码节点，运行语言选 `Python`，只做这 4 件事：

1. 读取 `W01.payload_json`
2. 读取 `W02.payload_json`
3. 把它们解析成对象
4. 显式产出后面要继续绑定的变量：
   - `scene_payload_json`
   - `legal_support_summary`
   - `recommended_laws_json`
   - `recommended_cases_json`
   - `issue_mapping_json`

### 条件判断节点怎么配

点 `条件判断节点`，在右侧直接建 3 条分支：

1. 分支 A：`current_stage` 属于 `prepare, investigation, evidence`
2. 分支 B：`current_stage` 属于 `debate, final_statement`
3. 分支 C：`current_stage` 属于 `mediation_or_judgment, report_ready`

连线规则就是：

- 分支 A 直接去 `统一合并结果`
- 分支 B 去 `W03`
- 分支 C 去 `W04`

### `W03` 工作流节点怎么配

1. 点 `W03` 这个工作流节点
2. 选择引用工作流：`W03_对方行为模拟`
3. 把 `解析上游结果` 代码节点产出的 `legal_support_summary` 绑定进去
4. 再把对方画像变量一并绑定进去

### `W04` 工作流节点怎么配

1. 点 `W04` 这个工作流节点
2. 选择引用工作流：`W04_结果分析复盘`
3. 重点确认这 4 个字段真的绑定给了它：
   - `legal_support_summary`
   - `recommended_laws_json`
   - `recommended_cases_json`
   - `issue_mapping_json`

### `统一合并结果` 代码节点怎么配

点这个代码节点，运行语言选 `Python`，只做这 4 件事：

1. 读取 `W01 / W02 / W03 / W04` 各自的 `payload_json`
2. 解析成对象
3. 按当前阶段把没有执行的模块补成空对象
4. 统一生成最终 `result_json`

### `result_json` 结构固定成这样

```json
{
  "status": "ok",
  "stage": "",
  "scene": {},
  "legal_support": {},
  "opponent": {},
  "analysis": {},
  "degraded_flags": []
}
```

### 回复节点怎么配

点 `回复节点`，让它直接回复 `result_json`。

这样你调用发布 API 时，拿到的就是统一 JSON 字符串。

### 结束节点怎么配

点 `结束节点`，输出变量至少配：

- `status`
- `stage`
- `result_json`

## 12. 当前后端字段怎么送进元器

当前后端字段名还不是元器正式入口字段名。

正式联调前，必须做一次统一适配。

你先记住映射关系：

| 当前后端字段 | 元器入口字段 |
| --- | --- |
| `v_focus_issues` | `focus_issues_json` |
| `v_claims` | `claims_json` |
| `v_missing_evidence` | `missing_evidence_json` |
| `v_opponent_arguments` | `opponent_arguments_json` |
| `focus_issues` | `focus_issues_json` |
| `claims` | `claims_json` |
| `missing_evidence` | `missing_evidence_json` |
| `fact_keywords` | `fact_keywords_json` |
| `likely_arguments` | `likely_arguments_json` |
| `likely_evidence` | `likely_evidence_json` |
| `likely_strategies` | `likely_strategies_json` |
| `opponent_arguments` | `opponent_arguments_json` |

统一规则只有一条：

- 所有数组进元器前先转 JSON 字符串

## 13. 正式调用元器 API 时怎么发

正式模式只调一次 `W00`。

后端流程应该是：

1. 组装当前回合变量
2. 重命名字段
3. 把数组转成 JSON 字符串
4. 调一次元器发布 API

推荐 payload 结构：

```json
{
  "assistant_id": "W00_发布后的_ID",
  "user_id": "demo_user_001",
  "messages": [
    {
      "role": "user",
      "content": "执行企鹅法庭当前回合编排"
    }
  ],
  "custom_variables": {
    "case_id": "case_001",
    "simulation_id": "sim_001",
    "current_stage": "debate",
    "turn_index": "4",
    "selected_action": "强调借条真实性",
    "branch_focus": "evidence_argumentation",
    "v_case_type": "private_lending",
    "v_case_title": "民间借贷纠纷",
    "v_case_summary": "原告主张被告尚未归还借款本金。",
    "focus_issues_json": "[\"是否存在借贷合意\",\"利息是否应支持\"]",
    "claims_json": "[\"请求返还借款本金\",\"请求支付逾期利息\"]",
    "missing_evidence_json": "[\"原始借条\"]",
    "fact_keywords_json": "[\"民间借贷\",\"转账\",\"借条\"]",
    "opponent_arguments_json": "[\"转账并非借款\"]"
  }
}
```

## 14. 你明天最值得先测的 4 条

### 单测 1：`W01`

你要看到：

- 有 `scene_title`
- 有 `scene_text`
- 有 `suggested_actions`
- `speaker_role` 是枚举值

### 单测 2：`W02`

你要看到：

- 得理插件正常返回
- 有 `legal_support_summary`
- 没有 `null`

### 单测 3：`W03`

你要看到：

- 有 `opponent_action`
- 有 `opponent_argument`
- 没有角色乱写

### 正式链路测：`W00`

你要看到：

- `prepare / investigation / evidence` 只跑 `W01 -> W02`
- `debate / final_statement` 跑 `W01 -> W02 -> W03`
- `mediation_or_judgment / report_ready` 跑 `W01 -> W02 -> W04`
- 上游结果能进下游，不断链

## 15. 最容易出错的地方

1. 让 `W01` 直接生成正式 `available_actions`
2. 让 `W04` 不吃 `W02` 结果就开始分析
3. 数组不转 JSON 字符串直接传元器
4. 角色输出自然语言而不是枚举值
5. 把插件占位符写法当成元器后台固定语法
6. `W01/W02/W03/W04` 只配了 `回复节点`，没配 `结束节点`

## 16. 你正式搭的时候就按这个记

你不用再去想“哪份文档看规则，哪份文档看操作”。

正式搭的时候就认这 6 句话：

1. 先建插件
2. 再建 `W01`
3. 再建 `W02`
4. 再建 `W03`
5. 再建 `W04`
6. 最后建 `W00`

然后永远记住：

`正式只调一次 W00，W00 内部顺序调子工作流`

## 17. 一句话结论

你要的“无脑照着做”的正式元器搭法就是：

`插件 -> W01 -> W02 -> W03 -> W04 -> W00 -> 一回合一次 W00 联调`

别再按“每个能力各发一次请求”去理解正式工作流了。

## 18. 官方参考入口

如果你后面发现元器页面文案有轻微变化，就优先回官方帮助中心核下面这几篇：

- 应用模式选择：<https://yuanqi.tencent.com/guide/agent-build-choose-mode>
- 应用标准配置：<https://yuanqi.tencent.com/guide/agent-build-standard-configuration>
- 工作流创建、配置与调试：<https://yuanqi.tencent.com/guide/workflow-create-config-debug>
- 插件创建：<https://yuanqi.tencent.com/guide/plugin-market-create-plugin>

你这份手册就是按上面这几类官方页面的结构重写的。

## 19. 代码节点可直接粘贴版

这一节开始，才是你最关心的“直接粘贴到代码节点里”的部分。

### 19.1 先记住代码节点的 4 条平台规则

根据腾讯元器官方 `代码节点` 帮助页：

1. 函数名保留 `main`
2. 输入输出都按 `dict` 处理
3. 在代码里通过 `params.get("变量名")` 取值
4. 返回值必须能被 JSON 序列化

### 19.2 代码节点统一操作步骤

每一个代码节点你都按这个顺序做：

1. 点代码节点
2. 在右侧先配 `输入变量`
3. 输入变量的变量名，尽量和我下面给你的代码完全一致
4. 点 `添加代码`
5. 整段覆盖粘贴下面代码
6. 点保存
7. 用右上角 `调试`
8. 跑通后点 `一键解析`
9. 确认输出变量名和代码里 `return {}` 的 key 一致

如果你改了输入变量名，代码里对应的 `params.get("...")` 也要一起改。

再记一条来自你导出样例的真实经验：

- 元器在下游引用上游节点输出时，经常会先出现一个 `Output` 根对象
- 所以你在工作流节点、代码节点、大模型节点之间绑定变量时，优先找：
  - `Output`
  - `Output.Content`
  - `Output.payload_json`
  - `Output.result_json`

不要看到我文档里写 `payload_json`，就在页面里死找同名顶层字段。

更稳的找法是：

1. 先点上游节点
2. 看它右侧或变量面板里实际暴露的输出树
3. 优先从 `Output` 根往下找你要的字段

### 19.3 `W01` 第一个代码节点：解析场景输入

这个节点右侧先建这些输入变量：

- `case_id`
- `current_stage`
- `turn_index`
- `selected_action`
- `next_stage`
- `branch_focus`
- `v_case_type`
- `v_case_title`
- `v_case_summary`
- `v_notes`
- `focus_issues_json`
- `claims_json`
- `missing_evidence_json`
- `opponent_arguments_json`

代码直接粘贴：

```python
import json


def _to_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
        return [s]
    return [str(value).strip()]


def main(params: dict) -> dict:
    focus_issues = _to_list(params.get("focus_issues_json"))
    claims = _to_list(params.get("claims_json"))
    missing_evidence = _to_list(params.get("missing_evidence_json"))
    opponent_arguments = _to_list(params.get("opponent_arguments_json"))

    return {
        "case_id": str(params.get("case_id") or ""),
        "current_stage": str(params.get("current_stage") or "prepare"),
        "turn_index": int(params.get("turn_index") or 1),
        "selected_action": str(params.get("selected_action") or ""),
        "next_stage": str(params.get("next_stage") or params.get("current_stage") or "prepare"),
        "branch_focus": str(params.get("branch_focus") or "general"),
        "v_case_type": str(params.get("v_case_type") or ""),
        "v_case_title": str(params.get("v_case_title") or ""),
        "v_case_summary": str(params.get("v_case_summary") or ""),
        "v_notes": str(params.get("v_notes") or ""),
        "focus_issues": focus_issues,
        "claims": claims,
        "missing_evidence": missing_evidence,
        "opponent_arguments": opponent_arguments,
        "focus_issues_text": "；".join(focus_issues) if focus_issues else "暂无争议焦点",
        "claims_text": "；".join(claims) if claims else "暂无明确诉求",
        "missing_evidence_text": "；".join(missing_evidence) if missing_evidence else "暂无明显证据缺口",
        "opponent_arguments_text": "；".join(opponent_arguments) if opponent_arguments else "暂无对方抗辩线索",
    }
```

跑通后你至少要看到这些输出变量：

- `focus_issues`
- `claims`
- `missing_evidence`
- `opponent_arguments`
- `focus_issues_text`
- `claims_text`

### 19.4 `W01` 第二个代码节点：收口场景结果

这个节点右侧先建这些输入变量：

- `llm_output`
- `branch_focus`
- `current_stage`

说明：

- `llm_output` 只是我在这份代码模板里给它起的输入变量名
- 在元器右侧引用来源时，优先去绑定大模型节点的 `Output.Content`
- 不要去绑 `Output.Thought`
- 如果你的页面没直接显示 `Output.Content`，就选那个“模型最终内容文本”的字段

代码直接粘贴：

```python
import json

ROLE_SET = {
    "plaintiff",
    "defendant",
    "applicant",
    "respondent",
    "agent",
    "witness",
    "judge",
    "other",
}


def _to_obj(value):
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return {}
        return json.loads(s)
    return {}


def _to_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
        return [s]
    return [str(value).strip()]


def _norm_role(value):
    role = str(value or "other").strip()
    return role if role in ROLE_SET else "other"


def main(params: dict) -> dict:
    obj = _to_obj(params.get("llm_output"))
    payload = {
        "scene_title": str(obj.get("scene_title") or "当前庭审环节"),
        "scene_text": str(obj.get("scene_text") or ""),
        "speaker_role": _norm_role(obj.get("speaker_role")),
        "suggested_actions": _to_list(obj.get("suggested_actions")),
        "branch_focus": str(obj.get("branch_focus") or params.get("branch_focus") or "general"),
        "next_stage_hint": str(obj.get("next_stage_hint") or params.get("current_stage") or ""),
    }
    return {
        "workflow_key": "courtroom_scene_generation",
        "status": "ok",
        "payload_json": json.dumps(payload, ensure_ascii=False),
    }
```

### 19.5 `W02` 第一个代码节点：生成检索关键词

这个节点右侧先建这些输入变量：

- `case_id`
- `case_type`
- `focus_issues_json`
- `fact_keywords_json`

代码直接粘贴：

```python
import json


def _to_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
        return [s]
    return [str(value).strip()]


def _dedupe(items):
    out = []
    seen = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def main(params: dict) -> dict:
    focus_issues = _to_list(params.get("focus_issues_json"))
    fact_keywords = _to_list(params.get("fact_keywords_json"))
    case_type = str(params.get("case_type") or "")

    candidate_keywords = _dedupe(focus_issues[:2] + fact_keywords[:2])
    if not candidate_keywords:
        default_map = {
            "private_lending": ["民间借贷", "借条", "转账记录"],
            "labor_dispute": ["劳动争议", "解除劳动合同", "工资支付"],
            "divorce_dispute": ["离婚纠纷", "夫妻共同财产", "子女抚养"],
            "tort_liability": ["侵权责任", "损害赔偿", "过错责任"],
        }
        candidate_keywords = default_map.get(case_type, ["民事纠纷", "证据", "争议焦点"])

    candidate_keywords = candidate_keywords[:3]
    law_keyword = candidate_keywords[0]
    case_keyword = candidate_keywords[1] if len(candidate_keywords) > 1 else candidate_keywords[0]

    return {
        "focus_issues": focus_issues,
        "fact_keywords": fact_keywords,
        "candidate_keywords": candidate_keywords,
        "candidate_keywords_json": json.dumps(candidate_keywords, ensure_ascii=False),
        "law_keyword": law_keyword,
        "case_keyword": case_keyword,
    }
```

插件节点绑定规则：

- `search_law.keyword <- law_keyword`
- `search_case.keyword <- case_keyword`

### 19.6 `W02` 第二个代码节点：收口法律支持结果

这个节点右侧先建这些输入变量：

- `llm_output`
- `search_law_raw`
- `search_case_raw`
- `law_info_raw`

说明：

- `llm_output` 这个输入变量，优先绑定大模型节点的 `Output.Content`
- `search_law_raw` 引用 `search_law` 插件节点的输出结果
- `search_case_raw` 引用 `search_case` 插件节点的输出结果
- `law_info_raw` 没接增强节点时可以先删掉这个输入变量，再把代码里对应那一行也删掉

代码直接粘贴：

```python
import json


def _to_obj(value):
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return {}
        try:
            return json.loads(s)
        except Exception:
            return {}
    return {}


def _to_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        return [s]
    return [value]


def main(params: dict) -> dict:
    obj = _to_obj(params.get("llm_output"))
    payload = {
        "legal_support_summary": str(obj.get("legal_support_summary") or ""),
        "recommended_laws": _to_list(obj.get("recommended_laws")),
        "recommended_cases": _to_list(obj.get("recommended_cases")),
        "issue_mapping": _to_list(obj.get("issue_mapping")),
        "missing_points": _to_list(obj.get("missing_points")),
    }
    return {
        "workflow_key": "legal_support_retrieval",
        "status": "ok",
        "payload_json": json.dumps(payload, ensure_ascii=False),
    }
```

### 19.7 `W03` 第一个代码节点：整理对方画像输入

这个节点右侧先建这些输入变量：

- `case_id`
- `current_stage`
- `selected_action`
- `branch_focus`
- `opponent_role`
- `opponent_name`
- `focus_issues_json`
- `claims_json`
- `likely_arguments_json`
- `likely_evidence_json`
- `likely_strategies_json`
- `legal_support_summary`

代码直接粘贴：

```python
import json


def _to_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
        return [s]
    return [str(value).strip()]


def main(params: dict) -> dict:
    likely_arguments = _to_list(params.get("likely_arguments_json"))
    likely_evidence = _to_list(params.get("likely_evidence_json"))
    likely_strategies = _to_list(params.get("likely_strategies_json"))

    return {
        "case_id": str(params.get("case_id") or ""),
        "current_stage": str(params.get("current_stage") or ""),
        "selected_action": str(params.get("selected_action") or ""),
        "branch_focus": str(params.get("branch_focus") or "general"),
        "opponent_role": str(params.get("opponent_role") or "other"),
        "opponent_name": str(params.get("opponent_name") or "对方当事人"),
        "focus_issues": _to_list(params.get("focus_issues_json")),
        "claims": _to_list(params.get("claims_json")),
        "likely_arguments": likely_arguments,
        "likely_evidence": likely_evidence,
        "likely_strategies": likely_strategies,
        "legal_support_summary": str(params.get("legal_support_summary") or ""),
        "likely_arguments_text": "；".join(likely_arguments) if likely_arguments else "暂无明确抗辩预判",
        "likely_evidence_text": "；".join(likely_evidence) if likely_evidence else "暂无明确证据预判",
        "likely_strategies_text": "；".join(likely_strategies) if likely_strategies else "暂无明确策略预判",
    }
```

### 19.8 `W03` 第二个代码节点：收口对方行为结果

这个节点右侧先建这些输入变量：

- `llm_output`
- `opponent_role`

说明：

- `llm_output` 这个输入变量，优先绑定大模型节点的 `Output.Content`

代码直接粘贴：

```python
import json

ROLE_SET = {
    "plaintiff",
    "defendant",
    "applicant",
    "respondent",
    "agent",
    "witness",
    "judge",
    "other",
}


def _to_obj(value):
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return {}
        return json.loads(s)
    return {}


def _to_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
        return [s]
    return [str(value).strip()]


def _norm_role(value):
    role = str(value or "other").strip()
    return role if role in ROLE_SET else "other"


def main(params: dict) -> dict:
    obj = _to_obj(params.get("llm_output"))
    payload = {
        "opponent_role": _norm_role(obj.get("opponent_role") or params.get("opponent_role")),
        "opponent_action": str(obj.get("opponent_action") or ""),
        "opponent_argument": str(obj.get("opponent_argument") or ""),
        "opponent_evidence": _to_list(obj.get("opponent_evidence")),
        "risk_delta": str(obj.get("risk_delta") or ""),
        "next_pressure": str(obj.get("next_pressure") or ""),
    }
    return {
        "workflow_key": "opponent_behavior_simulation",
        "status": "ok",
        "payload_json": json.dumps(payload, ensure_ascii=False),
    }
```

### 19.9 `W04` 第一个代码节点：整理复盘输入

这个节点右侧先建这些输入变量：

- `case_id`
- `case_type`
- `current_stage`
- `turn_index`
- `branch_focus`
- `focus_issues_json`
- `claims_json`
- `missing_evidence_json`
- `opponent_arguments_json`
- `legal_support_summary`
- `recommended_laws_json`
- `recommended_cases_json`
- `issue_mapping_json`
- `opponent_action`
- `opponent_argument`
- `opponent_evidence_json`
- `risk_delta`

代码直接粘贴：

```python
import json


def _to_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        return [s]
    return [value]


def main(params: dict) -> dict:
    focus_issues = _to_list(params.get("focus_issues_json"))
    claims = _to_list(params.get("claims_json"))
    missing_evidence = _to_list(params.get("missing_evidence_json"))
    opponent_arguments = _to_list(params.get("opponent_arguments_json"))
    recommended_laws = _to_list(params.get("recommended_laws_json"))
    recommended_cases = _to_list(params.get("recommended_cases_json"))
    issue_mapping = _to_list(params.get("issue_mapping_json"))
    opponent_evidence = _to_list(params.get("opponent_evidence_json"))

    return {
        "case_id": str(params.get("case_id") or ""),
        "case_type": str(params.get("case_type") or ""),
        "current_stage": str(params.get("current_stage") or ""),
        "turn_index": int(params.get("turn_index") or 1),
        "branch_focus": str(params.get("branch_focus") or "general"),
        "focus_issues": focus_issues,
        "claims": claims,
        "missing_evidence": missing_evidence,
        "opponent_arguments": opponent_arguments,
        "legal_support_summary": str(params.get("legal_support_summary") or ""),
        "recommended_laws": recommended_laws,
        "recommended_cases": recommended_cases,
        "issue_mapping": issue_mapping,
        "opponent_action": str(params.get("opponent_action") or ""),
        "opponent_argument": str(params.get("opponent_argument") or ""),
        "opponent_evidence": opponent_evidence,
        "risk_delta": str(params.get("risk_delta") or ""),
        "focus_issues_text": "；".join([str(x) for x in focus_issues]) if focus_issues else "暂无争议焦点",
        "claims_text": "；".join([str(x) for x in claims]) if claims else "暂无明确诉求",
        "missing_evidence_text": "；".join([str(x) for x in missing_evidence]) if missing_evidence else "暂无明显证据缺口",
    }
```

### 19.10 `W04` 第二个代码节点：收口复盘结果

这个节点右侧先建这些输入变量：

- `llm_output`

说明：

- `llm_output` 这个输入变量，优先绑定大模型节点的 `Output.Content`

代码直接粘贴：

```python
import json


def _to_obj(value):
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return {}
        return json.loads(s)
    return {}


def _to_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        return [s]
    return [value]


def main(params: dict) -> dict:
    obj = _to_obj(params.get("llm_output"))
    payload = {
        "win_rate_estimate": str(obj.get("win_rate_estimate") or ""),
        "issue_assessment": _to_list(obj.get("issue_assessment")),
        "risk_points": _to_list(obj.get("risk_points")),
        "evidence_gaps": _to_list(obj.get("evidence_gaps")),
        "next_steps": _to_list(obj.get("next_steps")),
        "report_markdown": str(obj.get("report_markdown") or ""),
    }
    return {
        "workflow_key": "outcome_analysis_report",
        "status": "ok",
        "payload_json": json.dumps(payload, ensure_ascii=False),
    }
```

### 19.11 `W00` 第一个代码节点：标准化输入

这个节点右侧先建这些输入变量：

- `case_id`
- `simulation_id`
- `current_stage`
- `turn_index`
- `selected_action`
- `branch_focus`
- `case_type`
- `v_case_type`
- `v_case_title`
- `v_case_summary`
- `v_notes`
- `v_focus_issues`
- `v_claims`
- `v_missing_evidence`
- `v_opponent_arguments`
- `focus_issues`
- `claims`
- `missing_evidence`
- `fact_keywords`
- `opponent_arguments`
- `opponent_role`
- `opponent_name`
- `likely_arguments`
- `likely_evidence`
- `likely_strategies`

这个节点的目的，是同时兼容：

- 你当前后端桥接里已经存在的真实字段
- 你在元器主工作流里统一想用的 JSON 字符串字段

代码直接粘贴：

```python
import json


def _first_not_empty(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        if isinstance(value, list) and len(value) == 0:
            continue
        return value
    return None


def _to_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
        return [s]
    return [str(value).strip()]


def _to_json_str(items):
    return json.dumps(items, ensure_ascii=False)


def main(params: dict) -> dict:
    focus_issues = _to_list(_first_not_empty(params.get("focus_issues"), params.get("v_focus_issues")))
    claims = _to_list(_first_not_empty(params.get("claims"), params.get("v_claims")))
    missing_evidence = _to_list(_first_not_empty(params.get("missing_evidence"), params.get("v_missing_evidence")))
    opponent_arguments = _to_list(_first_not_empty(params.get("opponent_arguments"), params.get("v_opponent_arguments")))
    fact_keywords = _to_list(params.get("fact_keywords"))
    likely_arguments = _to_list(params.get("likely_arguments"))
    likely_evidence = _to_list(params.get("likely_evidence"))
    likely_strategies = _to_list(params.get("likely_strategies"))

    case_type = str(_first_not_empty(params.get("case_type"), params.get("v_case_type")) or "")

    return {
        "case_id": str(params.get("case_id") or ""),
        "simulation_id": str(params.get("simulation_id") or ""),
        "current_stage": str(params.get("current_stage") or "prepare"),
        "turn_index": int(params.get("turn_index") or 1),
        "selected_action": str(params.get("selected_action") or ""),
        "next_stage": str(params.get("current_stage") or "prepare"),
        "branch_focus": str(params.get("branch_focus") or "general"),
        "case_type": case_type,
        "v_case_type": str(params.get("v_case_type") or case_type),
        "v_case_title": str(params.get("v_case_title") or ""),
        "v_case_summary": str(params.get("v_case_summary") or ""),
        "v_notes": str(params.get("v_notes") or ""),
        "focus_issues_json": _to_json_str(focus_issues),
        "claims_json": _to_json_str(claims),
        "missing_evidence_json": _to_json_str(missing_evidence),
        "fact_keywords_json": _to_json_str(fact_keywords),
        "opponent_arguments_json": _to_json_str(opponent_arguments),
        "likely_arguments_json": _to_json_str(likely_arguments),
        "likely_evidence_json": _to_json_str(likely_evidence),
        "likely_strategies_json": _to_json_str(likely_strategies),
        "opponent_role": str(params.get("opponent_role") or "other"),
        "opponent_name": str(params.get("opponent_name") or "对方当事人"),
    }
```

### 19.12 `W00` 第二个代码节点：解析 `W01/W02` 上游结果

这个节点右侧先建这些输入变量：

- `w01_payload_json`
- `w02_payload_json`

说明：

- `w01_payload_json` 的数据来源，引用 `W01` 工作流节点的 `payload_json`
- `w02_payload_json` 的数据来源，引用 `W02` 工作流节点的 `payload_json`

代码直接粘贴：

```python
import json


def _to_obj(value):
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return {}
        try:
            return json.loads(s)
        except Exception:
            return {}
    return {}


def main(params: dict) -> dict:
    scene_obj = _to_obj(params.get("w01_payload_json"))
    legal_obj = _to_obj(params.get("w02_payload_json"))

    return {
        "scene_payload_json": json.dumps(scene_obj, ensure_ascii=False),
        "legal_payload_json": json.dumps(legal_obj, ensure_ascii=False),
        "legal_support_summary": str(legal_obj.get("legal_support_summary") or ""),
        "recommended_laws_json": json.dumps(legal_obj.get("recommended_laws") or [], ensure_ascii=False),
        "recommended_cases_json": json.dumps(legal_obj.get("recommended_cases") or [], ensure_ascii=False),
        "issue_mapping_json": json.dumps(legal_obj.get("issue_mapping") or [], ensure_ascii=False),
        "missing_points_json": json.dumps(legal_obj.get("missing_points") or [], ensure_ascii=False),
    }
```

### 19.13 `W00` 第三个代码节点：统一合并结果

这个节点右侧先建这些输入变量：

- `current_stage`
- `scene_payload_json`
- `legal_payload_json`
- `w03_payload_json`
- `w04_payload_json`

说明：

- `w03_payload_json` 引用 `W03` 工作流节点的 `payload_json`
- `w04_payload_json` 引用 `W04` 工作流节点的 `payload_json`
- 如果某条分支没执行，对应值可能是空，这段代码已经做了兜底

代码直接粘贴：

```python
import json


def _to_obj(value):
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return {}
        try:
            return json.loads(s)
        except Exception:
            return {}
    return {}


def main(params: dict) -> dict:
    stage = str(params.get("current_stage") or "")
    scene_obj = _to_obj(params.get("scene_payload_json"))
    legal_obj = _to_obj(params.get("legal_payload_json"))
    opponent_obj = _to_obj(params.get("w03_payload_json"))
    analysis_obj = _to_obj(params.get("w04_payload_json"))

    degraded_flags = []
    if not scene_obj:
        degraded_flags.append("scene_missing")
    if not legal_obj:
        degraded_flags.append("legal_support_missing")

    result = {
        "status": "ok",
        "stage": stage,
        "scene": scene_obj,
        "legal_support": legal_obj,
        "opponent": opponent_obj if stage in {"debate", "final_statement"} else {},
        "analysis": analysis_obj if stage in {"mediation_or_judgment", "report_ready"} else {},
        "degraded_flags": degraded_flags,
    }

    return {
        "status": "ok",
        "stage": stage,
        "result_json": json.dumps(result, ensure_ascii=False),
    }
```

## 20. `W00` 子工作流节点绑定总表

这张表非常重要。你不要自己临场猜字段名，直接按这个绑。

### 20.1 `W00 -> W01`

| `W01` 输入变量 | `W00` 数据来源 |
| --- | --- |
| `case_id` | `标准化输入.case_id` |
| `current_stage` | `标准化输入.current_stage` |
| `turn_index` | `标准化输入.turn_index` |
| `selected_action` | `标准化输入.selected_action` |
| `next_stage` | `标准化输入.next_stage` |
| `branch_focus` | `标准化输入.branch_focus` |
| `v_case_type` | `标准化输入.v_case_type` |
| `v_case_title` | `标准化输入.v_case_title` |
| `v_case_summary` | `标准化输入.v_case_summary` |
| `v_notes` | `标准化输入.v_notes` |
| `focus_issues_json` | `标准化输入.focus_issues_json` |
| `claims_json` | `标准化输入.claims_json` |
| `missing_evidence_json` | `标准化输入.missing_evidence_json` |
| `opponent_arguments_json` | `标准化输入.opponent_arguments_json` |

### 20.2 `W00 -> W02`

| `W02` 输入变量 | `W00` 数据来源 |
| --- | --- |
| `case_id` | `标准化输入.case_id` |
| `case_type` | `标准化输入.case_type` |
| `focus_issues_json` | `标准化输入.focus_issues_json` |
| `fact_keywords_json` | `标准化输入.fact_keywords_json` |

### 20.3 `W00 -> W03`

| `W03` 输入变量 | `W00` 数据来源 |
| --- | --- |
| `case_id` | `标准化输入.case_id` |
| `current_stage` | `标准化输入.current_stage` |
| `selected_action` | `标准化输入.selected_action` |
| `branch_focus` | `标准化输入.branch_focus` |
| `opponent_role` | `标准化输入.opponent_role` |
| `opponent_name` | `标准化输入.opponent_name` |
| `focus_issues_json` | `标准化输入.focus_issues_json` |
| `claims_json` | `标准化输入.claims_json` |
| `likely_arguments_json` | `标准化输入.likely_arguments_json` |
| `likely_evidence_json` | `标准化输入.likely_evidence_json` |
| `likely_strategies_json` | `标准化输入.likely_strategies_json` |
| `legal_support_summary` | `解析上游结果.legal_support_summary` |

### 20.4 `W00 -> W04`

| `W04` 输入变量 | `W00` 数据来源 |
| --- | --- |
| `case_id` | `标准化输入.case_id` |
| `case_type` | `标准化输入.case_type` |
| `current_stage` | `标准化输入.current_stage` |
| `turn_index` | `标准化输入.turn_index` |
| `branch_focus` | `标准化输入.branch_focus` |
| `focus_issues_json` | `标准化输入.focus_issues_json` |
| `claims_json` | `标准化输入.claims_json` |
| `missing_evidence_json` | `标准化输入.missing_evidence_json` |
| `opponent_arguments_json` | `标准化输入.opponent_arguments_json` |
| `legal_support_summary` | `解析上游结果.legal_support_summary` |
| `recommended_laws_json` | `解析上游结果.recommended_laws_json` |
| `recommended_cases_json` | `解析上游结果.recommended_cases_json` |
| `issue_mapping_json` | `解析上游结果.issue_mapping_json` |

注意：

- v1 正式主链里，`W04` 先只依赖法律支持和案件基础字段
- `opponent_action / opponent_argument / opponent_evidence_json / risk_delta` 这 4 个增强字段先不做正式绑定
- 以后如果你要做跨回合记忆，再由后端把上一回合的对方行为结果重新塞进 `custom_variables`

## 21. 首轮调试时你必须盯住的返回值

### 21.1 调 `W01`

至少确认：

- `payload_json` 能被 JSON 解析
- `speaker_role` 落在枚举集里
- `suggested_actions` 是数组，不是字符串

### 21.2 调 `W02`

至少确认：

- 插件节点没报认证错
- `search_law` 和 `search_case` 真的有返回
- `legal_support_summary` 不是空
- `recommended_laws` 和 `recommended_cases` 不是 `null`

### 21.3 调 `W03`

至少确认：

- `opponent_role` 没乱出中文自然语言
- `opponent_evidence` 是数组
- `risk_delta` 有明确倾向描述

### 21.4 调 `W04`

至少确认：

- 它吃到了 `legal_support_summary`
- `win_rate_estimate` 不是空
- `evidence_gaps` 和 `risk_points` 不是空数组

### 21.5 调 `W00`

至少确认：

- `prepare / investigation / evidence` 阶段，`result_json.analysis` 为空对象
- `debate / final_statement` 阶段，`result_json.opponent` 不为空
- `mediation_or_judgment / report_ready` 阶段，`result_json.analysis` 不为空
- `degraded_flags` 没有出现 `scene_missing` 或 `legal_support_missing`

## 22. 当前这版文档还剩哪一层不确定

补到这里后，这份手册已经把：

- 平台按钮入口
- 节点顺序
- 输入参数名
- 输出参数名
- 代码节点可粘贴版
- `W00` 子工作流绑定表

都补齐了。

但我还是只把下面这 2 件事留作“首轮调试确认项”：

1. 你账号里大模型节点和插件节点的“主输出变量”具体显示名
2. 得理接口实际返回 JSON 的字段路径，是否需要你在 `W02` 里再做一层结果清洗

也就是说，现在离“真正可无脑搭”只差最后一步：

- 你照着这份搭第一轮
- 把元器里实际跑出来的 3 张调试截图或 3 段节点输出贴给我
- 我再把这份文档最后那一层变量路径彻底钉死
