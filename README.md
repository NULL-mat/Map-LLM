# Map-LLM 智能制图系统

[在线项目展示](https://map-llm-showcase.pages.dev/)

Map-LLM 是一个自然语言驱动的 GIS 制图工作台。用户描述制图目标，Agent
负责理解需求和规划步骤，本地 GIS 工具负责读取空间数据、执行空间处理和
渲染地图。生成结果会保存为可继续修改的地图状态，而不是一次性图片。

> 本仓库是用于公开展示的版本。真实业务数据、训练权重和依赖内部环境的
> 算法实现不随仓库分发；完整实现保存在私有仓库中。

## 系统主线

```text
自然语言请求
    -> Django Web 请求与 Session
    -> ConversationalMappingAgent
    -> LangGraph 流程路由
    -> LangChain Tool Calling / Pydantic Schema
    -> 本地 GIS Tool
    -> GeoPandas / Shapely / Matplotlib
    -> 地图生成或路网综合
    -> MapState、版本与 Tool Trace
    -> 返回结果并支持下一轮修改
```

LLM 只负责理解需求、识别意图和规划工具调用，不直接运行 Python，也不直接
修改地图数据。确定性的 GIS Runtime 负责空间数据处理、样式修改、地图渲染
和状态提交。

## 三项能力

### 单一尺度自动成图

`ConversationalMappingAgent` 从自然语言中提取数据源、图层、样式和地图配置，
再通过 LangChain 工具完成初始化地图、添加图层、设置样式、添加比例尺、指北针
和注记等操作。GeoPandas/Fiona 读取矢量数据，Shapely 处理几何，Matplotlib
完成渲染；图层、样式、范围和版式元素最终写入 `MapState`。

### 多尺度路网综合

路网综合通过统一的 `RoadNetworkGeneralizationEngine` 接收算法、尺度和保留比例，
返回综合结果与统计信息。Stroke、网眼密度和层次选取等通用算法代码保留为
可阅读的接口示例；GCNN 在公开版中只保留 `GCNNSelector` 合约，训练数据、模型
权重和推理实现由私有部署注入。公开版不会伪造 GCNN 结果，调用时会明确提示
缺少私有适配器。

### 多轮动态调整

用户可以在已有地图上继续说“把道路改成黄色”“增加比例尺”或“调整标题”。
流程为：

```text
加载当前 MapState
    -> IntentAnalysisV2（结构化意图）
    -> 当前状态与参数校验
    -> AdjustmentPatch / PatchOperation
    -> 白名单操作执行
    -> 重新渲染
    -> 保存新版本
```

`AdjustmentPatch` 由 Python 根据已校验的意图编译生成，LLM 不直接生成可执行
代码。每个版本保存父版本关系，历史状态可直接加载用于恢复。

## Agent 分层

| 层 | 作用 |
| --- | --- |
| Django Web | 登录、会话、地图请求、历史结果和下载接口 |
| `ConversationState` | 保存消息、意图、任务类型、错误和流程节点信息 |
| LangGraph | 管理创建、修改、查询、确认和错误处理的条件路由 |
| LangChain | 接入模型、绑定 Schema、处理 Tool Calling 与工具结果 |
| LLM | 解析自然语言并规划下一步，不直接执行 GIS 操作 |
| GIS Tool / Runtime | 读取数据、执行空间计算、修改样式并渲染地图 |
| `MapState` | 保存图层、配置、版式元素、综合结果和版本信息 |
| SQLite 状态层 | 持久化 Session、MapState、图层、注记和版本关系 |

## 工程边界与可靠性

- `IntentAnalysisV2`、`MapState`、`AdjustmentPatch` 使用 Pydantic 进行结构校验。
- 意图解析失败时，Agent 使用规则路径作为后备，并把错误返回到对话层。
- 工具输入错误、数据文件不存在、渲染异常会返回结构化失败结果并写入 Tool Trace。
- 修改在状态副本上执行，只有生成有效修改记录后才创建新版本。
- 历史版本采用完整快照，恢复时不需要让 LLM 推导反向操作。
- GCNN 依赖私有模型和数据，公开版本采用失败即提示的策略，避免静默替换算法。

## 本地运行

### 环境

- Python 3.9+
- GeoPandas、Shapely、Matplotlib、LangChain、LangGraph 等依赖
- 如果使用 LLM，需要兼容 Tool Calling 的模型服务

### 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py check
python manage.py runserver
```

访问：

- 地图工作台：`http://127.0.0.1:8000/mapping/`
- 项目展示：`http://127.0.0.1:8000/mapping/showcase/`
- 登录：`http://127.0.0.1:8000/accounts/login`
- 管理后台：`http://127.0.0.1:8000/admin/`

### 模型配置

在本地 `.env` 中填写，不要提交该文件：

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

公开仓库不包含任何 API Key、数据库文件、GIS 数据、日志或生成结果。请将
自己的数据目录配置到 `DATA_DIRECTORY_BASE`；`data/` 目录只提供说明文件。

## 目录说明

```text
Map-LLM/
├── accounts/                         # 登录、注册和用户资料
├── mapping/                          # Django 页面、API 和业务模型
├── gis_mapping_agent/
│   ├── agent/                        # 对话式 Agent 与 LangGraph 流程
│   ├── tools/                        # LangChain GIS 工具
│   ├── adjustment/                   # 意图到 AdjustmentPatch 的编译与执行
│   ├── models/                       # MapState 与版本 Schema
│   ├── state/                        # SQLite 状态管理与 Tool Trace
│   ├── rendering/                    # 地图渲染和质量检查
│   └── algorithms/                   # 通用算法示例与私有算法接口
├── cloudflare-showcase/              # Cloudflare Pages 静态展示页
├── static/                           # Django 静态资源与展示素材
├── data/README.md                    # 本地数据目录说明
├── .env.example                      # 脱敏配置模板
└── requirements.txt                  # Python 依赖
```

## 公开版本边界

公开仓库用于说明系统架构、数据流和 Agent/GIS 的职责边界，并提供项目展示页。
以下内容只存在于私有仓库或部署环境：真实 GIS 数据及元数据、训练好的模型权重、
公司内部算法适配器、内部服务地址和运行日志。这样既能复现公开的接口和流程，
也不会把公司的业务资产提交到 GitHub。
