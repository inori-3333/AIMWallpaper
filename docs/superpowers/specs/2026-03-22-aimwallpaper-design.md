# AIMWallpaper 设计文档

> AI 驱动的 Wallpaper Engine 动态壁纸制作工具

## 1. 项目概述

AIMWallpaper 是一个 Web 应用，用户通过自然语言描述需求，AI 自动生成 Wallpaper Engine (WE) 壁纸项目文件。用户提供图片/视频素材，AI 为其添加动态效果（粒子、水波、光效）、交互功能（鼠标跟随、音频响应）以及桌面组件（时钟、天气）。

### 核心理念

- **不操作 WE Editor GUI**，而是直接生成 WE 项目文件（JSON 配置 + 资源文件）
- **从范例中学习**：用户提供已有壁纸项目作为参考，AI 分析其格式和模式
- **知识沉淀**：经过验证的效果模式存入知识库，越用越聪明
- **SceneScript 扩展**：超越范例库的能力天花板，AI 生成 JS 脚本实现自定义效果

### 目标用户

不熟悉 WE Editor 的壁纸爱好者，希望通过自然语言描述即可制作动态壁纸。

## 2. 系统架构

### 2.1 整体架构

系统分为 5 层：

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web UI (React)                           │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  ┌───────────┐  │
│  │ 素材上传  │  │  对话面板     │  │  实时预览  │  │ 知识库管理 │  │
│  └──────────┘  └──────────────┘  └───────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Python Backend (FastAPI)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐    │
│  │  对话管理器       │  │  项目生成器       │  │  预览服务     │    │
│  └─────────────────┘  └─────────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│              AI 引擎层 (可插拔 LLM Provider)                     │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Claude  │  │  GPT    │  │  Ollama  │  │  其他... │          │
│  └─────────┘  └─────────┘  └──────────┘  └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌──────────────┐  ┌──────────────┐  ┌────────────────┐
│  范例分析器    │  │  知识库       │  │ SceneScript    │
│              │  │              │  │ 生成器          │
└──────────────┘  └──────────────┘  └────────────────┘
                              │
┌──────────────┐              ┌──────────────────┐
│  素材存储     │              │  WE 项目输出      │
└──────────────┘              └──────────────────┘
```

### 2.2 核心数据流

1. **用户上传素材** → 存入素材存储
2. **用户输入描述** → 对话管理器解析意图
3. **AI 查询知识库** → 查找匹配的效果模式和参数
4. **知识库不足时** → 分析用户提供的范例项目，提取新模式
5. **遇到不确定字段** → 通过对话向用户确认
6. **生成项目文件** → 组装 JSON + 可选 SceneScript
7. **预览** → 调用 WE CLI 加载壁纸，截图返回给前端
8. **用户反馈** → 多轮迭代调整

## 3. 范例分析器

### 3.1 分析流程

```
用户上传范例 (.pkg 或项目文件夹)
    │
    ▼
1. 文件解包 — .pkg 解压提取，或直接读取项目文件夹
    │
    ▼
2. 结构解析 — 解析 scene.json 中的:
   • objects[] → 图层列表（图片/粒子/声音/模型）
   • effects[] → 每个图层的效果链
   • materials/ → 材质和 shader 参数
   • particles/ → 粒子系统配置
   • scripts/ → SceneScript 脚本
    │
    ▼
3. 模式提取 — AI 分析解析结果，提取可复用模式
    │
    ▼
4. 置信度评估:
   ✅ 高置信度 → 直接沉淀入知识库
   ⚠️ 中置信度 → 沉淀 + 标记待验证
   ❓ 低置信度 → 向用户提问确认
    │
    ▼
