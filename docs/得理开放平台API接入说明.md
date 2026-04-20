# 得理开放平台 API 接入说明

> 依据文档：[服创赛D06赛道帮助指引.docx](/E:/lawai/服创赛D06赛道帮助指引.docx)  
> 适用范围：企鹅法庭项目的案例检索、法规检索与法规详情获取

## 1. 结论

根据 D06 帮助指引，得理开放平台当前对参赛作品开放的核心法律原子能力主要有两个：

- 类案检索
- 法规检索

另外文档还给出了法规详情接口，适合在法规检索命中后进一步拉取完整法规内容。

帮助指引明确说明：

- 参赛同学无需额外注册开放平台账号即可访问测试库
- 可直接使用指引文档中给出的 `appid` 和 `secret`
- 可通过 `腾讯元器` 工作流调用，也可通过后端代码直接调用
- 在正式赛题口径中，`得理开放平台API` 属于官方允许使用的 6 项开发工具之一，不应被表述成普通外部增强接口

## 2. 接口清单

## 2.1 类案检索

- Method: `POST`
- URL: `https://openapi.delilegal.com/api/qa/v3/search/queryListCase`

用途：

- 根据关键词数组或案情语义，检索相关案例
- 用于支撑：
  - 对方行为模拟
  - 胜诉率分析
  - 类案参考输出

## 2.2 法规检索

- Method: `POST`
- URL: `https://openapi.delilegal.com/api/qa/v3/search/queryListLaw`

用途：

- 根据关键词或语义检索法规
- 用于支撑：
  - 报告中的法条依据
  - 庭前备战建议中的法律引用
  - 立法沙盘的法规背景分析

## 2.3 法规详情

- Method: `GET`
- URL Pattern: `https://openapi.delilegal.com/api/qa/v3/search/lawInfo?lawId=<LAW_ID>&merge=true`

用途：

- 在法规检索列表返回基础信息后，进一步拉取法规正文
- 适合在报告生成阶段补全文本引用和法规详情摘要

## 3. 认证方式

帮助指引里给出的测试库调用方式是通过请求头传递：

- `appid`
- `secret`

建议在项目中统一使用环境变量，不要把文档中的测试凭据硬编码到代码库里。

推荐环境变量命名：

```env
DELILEGAL_APP_ID=
DELILEGAL_APP_SECRET=
DELILEGAL_BASE_URL=https://openapi.delilegal.com
```

说明：

- `DELILEGAL_APP_ID` 和 `DELILEGAL_APP_SECRET` 的值直接取自帮助指引原文
- 团队成员本地开发时各自配置 `.env`
- 若后续赛事方或平台方更新测试凭据，只需替换环境变量

## 4. 推荐接入位置

## 4.1 元器工作流中接入

按 D06 帮助指引，智能体工作流编排推荐使用元器，因此得理 API 的主展示链路建议如下：

- 在元器里通过【工具】节点调用得理 API
- 通过【代码】节点完成参数转换
- 通过【大模型】节点完成案例/法规结果分析
- 通过【变量聚合】解决多分支输出中的 `null`
- 通过【回复】节点统一输出

推荐分工：

- 元器：负责展示型法律检索链路
- 后端：负责兜底调用、缓存、数据归档和报告拼装

## 4.2 后端代码中接入

后端建议建立统一服务：

- `apps/api/app/services/legal_retrieval_service.py`

其职责：

- 统一封装类案检索、法规检索、法规详情
- 统一追加请求头
- 统一超时与错误处理
- 将返回结果转换成项目内部结构
- 在外部接口失败时切换本地规则库

## 5. 请求体设计建议

## 5.1 类案检索请求

帮助指引强调 `keywordArr` 是 `字符串数组`，不是单字符串。

推荐后端请求体结构：

```json
{
  "pageNo": 1,
  "pageSize": 5,
  "sortField": "correlation",
  "sortOrder": "desc",
  "condition": {
    "keywordArr": ["上班途中车祸工伤案例"]
  }
}
```

注意：

- `keywordArr` 必须是 `["..."]`
- 若用户输入是字符串，必须先转换成字符串数组
- 在元器中可通过代码节点处理
- 在后端中可通过统一 helper 处理

## 5.2 法规检索请求

推荐后端请求体结构：

```json
{
  "pageNo": 1,
  "pageSize": 5,
  "sortField": "correlation",
  "sortOrder": "desc",
  "condition": {
    "keywords": ["深圳市房地产相关的法律规定有哪些？"],
    "fieldName": "semantic"
  }
}
```

注意：

- `keywords` 同样建议统一处理成字符串数组
- `fieldName` 可选：
  - `title`
  - `semantic`

## 6. 本项目中的实际调用策略

针对企鹅法庭，建议这样用：

### 案件录入后

- 用法规检索补齐相关法条方向
- 用类案检索补齐典型争议焦点和裁判要点

### 庭审模拟过程中

- 当触发关键争议时，调用类案检索，为：
  - 对方行为模拟
  - 胜诉率分析
  提供依据

### 报告生成阶段

- 用法规检索输出法条依据列表
- 必要时用法规详情接口补足正文内容摘要

## 7. 错误与风险点

## 7.1 ArrayString 问题

D06 帮助指引明确提到，在元器工作流中如果 API 参数要求 `[str]`，但实际传了 `str`，会出现 `ArrayString` 相关错误。

解决策略：

- 后端中统一把单字符串包成数组
- 元器中统一增加代码节点进行类型转换

## 7.2 多分支输出 null

帮助指引明确提到，多分支路径中部分节点没有值时，直接回复会出现 `null`。

解决策略：

- 元器工作流使用变量聚合节点
- 后端聚合时统一过滤空字段

## 7.3 测试库限制

当前文档提供的是测试库能力，项目应把它定位成：

- 用于 MVP 开发验证
- 用于答辩演示的法律检索增强

不要在对外表述里夸大为完整商用案例平台接入。

## 8. 推荐工程约束

- 不在 git 中提交真实的 `.env`
- 在 `.env.example` 中只保留变量名
- 所有请求头拼装只在一个服务层做
- 所有接口响应都先转内部 schema 再给上层使用
- API 调用必须有超时、重试和本地规则库兜底

## 9. 本项目建议的环境变量模板

```env
DELILEGAL_BASE_URL=https://openapi.delilegal.com
DELILEGAL_APP_ID=
DELILEGAL_APP_SECRET=
DELILEGAL_TIMEOUT_SECONDS=12
DELILEGAL_CASE_SEARCH_PATH=/api/qa/v3/search/queryListCase
DELILEGAL_LAW_SEARCH_PATH=/api/qa/v3/search/queryListLaw
DELILEGAL_LAW_INFO_PATH=/api/qa/v3/search/lawInfo
```

## 10. 最终建议

对于企鹅法庭项目，得理 API 不应被当作“顺手加一下”的外部增强，而应被定义为：

`元器工作流和后端规则层之间的法律事实与法规依据来源`

这样它才能在：

- 创新性表达
- 法律专业性
- 胜诉率分析可信度
- 报告可解释性

这四个方面真正发挥作用。
