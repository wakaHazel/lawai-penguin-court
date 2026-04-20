# 元器工作流交接包

这个目录是给接手元器工作流问题的人准备的，尽量减少她重新找文件和重新定位问题的时间。

目录结构：

- `01_可导入包`
  - `企鹅法庭元器导入包_正式版.zip`
  - `penguin_yuanqi_formal_pkg_ascii`
- `02_脚本`
  - `generate_penguin_yuanqi_formal_package.py`
- `03_参考样例`
  - `yuanqi_user_sample`
  - `yuanqi_sample_base`
- `04_说明`
  - `当前状态说明.md`
  - `快速测试输入_W00.txt`
  - `审计摘要.json`

建议接手顺序：

1. 先看 `04_说明/当前状态说明.md`
2. 再看 `01_可导入包/企鹅法庭元器导入包_正式版.zip`
3. 需要改包时看 `02_脚本/generate_penguin_yuanqi_formal_package.py`
4. 需要对照导出样例时看 `03_参考样例`

当前最重要的结论：

- 业务链路层面的空输出问题已经修过一轮
- 五个工作流的开始参数默认值已经写进 `StartNodeData.WorkflowParams`
- 运行链路里 `answer_text`、回复节点、结束节点引用已经补齐
- 还没有彻底解决的是元器 UI 中“工作流级变量/启动工作流输入变量”面板的识别问题