5. 沉淀入知识库 或 向用户提问
```

### 3.2 范例管理功能

- **上传范例**：支持 .pkg 文件或直接指定项目文件夹路径
- **范例浏览**：可视化查看范例的图层结构、效果链、参数
- **批量导入**：从 WE 的 workshop 目录批量扫描已下载的壁纸
- **标注功能**：用户可以给范例中的效果添加注释（如"这个效果是下雨"）
- **AI 提问面板**：集中展示 AI 的不确定项，用户批量确认

## 4. 知识库

### 4.1 数据模型

**效果模式表 (effect_patterns)**
- id, name, description, category, tags
- confidence（置信度）, source（来源范例）, verified（是否经用户验证）
- components：效果的完整配置（图层 JSON、粒子配置等）
- params：可调参数及其默认值和取值范围
- embedding：语义向量（用于检索）

**字段知识表 (field_knowledge)**
- path：JSON 字段路径（如 `objects[].effects[].passes[].combos`）
- description：字段含义
- value_type, examples, confidence
- user_note：用户标注的说明

**组合规则表 (composition_rules)**
- rule：效果组合时的约束/注意事项
- source, verified, user_note

**SceneScript 片段表 (script_snippets)**
- name, description, code
- api_used：使用的 SceneScript API 列表
- tags

### 4.2 检索流程

1. **语义检索** — 用户描述 → embedding → 向量匹配知识库中的效果模式
2. **参数映射** — 自然语言描述（"雨量大"）→ 映射到具体参数值（rate=400）
3. **组合规则检查** — 检测已有效果与新增效果之间的兼容性和依赖
4. **生成配置** — 输出完整的图层 JSON + 素材引用

### 4.3 存储技术

- **SQLite** — 结构化数据存储，零部署
- **ChromaDB** — 向量索引，嵌入式，用于语义检索
- **文件系统** — SceneScript 代码片段、素材模板

## 5. 对话流程与项目生成

### 5.1 AI 决策逻辑

```
用户描述一个效果需求
    │
    ▼
知识库检索 → 命中已有模式？
    │            │
    否           是 → 取出模式 + AI 调参 → 组合规则检查 → 生成图层配置
    │
    ▼
范例库中有类似效果？
    │         │
    是        否 → SceneScript 生成（JS 代码）→ 语法验证
    │
    ▼
