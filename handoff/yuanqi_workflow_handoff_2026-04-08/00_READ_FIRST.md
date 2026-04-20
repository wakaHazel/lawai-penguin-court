# READ FIRST

If you are taking over the Yuanqi setup for this project, do not import the workflow package first.

Read in this order:

1. `00_先看这里.md`
2. `04_说明/yuanqi_tool_specs.json`
3. `01_可导入包/企鹅法庭元器导入包_正式版.zip`

Core rule:

- the zip package is only the workflow skeleton
- Deli search tools still need to be created manually inside Yuanqi

Recommended order:

1. create `search_case`
2. create `search_law`
3. create `get_law_info`
4. test the three tools
5. import `W00-W04`
6. verify start variables and end outputs manually in Yuanqi UI
7. debug `W02` first
8. debug `W00` last

