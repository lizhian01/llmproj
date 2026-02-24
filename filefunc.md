# 文件功能说明（filefunc.md）

本文档按“职责分层”说明当前仓库各文件/目录的作用，便于维护和二次开发。

## 1. 根目录脚本与配置

| 路径 | 作用 |
|---|---|
| `README.md` | 项目总览、快速开始、接口说明。 |
| `operate.md` | 完整操作手册（安装、启动、联调、排障）。 |
| `filefunc.md` | 本文件，说明各文件职责。 |
| `requirements.txt` | Python 依赖清单（OpenAI/FastAPI/Uvicorn 等）。 |
| `.env` | 本地环境变量（API key、超时、代理等，不应提交）。 |
| `.gitignore` | Git 忽略规则。 |
| `config.py` | `.env` 加载与必需环境变量校验。 |
| `client.py` | OpenAI 客户端初始化（key、base_url、timeout、重试、代理）。 |
| `run.py` | 文本处理 CLI 入口：读文本 -> 调 `app/pipeline.py` -> 输出 JSON/报告。 |
| `qa.py` | RAG CLI 入口：`index` 建库、`ask` 问答。 |
| `01_smoke_test.py` | API/模型连通性快速检查。 |
| `eval.py` | 文本处理评测脚本。 |
| `eval_qa.py` | RAG 评测脚本。 |
| `reproduce.ps1` | Windows 下复现/运行辅助脚本。 |
| `tool.py` | 辅助实验函数。 |
| `PLAN.md` | 规划记录（若存在）。 |
| `project_analysis.md` | 项目分析记录（若存在）。 |

## 2. 算法层（`app/`）

| 路径 | 作用 |
|---|---|
| `app/pipeline.py` | 文本处理核心逻辑：构造 prompt、调用模型、解析 JSON、字段兜底。 |
| `app/rag.py` | RAG 核心算法：文档读取、分段切分、chunk 划分、向量化、检索、拒答判断、答案生成。 |
| `app/prompt_loader.py` | Prompt 模板读取与占位渲染。 |
| `app/schemas.py` | 文本处理结果数据结构定义。 |

### 2.1 `app/rag.py` 关键函数
- `load_kb_files`：读取知识库目录下 `.md/.txt` 文件。
- `split_sections`：按标题切段（空行不再强制分段，避免“标题和列表分离”）。
- `split_with_overlap`：按长度 + overlap 切 chunk。
- `build_index` / `load_index`：写入/读取向量索引与 chunk。
- `retrieve`：向量检索并按相似度排序。
- `should_refuse`：阈值拒答判断。
- `generate_answer`：基于证据调用 LLM 生成答案。

## 3. Prompt 模板（`prompts/`）

| 路径 | 作用 |
|---|---|
| `prompts/extract_all.json.md` | 文本处理任务的提示模板。 |
| `prompts/rag_answer.md` | RAG 回答模板，约束“仅基于证据回答”。 |

## 4. 后端 API 层（`server/`）

### 4.1 入口
| 路径 | 作用 |
|---|---|
| `server/main.py` | FastAPI 应用入口，注册路由、配置 CORS、提供 `/health`。 |

### 4.2 路由层
| 路径 | 作用 |
|---|---|
| `server/api/routers/text.py` | `POST /api/text/process`，调用文本处理流水线。 |
| `server/api/routers/kb.py` | `GET /api/kb/list`、`POST /api/kb/upload`、`POST /api/kb/{kb_id}/index`。 |
| `server/api/routers/rag.py` | `POST /api/rag/ask`，执行检索问答。 |

### 4.3 服务层
| 路径 | 作用 |
|---|---|
| `server/services/paths.py` | 统一路径常量（项目根目录、`data/kbs`、manifest）。 |
| `server/services/manifest.py` | KB manifest 的读写与 upsert。 |
| `server/services/kb_store.py` | kb_id 生成、上传落盘、KB 列表、索引路径管理。 |
| `server/services/rag_service.py` | 面向 API 的 RAG 业务封装（建库、拒答、citations score 输出）。 |

## 5. 前端层（`web/`）

### 5.1 工程配置
| 路径 | 作用 |
|---|---|
| `web/package.json` | 前端依赖与脚本（Vite dev/build）。 |
| `web/vite.config.js` | Vite 配置。 |
| `web/tailwind.config.js` | Tailwind 主题配置（颜色、字体、容器等）。 |
| `web/postcss.config.js` | PostCSS + Tailwind 插件配置。 |
| `web/components.json` | shadcn 风格组件配置描述。 |

### 5.2 页面与逻辑
| 路径 | 作用 |
|---|---|
| `web/src/main.jsx` | 前端入口，挂载 React 应用。 |
| `web/src/App.jsx` | Dashboard 主布局（侧边栏 + 顶栏 + 路由 + Toaster）。 |
| `web/src/routes/TextLab.jsx` | TextLab 页面（输入、处理、结果卡片、JSON/Markdown Tab）。 |
| `web/src/routes/RAGLab.jsx` | RAGLab 页面（KB 管理、问答、分数进度、证据折叠）。 |
| `web/src/lib/api.js` | 统一 fetch 封装，默认请求 `http://localhost:8000`。 |
| `web/src/lib/report.js` | 前端 Markdown 报告拼装逻辑。 |
| `web/src/lib/utils.js` | `cn` 合并类名工具（clsx + tailwind-merge）。 |
| `web/src/index.css` | Tailwind 全局样式与主题变量。 |

### 5.3 UI 组件（`web/src/components/ui/`）
- `button.jsx`：按钮。
- `card.jsx`：卡片容器。
- `input.jsx` / `textarea.jsx`：输入组件。
- `badge.jsx`：状态标识。
- `tabs.jsx`：Tab 容器。
- `accordion.jsx`：折叠面板（用于 citations）。
- `progress.jsx`：进度条（top_score vs threshold）。
- `table.jsx`：高密度表格（KB 列表）。
- `skeleton.jsx`：加载骨架。
- `separator.jsx`：分隔线。
- `label.jsx`：表单标签。

## 6. 数据目录（`data/`）

| 路径 | 作用 |
|---|---|
| `data/sample.txt` | 文本处理示例输入。 |
| `data/sample.result.json` | 文本处理示例输出（结构化）。 |
| `data/sample.report.md` | 文本处理示例输出（报告）。 |
| `data/tests.jsonl` | 文本处理评测数据。 |
| `data/eval_qa.jsonl` | RAG 评测数据。 |
| `data/kb/` | CLI 场景下示例知识库。 |
| `data/index/` | CLI 默认索引输出目录。 |
| `data/chunks.json` | CLI 默认 chunk 输出。 |
| `data/kbs/` | Web KB 数据根目录（上传 raw、index、manifest）。 |

## 7. 运行期文件（自动生成）
- `data/kbs/{kb_id}/raw/`：上传原始文件。
- `data/kbs/{kb_id}/index/`：向量索引。
- `data/kbs/{kb_id}/chunks.json`：切分结果。
- `data/kbs/manifest.json`：KB 元信息。
- `web/dist/`：前端构建产物。

## 8. 维护建议
- 业务逻辑优先在 `app/` 和 `server/services/` 维护，路由层保持薄。
- 新增 API 时同步更新 `README.md` 与 `operate.md`。
- 修改 RAG 切分策略后，必须重建索引。