提取新模式 → 置信度评估 → 需要确认则提问用户 → 更新知识库
```

### 5.2 关键设计决策

- **多轮对话优先**：宁可多问一次也不猜测，避免生成不符合预期的结果
- **增量生成**：每次只修改变化的部分，不重新生成整个项目
- **版本快照**：每次生成保留版本快照，用户说"撤销"可以回到上一步
- **一键导出**：最终壁纸直接复制到 WE 项目目录，打开 WE 即可使用

### 5.3 典型使用案例

用户："我有一张城市夜景图，想加上下雨效果，窗户有暖光闪烁，底部加一个时钟"

1. AI 解析出 3 个子任务：下雨效果、窗户暖光、时钟组件
2. 知识库命中"雨滴效果"（高置信），部分命中"灯光闪烁"（中置信），时钟需要 SceneScript
3. AI 对不确定项提问：雨量大小？时钟格式？窗户区域标注？
4. 用户回答后生成完整项目文件
5. 预览 → 用户反馈"雨再大一点" → 调整参数 → 重新预览
6. 满意后导出到 WE 项目目录

## 6. Web UI 设计

### 6.1 三栏式布局

- **左栏（素材 & 图层）**：拖拽上传素材，图层结构树，范例库管理
- **中央（实时预览）**：通过 WE CLI 渲染壁纸，支持在预览图上标注区域
- **右栏（AI 对话）**：自然语言交互，支持上传、截图标注、撤销

### 6.2 顶部导航

- 项目管理（新建/打开/保存）
- 知识库浏览与编辑
- 设置（AI 模型选择、WE 路径配置等）

## 7. 技术栈

### 7.1 前端

| 技术 | 用途 |
|------|------|
| React 18 + TypeScript | 核心框架 |
| Vite | 构建工具 |
| TailwindCSS | 样式 |
| Zustand | 状态管理 |
| React Query | API 请求/缓存 |
| Monaco Editor | SceneScript 代码查看/编辑 |
| react-dropzone | 素材拖拽上传 |

### 7.2 后端

| 技术 | 用途 |
|------|------|
| Python 3.11+ | 运行时 |
| FastAPI | HTTP + WebSocket |
| Pydantic | 数据校验 / WE JSON Schema 建模 |
| SQLAlchemy + SQLite | 知识库结构化存储 |
| ChromaDB | 向量检索（嵌入式） |
| Pillow | 图片处理 / 缩略图 |
| aiofiles | 异步文件操作 |

### 7.3 AI 引擎层

| 技术 | 用途 |
|------|------|
| LiteLLM | 统一 LLM 调用接口（Claude/GPT/Ollama/...） |
| OpenAI text-embedding-3-small | 云端向量嵌入 |
| sentence-transformers | 本地向量嵌入备选 |

### 7.4 工具链

| 技术 | 用途 |
|------|------|
| wallpaper32.exe -control | WE 壁纸运行时预览 |
| repkg | .pkg 解包 / .tex 转换 |
| pytest | 后端测试 |
| Vitest | 前端测试 |

## 8. 项目目录结构

```
AIMWallpaper/
├── frontend/                    ← React 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatPanel/       ← AI 对话面板
│   │   │   ├── AssetPanel/      ← 素材 & 图层管理
│   │   │   ├── PreviewPanel/    ← 壁纸预览区
│   │   │   └── KnowledgeBase/   ← 知识库管理界面
│   │   ├── stores/              ← Zustand 状态
│   │   ├── api/                 ← 后端 API 调用
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                     ← Python 后端
│   ├── app/
│   │   ├── main.py              ← FastAPI 入口
│   │   ├── api/
│   │   │   ├── chat.py          ← 对话 API (WebSocket)
│   │   │   ├── project.py       ← 项目管理 API
│   │   │   ├── assets.py        ← 素材上传 API
│   │   │   └── knowledge.py     ← 知识库 API
│   │   ├── core/
│   │   │   ├── ai_engine.py     ← LLM 调用 (LiteLLM)
│   │   │   ├── example_analyzer.py  ← 范例分析器
│   │   │   ├── knowledge_base.py    ← 知识库管理
│   │   │   ├── project_generator.py ← WE 项目生成器
│   │   │   ├── scene_builder.py     ← scene.json 组装
│   │   │   ├── script_generator.py  ← SceneScript 生成
│   │   │   └── preview.py           ← WE CLI 预览
│   │   ├── models/              ← Pydantic 数据模型
│   │   │   ├── scene.py         ← WE scene.json Schema
│   │   │   ├── project.py       ← WE project.json Schema
│   │   │   ├── particle.py      ← 粒子系统 Schema
│   │   │   └── effect.py        ← 效果 Schema
│   │   └── db/
│   │       ├── database.py      ← SQLite 连接
│   │       └── models.py        ← SQLAlchemy ORM
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── data/                        ← 运行时数据
│   ├── knowledge.db             ← SQLite 知识库
│   ├── chroma/                  ← ChromaDB 向量存储
│   ├── examples/                ← 用户导入的范例
│   ├── uploads/                 ← 用户上传的素材
│   └── projects/                ← 生成的 WE 壁纸项目
│
├── config.yaml                  ← 全局配置
└── README.md
```

## 9. API 规范

### 9.1 REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/assets/upload` | 上传素材文件（multipart/form-data），返回 asset_id |
| GET | `/api/assets` | 列出当前项目的所有素材 |
| DELETE | `/api/assets/{asset_id}` | 删除素材 |
| POST | `/api/projects` | 新建壁纸项目 |
| GET | `/api/projects` | 列出所有项目 |
| GET | `/api/projects/{project_id}` | 获取项目详情（图层结构、版本历史） |
| POST | `/api/projects/{project_id}/export` | 导出项目到 WE 目录 |
| POST | `/api/projects/{project_id}/preview` | 触发预览，返回截图 URL |
| POST | `/api/projects/{project_id}/undo` | 回退到上一版本快照 |
| POST | `/api/examples/import` | 导入范例（.pkg 或文件夹路径） |
| POST | `/api/examples/scan` | 批量扫描 WE workshop 目录 |
| GET | `/api/examples` | 列出所有已导入的范例 |
| GET | `/api/knowledge/patterns` | 查询知识库中的效果模式 |
| PUT | `/api/knowledge/patterns/{id}/verify` | 用户确认/验证一个效果模式 |
| DELETE | `/api/knowledge/patterns/{id}` | 删除一个效果模式 |
| GET | `/api/knowledge/questions` | 获取 AI 待确认的问题列表 |
| POST | `/api/knowledge/questions/{id}/answer` | 用户回答 AI 的问题 |
| GET | `/api/config` | 获取当前配置 |
| PUT | `/api/config` | 更新配置（AI 模型、WE 路径等） |

