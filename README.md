# Map-LLM GIS Mapping Agent

Map-LLM 是一个以自然语言驱动的 GIS 制图 Agent。它负责理解制图目标、规划工具调用，并把空间数据处理、地图渲染、路网综合和多轮修改交给确定性的本地 GIS Runtime 执行。

本公开仓库只保留 Agent、GIS 工具、状态管理和算法接口。真实业务数据、内部算法适配器、模型权重和部署层不在仓库中。

[在线项目展示](https://map-llm-showcase.pages.dev/)

## 工作方式

```text
自然语言请求
    -> ConversationalMappingAgent / ThinkingGISMappingAgent
    -> LangGraph 流程与条件路由
    -> LangChain Tool Calling 与 Pydantic Schema
    -> 本地 GIS 工具
    -> GeoPandas / Shapely / Matplotlib / NetworkX
    -> 地图绘制或路网综合
    -> MapState、SQLite 版本链与 Tool Trace
    -> 返回结果，并支持下一轮增量修改
```

LLM 只负责理解需求、识别意图和规划工具调用；它不会直接运行 Python 或修改地图状态。GIS Runtime 负责读取空间数据、执行计算、渲染结果，并在校验通过后提交状态。

## 核心模块

- `gis_mapping_agent.agent`：思考-行动-观察制图 Agent，以及支持多轮会话的 `ConversationalMappingAgent`。
- `gis_mapping_agent.tools`：地图初始化、图层、样式、比例尺、指北针、注记、路网综合和状态操作工具。
- `gis_mapping_agent.adjustment`：将结构化修改意图校验并编译为白名单 `AdjustmentPatch` / `PatchOperation`。
- `gis_mapping_agent.models` 与 `gis_mapping_agent.specs`：`MapState`、地图配置、综合参数和修改补丁的 Pydantic 模型。
- `gis_mapping_agent.state`：会话上下文、SQLite 状态持久化、版本管理和工具调用追踪。
- `gis_mapping_agent.rendering`：基于 Matplotlib 的地图渲染与结果质量检查。
- `gis_mapping_agent.generalization` 与 `gis_mapping_agent.algorithms`：Stroke、网眼密度、层次选取等路网综合算法，以及可选 GCNN 适配器接口。
- `gis_mapping_agent.gis` 与 `gis_mapping_agent.utils`：空间数据读取、范围计算、路径解析和通用辅助能力。

## 三类制图能力

### 自动制图

Agent 从自然语言提取数据文件、图层和版式要求，按初始化地图、添加图层、设置样式、添加地图元素、保存结果的顺序调用工具。GeoPandas/Fiona 读取矢量数据，Shapely 处理几何，Matplotlib 生成图片，最终配置写入 `MapState`。

### 多尺度路网综合

`RoadNetworkGeneralizationEngine` 接收源比例尺、目标比例尺、算法和可选 `keep_ratio`。Stroke、网眼密度和层次选取算法会根据尺度参数计算综合程度并返回统计结果；GCNN 仅保留公开适配器合约，未配置私有实现时会明确失败，不会静默替换算法。

### 多轮动态修改

每轮修改先加载当前 `MapState`，再由 `IntentAnalysisV2` 解析自然语言。修改引擎校验目标图层和参数，将合法意图编译为受控 Patch，执行局部更新、重新渲染并保存新的完整状态版本。历史版本可以直接加载或回退，不需要让 LLM 推导反向操作。

## 状态与可靠性

- SQLite 保存会话、完整 `MapState` 快照、版本父子关系和修改记录；运行时上下文保存在 `SessionContext`。
- Pydantic Schema 约束工具输入、意图和 Patch 结构，参数错误会在执行前返回失败信息。
- 不存在的图层、缺少数据文件、渲染异常和工具异常会返回结构化错误，并写入 Tool Trace。
- Agent 通过规则路径、结构化意图校验和有限工具迭代控制不确定性；只有有效修改才生成新版本。
- `event_callback` 可选用于宿主程序接收工具进度，核心包本身不依赖 Web 框架。

## 安装

需要 Python 3.9 或更高版本，以及 GeoPandas、Shapely、Matplotlib、LangChain 和 LangGraph 的运行环境。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
copy .env.example .env
```

在 `.env` 中设置兼容 Tool Calling 的模型服务：

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
DATA_DIRECTORY_BASE=data
OUTPUT_DIR=outputs
```

不要提交 `.env`、空间数据、数据库、日志或生成结果。

## 使用示例

```python
from gis_mapping_agent import ConversationalMappingAgent

agent = ConversationalMappingAgent()
created = agent.chat("使用 data/roads.shp 绘制道路地图，线条设置为黄色，添加比例尺")
print(created["message"])

updated = agent.chat("把道路线宽改为 3")
print(updated["message"])
```

需要直接控制思考-行动-观察循环时，可使用 `ThinkingGISMappingAgent`。地图状态默认写入 `outputs/states/map_states.db`，渲染文件写入 `outputs/`。

## 目录

```text
Map-LLM/
├── gis_mapping_agent/
│   ├── agent/              # Agent 与流程编排
│   ├── tools/              # LangChain GIS 工具
│   ├── adjustment/         # 意图到受控 Patch 的编译
│   ├── models/ specs/      # MapState 与结构化 Schema
│   ├── state/              # SQLite、会话上下文和 Trace
│   ├── rendering/          # 地图渲染与质量检查
│   ├── generalization/    # 路网综合引擎
│   ├── algorithms/         # 通用算法与可选 GCNN 接口
│   ├── gis/ utils/         # 数据读取和空间辅助工具
│   └── __init__.py
├── config/                 # 运行参数
├── data/README.md          # 本地数据目录说明
├── cloudflare-showcase/    # 独立静态项目展示页
├── .github/workflows/      # 展示页自动部署到 Cloudflare Pages
├── .env.example            # 配置模板
├── pyproject.toml          # 包元数据与依赖
└── requirements.txt        # 锁定环境依赖
```

## 公开版本边界

公开版用于展示 Agent 的接口、流程和 GIS 工程结构。私有部署可以在不改变 Agent 与工具层契约的情况下注入业务数据、GCNN 模型和内部算法实现。
