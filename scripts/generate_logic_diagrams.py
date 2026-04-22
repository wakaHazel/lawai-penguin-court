import os
import requests

def generate_mermaid_diagram(mmd_content, output_path):
    url = "https://kroki.io/mermaid/png"
    try:
        print(f"Generating diagram: {output_path}")
        # Clean up the MMD content, Kroki is strict about syntax
        clean_mmd = mmd_content.strip()
        response = requests.post(url, data=clean_mmd, headers={'Content-Type': 'text/plain'}, timeout=30)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Saved diagram to {output_path}")
            return True
        else:
            print(f"❌ Failed to generate diagram. Status: {response.status_code}, Msg: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error generating diagram: {e}")
        return False

def main():
    output_dir = "E:/lawai/output/doc/diagrams"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 总体系统四层架构图 (System Architecture Diagram)
    architecture_mmd = """graph TD
    subgraph L1 [前端交互层 Front-End Layer]
        A1[案件录入与卷宗管理]
        A2[沉浸式庭审交互沙盘]
        A3[胜诉率多维可视化分析]
    end

    subgraph L2 [后端控制层 Back-End Control Layer]
        B1[庭审状态机引擎 Checkpoint]
        B2[会话管理与轨迹溯源]
        B3[推演算分与报告生成器]
    end

    subgraph L3 [智能编排层 AI Orchestration Layer]
        C1[腾讯元器 Agent 工作流]
        C2[多智能体协同引擎]
        C3[动态策略对抗推演引擎]
    end

    subgraph L4 [法律工具层 Legal Capabilities Layer]
        D1[得理开放平台 API]
        D2[小理 AI 专业检索]
        D3[法律法规与案例图谱库]
    end

    L1 -->|操作指令 / 状态获取| L2
    L2 -->|状态流转 / 推演请求| L3
    L3 -->|事实核查 / 法律依据| L4
    L4 -->|专业检出结果| L3
    L3 -->|结构化对抗文本| L2
    L2 -->|渲染视图 / 报告数据| L1
    """

    # 2. 核心主干业务流转图 (Core Business Workflow)
    workflow_mmd = """flowchart LR
    S1[1. 案件初始化]
    S2[2. 庭审模拟推演]
    S3[3. 动态质证博弈]
    S4[4. 胜率多维评估]
    S5[5. 全景复盘生成]

    S1 -->|加载预置模板 / 录入| S2
    S2 -->|多节点分支选择| S3
    S3 -->|调用法律检索 / 对手生成| S4
    S4 -->|算法权重结算| S5

    subgraph Detail_S2 [推演阶段拆解]
        A1[法庭调查] --> A2[举证质证] --> A3[法庭辩论] --> A4[最后陈述]
    end
    
    S2 -.-> Detail_S2
    """
    
    generate_mermaid_diagram(architecture_mmd, os.path.join(output_dir, "system_architecture.png"))
    generate_mermaid_diagram(workflow_mmd, os.path.join(output_dir, "core_workflow.png"))

if __name__ == "__main__":
    main()