### 9.2 WebSocket 对话协议

连接端点：`ws://localhost:8000/ws/chat/{project_id}`

**客户端 → 服务端消息格式：**

```json
{ "type": "user_message", "content": "给这张图加上下雨效果" }
{ "type": "annotation", "region": { "x": 100, "y": 200, "w": 300, "h": 150 }, "label": "窗户区域" }
```

**服务端 → 客户端消息格式：**

```json
{ "type": "ai_message", "content": "好的，我来添加下雨效果。雨量偏大还是偏小？" }
{ "type": "ai_thinking", "content": "正在分析知识库..." }
{ "type": "generation_start", "task": "adding_rain_effect" }
{ "type": "generation_progress", "task": "adding_rain_effect", "progress": 0.6 }
{ "type": "generation_complete", "task": "adding_rain_effect", "preview_url": "/api/projects/1/preview/latest.png" }
{ "type": "ai_question", "question_id": "q1", "content": "这个字段 'controlpoint1' 的值是 [960, 0, 0]，它可能是粒子发射位置。是这样吗？" }
{ "type": "error", "code": "LLM_TIMEOUT", "message": "AI 模型响应超时，请重试" }
```

## 10. 预览机制

### 10.1 WE CLI 预览流程

1. **加载壁纸**：`wallpaper32.exe -control openWallpaper -file "<project_path>/project.json" -playback play`
2. **等待渲染**：等待 2-3 秒让壁纸完成初始化和首帧渲染
3. **截图捕获**：使用 Windows 窗口截图 API（通过 Python `pyautogui` 或 `mss` 库）截取 WE 渲染窗口
4. **返回前端**：将截图保存为 PNG，通过 HTTP 提供给前端展示

### 10.2 预览限制与备选方案

- WE 必须已安装且正在运行（后台模式）
- 预览延迟约 3-5 秒（加载 + 渲染 + 截图）
- 如果 WE 未安装，降级为静态预览：仅显示图层结构和素材缩略图，不渲染动态效果
- 如果 WE 已有壁纸运行中，先保存当前壁纸状态，预览完成后恢复

## 11. SceneScript 生成

### 11.1 API 参考来源

- WE 官方 SceneScript 文档（ECMAScript 2018 子集）
- 从范例壁纸中提取的 SceneScript 代码作为学习素材
- 内置 API 摘要作为 LLM prompt 的一部分（核心 API：`thisScene`、`thisLayer`、`input`、`engine`）

### 11.2 生成与验证流程

1. AI 根据需求生成 SceneScript 代码
2. **语法检查**：通过 `esprima` 或 `acorn`（Node.js）进行 JS 语法解析
3. **API 白名单检查**：确认代码仅调用了已知的 SceneScript API（不允许 `fetch`、`eval` 等）
4. **运行时测试**：将脚本加载到 WE 预览中，检测是否崩溃或报错
5. 如果验证失败，AI 根据错误信息自动修复并重试（最多 3 次）

## 12. 知识库置信度与生命周期

### 12.1 置信度评估标准

| 级别 | 分数范围 | 判定条件 |
|------|---------|----------|
| 高 | 0.8-1.0 | 字段名语义明确（name, visible, scale）；多个范例中重复出现相同结构；与社区文档一致 |
| 中 | 0.5-0.8 | 数值型参数，字段名可识别但取值范围不确定；仅在 1-2 个范例中出现 |
| 低 | 0-0.5 | 未知字段，用途不明；范例间模式冲突；可能有多种含义 |

### 12.2 验证与生命周期

- **自动提升**：中置信度模式被成功用于生成壁纸且用户未报错 → 提升 0.1
- **用户确认**：用户在 AI 提问面板确认 → 直接提升到 0.9+
- **降级/删除**：用户标记为错误 → 降至 0，标记为 deprecated；生成的壁纸用户反馈"效果不对" → 降 0.2
- **清理策略**：confidence < 0.2 且超过 30 天未使用的模式自动归档

