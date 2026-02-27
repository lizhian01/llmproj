# 文件功能说明（filefunc.md）
本文档按“职责分层”说明当前仓库各文件与目录的作用，便于维护与二次开发。

## 1. 根目录脚本与配置

| 路径 | 作用 |
|---|---|
| `README.md` | 项目总览、快速开始、接口说明与示例。 |
| `operate.md` | 完整操作手册（安装、启动、联调、排障）。 |
| `filefunc.md` | 本文档，说明各文件职责。 |
| `requirements.txt` | Python 依赖清单（OpenAI/FastAPI/Uvicorn 等）。 |
| `.env` | 本地环境变量（API Key、JWT_SECRET、DB_PATH、超时、代理），不应提交。 |
| `.env.example` | 环境变量模板示例（不含真实密钥）。 |
| `.gitignore` | Git 忽略规则（含 `data/app.db` 等运行期文件）。 |
| `config.py` | `.env` 加载与必需环境变量校验。 |
| `client.py` | OpenAI 客户端初始化（key、base_url、timeout、重试、代理）。 |
| `run.py` | 文本处理 CLI 入口：读文本 -> 调 `app/pipeline.py` -> 输出 JSON/报告。 |
| `qa.py` | RAG CLI 入口：`index` 建库、`ask` 问答。 |
| `01_smoke_test.py` | API/模型连通性快速检查。 |
| `eval.py` | 文本处理评测脚本。 |
| `eval_qa.py` | RAG 评测脚本。 |
| `reproduce.ps1` | Windows 下复现/运行辅助脚本。 |
| `tool.py` | 辅助实验函数。 |


## 2. 算法层（`app/`）

| 路径 | 作用 |
|---|---|
| `app/pipeline.py` | 文本处理核心逻辑：构造 prompt、调用模型、解析 JSON、字段兜底。 |
| `app/rag.py` | RAG 核心算法：切分、向量化、检索、拒答判断、答案生成。 |
| `app/prompt_loader.py` | Prompt 模板读取与占位渲染。 |
| `app/schemas.py` | 文本处理结果数据结构定义。 |

## 3. Prompt 模板（`prompts/`）

| 路径 | 作用 |
|---|---|
| `prompts/extract_all.json.md` | 文本处理任务 prompt 模板。 |
| `prompts/rag_answer.md` | RAG 回答模板，约束“仅基于证据回答”。 |

## 4. 后端 API（`server/`）

### 4.1 入口

| 路径 | 作用 |
|---|---|
| `server/main.py` | FastAPI 应用入口，注册路由与 CORS，提供 `/health`。 |

### 4.2 路由层（`server/api/routers/`）

| 路径 | 作用 |
|---|---|
| `server/api/routers/text.py` | `POST /api/text/process` 文本处理；新增 `/api/text/history` 列表与详情。 |
| `server/api/routers/kb.py` | `GET /api/kb/list`、`POST /api/kb/upload`、`POST /api/kb/{kb_id}/index`。 |
| `server/api/routers/rag.py` | `POST /api/rag/ask`；新增 `/api/rag/history` 列表与详情。 |
| `server/api/routers/auth.py` | 账号与鉴权接口（注册/登录/登出/获取用户/删除账户）。 |
| `server/api/deps.py` | 鉴权依赖（解析 Bearer Token，注入当前用户）。 |

### 4.3 服务层（`server/services/`）

| 路径 | 作用 |
|---|---|
| `server/services/paths.py` | 统一路径常量（项目根、`data/kbs`、`app.db`）。 |
| `server/services/db.py` | SQLite 初始化与建表（用户/KB/历史记录）。 |
| `server/services/auth.py` | 密码哈希（PBKDF2）与 JWT 生成/校验。 |
| `server/services/user_store.py` | 用户与 KB 元信息的数据库访问层。 |
| `server/services/manifest.py` | 旧版 KB manifest 读写（遗留）。 |
| `server/services/kb_store.py` | kb_id 生成、上传落盘、按用户隔离的 KB 路径管理。 |
| `server/services/rag_service.py` | 面向 API 的 RAG 封装（用户权限校验、建库、拒答）。 |
| `server/services/history_store.py` | 历史记录存储与查询（SQLite，按用户隔离）。 |