## 13. 错误处理

### 13.1 各层错误处理策略

| 层 | 错误场景 | 处理方式 |
|----|---------|---------|
| **前端** | WebSocket 断连 | 自动重连（指数退避），显示"重新连接中..." |
| **前端** | 上传文件过大/格式不支持 | 前端拦截，提示支持的格式和大小限制（图片 <50MB，视频 <500MB） |
| **后端** | LLM API 超时/限流 | 重试 2 次（指数退避），失败后通知前端，用户可切换模型重试 |
| **后端** | LLM 返回无效 JSON | Pydantic 校验失败 → 将错误信息反馈给 LLM 要求修正（最多 3 轮） |
| **后端** | .pkg 解包失败 | 提示用户文件可能损坏或格式不支持，建议改用项目文件夹导入 |
| **后端** | 生成的 scene.json 无效 | Pydantic Schema 校验 → 定位错误字段 → AI 自动修复 |
| **预览** | WE 未安装或 CLI 不可用 | 降级为静态预览模式，提示用户安装 WE 以获得完整预览 |
| **预览** | WE 加载壁纸后崩溃 | 超时检测（10s），终止预览进程，通知用户并提供错误日志 |
| **知识库** | SQLite/ChromaDB 损坏 | 启动时完整性检查，损坏时从备份恢复或重建 |

### 13.2 文件上传安全

- 文件类型白名单：图片（PNG/JPG/BMP/TGA）、视频（MP4/WEBM）、音频（OGG/MP3/WAV）、WE 项目文件（.pkg/.json）
- 文件大小限制：图片 50MB，视频 500MB，音频 50MB，.pkg 200MB
- 文件名清理：移除路径遍历字符，使用 UUID 重命名存储

## 14. 测试策略

### 14.1 后端测试 (pytest)

- **单元测试**：scene_builder（JSON 组装）、knowledge_base（CRUD + 检索）、example_analyzer（解析逻辑）
- **集成测试**：完整的生成流水线（输入描述 → 输出项目文件），使用 mock LLM
- **Schema 验证测试**：生成的 scene.json / project.json 通过 Pydantic 模型校验
- **知识库测试**：效果模式的 CRUD、语义检索精度、置信度生命周期

### 14.2 前端测试 (Vitest)

- **组件测试**：ChatPanel、AssetPanel、PreviewPanel 的渲染和交互
- **API 集成测试**：Mock WebSocket 和 REST API，测试前后端消息流

### 14.3 端到端验证

- 准备一组参考范例壁纸，导入知识库后，用固定的自然语言描述生成壁纸
- 验证输出的项目文件结构完整、JSON 合法、可被 WE 加载

## 15. 设计约束

- **单用户应用**：作为本地工具运行，不考虑多用户并发
- **对话状态**：存储在内存中（Zustand + 后端 session），重启后需新建对话
- **Embedding 模型一致性**：config.yaml 中锁定 embedding 模型，切换模型时需重建向量索引
- **数据库迁移**：使用 Alembic 管理 SQLite schema 变更

## 16. 外部依赖与环境要求

- **Wallpaper Engine**：已安装并可运行（用于预览），路径可配置
- **Python 3.11+**：后端运行时
- **Node.js 18+**：前端构建
- **AI API Key**：至少配置一个 LLM provider（Claude/OpenAI/本地 Ollama）

## 17. 配置文件 (config.yaml)

```yaml
wallpaper_engine:
  path: "E:\\SteamLibrary\\steamapps\\common\\wallpaper_engine"
  exe: "wallpaper32.exe"

ai:
  default_provider: "openai"       # openai / anthropic / ollama
  openai:
    api_key: ""
    model: "gpt-4o"
  anthropic:
    api_key: ""
    model: "claude-sonnet-4-20250514"
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3"

embedding:
  provider: "openai"               # openai / local
  openai:
    model: "text-embedding-3-small"
  local:
    model: "all-MiniLM-L6-v2"

storage:
  data_dir: "./data"
  max_upload_size_mb: 500
  preview_timeout_seconds: 10
```