## 5. 前端（`web/`）

### 5.1 工程配置

| 路径 | 作用 |
|---|---|
| `web/package.json` | 前端依赖与脚本（Vite dev/build）。 |
| `web/vite.config.js` | Vite 配置。 |
| `web/tailwind.config.js` | Tailwind 主题配置。 |
| `web/postcss.config.js` | PostCSS + Tailwind 插件配置。 |
| `web/components.json` | shadcn 风格组件配置。 |

### 5.2 页面与逻辑

| 路径 | 作用 |
|---|---|
| `web/src/main.jsx` | 前端入口，挂载 React 应用。 |
| `web/src/App.jsx` | Dashboard 布局（侧边栏、顶栏、路由、Toaster）。 |
| `web/src/routes/Login.jsx` | 登录/注册页。 |
| `web/src/routes/Settings.jsx` | 账户设置与删除入口。 |
| `web/src/routes/TextLab.jsx` | TextLab 页面（输入、处理、结果卡片、JSON/Markdown、历史记录）。 |
| `web/src/routes/RAGLab.jsx` | RAGLab 页面（KB 管理、问答、分数进度、引用证据、历史记录）。 |
| `web/src/lib/api.js` | 统一 fetch 封装（自动携带 Bearer Token）。 |
| `web/src/lib/auth.jsx` | 前端登录态管理（token 存取、登出、401 处理）。 |
| `web/src/lib/report.js` | 前端 Markdown 报告拼装逻辑。 |
| `web/src/lib/utils.js` | `cn` 类名工具（clsx + tailwind-merge）。 |
| `web/src/index.css` | Tailwind 全局样式与主题变量。 |

### 5.3 UI 组件（`web/src/components/ui/`）
- `button.jsx`：按钮
- `card.jsx`：卡片容器
- `input.jsx` / `textarea.jsx`：输入组件
- `badge.jsx`：状态标识
- `tabs.jsx`：Tab 容器
- `accordion.jsx`：折叠面板（citations）
- `progress.jsx`：进度条（top_score vs threshold）
- `table.jsx`：高密度表格（列表展示）
- `skeleton.jsx`：加载骨架
- `separator.jsx`：分隔线
- `label.jsx`：表单标签

## 6. 数据目录（`data/`）

| 路径 | 作用 |
|---|---|
| `data/sample.txt` | 文本处理示例输入。 |
| `data/sample.result.json` | 文本处理示例输出（结构化）。 |
| `data/sample.report.md` | 文本处理示例输出（报告）。 |
| `data/tests.jsonl` | 文本处理评测数据。 |
| `data/eval_qa.jsonl` | RAG 评测数据。 |
| `data/kb/` | CLI 场景示例知识库。 |
| `data/index/` | CLI 默认索引输出目录。 |
| `data/chunks.json` | CLI 默认 chunk 输出。 |
| `data/kbs/` | Web KB 数据目录（按用户隔离）。 |
| `data/app.db` | Web 历史记录与账号数据 SQLite（TextLab/RAGLab）。 |
| `data/history.db` | 旧版历史库（遗留，不再使用）。 |

## 7. 运行期文件（自动生成类文件）
- `data/kbs/{user_id}/{kb_id}/raw/`：上传原始文件
- `data/kbs/{user_id}/{kb_id}/index/`：向量索引
- `data/kbs/{user_id}/{kb_id}/chunks.json`：切分结果
- `data/kbs/manifest.json`：旧版 KB 元信息（遗留）
- `data/app.db`：账号/历史记录存储（可通过 `DB_PATH` 指定）
- `web/dist/`：前端构建产物

## 8. 维护建议
- 新增或修改 API 时同步更新 `README.md` 与 `operate.md`。
- 修改 RAG 切分或索引策略后必须重建索引。
- 需要清空历史记录时，删除 `data/app.db` 或设置新的 `DB_PATH`。
