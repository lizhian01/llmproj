# 基于大语言模型的文本处理辅助系统

> 面向中文文本的轻量级处理与知识库问答工具。以“快速、直观、可复现、可扩展”为目标，提供 TextLab（文本处理/生成） 与 RagLab（基于知识库的 RAG 问答） 两条能力主线：用户在 Web 端（或CLI均可）输入文本或问题，系统在后端完成模型调用、检索增强与证据组织，输出结构化结果与可追溯引用；同时支持 JWT 登录鉴权与多用户隔离，确保不同账号的历史记录与知识库相互独立，便于作为通用 AI 能力服务接入业务系统。

## 简介
本项目包含两条主线能力：
1) **文本处理辅助系统**：对输入文本进行摘要、要点提取、主题/情绪分类、实体抽取、正式改写，并输出结构化 JSON 与 Markdown 报告。
2) **本地知识库问答（RAG）**：对本地 `.md/.txt` 文档建索引，检索相关证据并基于证据回答。

在此基础上，项目新增了完整 Web 工程封装（优化，非必需）：
- 后端：`FastAPI` REST API（`server/`）
- 前端：`Vite + React + Tailwind + shadcn/ui` 工作台（`web/`）

## 环境要求
- Python 3.9+
- Node.js 18+
- 依赖（后端）：`openai`、`python-dotenv`、`fastapi`、`uvicorn`、`python-multipart`
- 依赖（前端）：`react`、`vite`、`tailwindcss`、`@radix-ui/*`、`sonner` 等（见 `web/package.json`）
- 需要在 `.env` 中配置 `OPENAI_API_KEY` 与 `JWT_SECRET`（Web 登录必需）

## 功能概览
### 文本处理
- 一句话摘要（短句、直观）
- 3 条要点列表（便于快速理解）
- 主题与情绪分类（固定枚举）
- 关键词与实体信息抽取（时间、地点、人、组织）
- 正式书面改写（不添加事实）
- 自动生成：`*.result.json` 与 `*.report.md`

### 本地知识库问答（RAG）
- 导入本地 `.md/.txt` 目录
- 文档切分 -> 向量化索引 -> 相似度检索
- 证据不足时拒答（阈值门控）
- 返回引用信息（来源文件/片段）

### Web 应用（新增）
- **TextLab**：文本输入/上传、卡片化结果展示、JSON/Markdown 双视图
- **RAGLab**：KB 列表、上传、建库、问答、分数进度条、引用证据折叠展示
- **历史记录**：TextLab/RAGLab 最近记录列表与详情查看（后端持久化，刷新不丢失）
- 上传与索引统一落盘：`data/kbs/{user_id}/{kb_id}/...`

## 目录结构与功能
```
.
├─ app/                 # 核心逻辑
│  ├─ pipeline.py       # 调用 LLM + 解析结果
│  ├─ prompt_loader.py  # prompt 读取/渲染
│  ├─ rag.py            # RAG 逻辑（切分/索引/检索/回答）
│  └─ schemas.py        # 数据结构定义
├─ server/              # FastAPI 后端
│  ├─ main.py           # 应用入口、CORS、路由注册
│  ├─ api/routers/      # text/kb/rag 路由
│  └─ services/         # manifest、kb 存储、rag 服务封装
├─ web/                 # 前端工作台
│  ├─ src/routes/       # TextLab / RAGLab 页面
│  ├─ src/components/ui # shadcn 风格组件
│  └─ package.json      # 前端依赖与脚本
├─ prompts/             # prompt 模板
│  ├─ extract_all.json.md
│  └─ rag_answer.md
├─ data/                # 示例数据与输出
│  ├─ sample.txt
│  ├─ kb/               # CLI 示例 KB
│  └─ kbs/              # Web KB 数据
├─ examples/            # 参考脚本
├─ run.py               # 主入口：处理文本并输出结果
├─ eval.py              # 简易评测脚本（基于 tests.jsonl）
├─ qa.py                # 本地知识库问答（RAG）入口
├─ eval_qa.py           # RAG 评测脚本
├─ 01_smoke_test.py     # API 连通性测试
├─ client.py            # OpenAI 客户端初始化
├─ config.py            # 环境变量加载
└─ requirements.txt     # 依赖列表
```

## 核心文件说明
- `app/pipeline.py`：文本处理主流程（调用模型 + JSON 解析 + 兜底字段）
- `run.py`：文本处理入口，生成 `*.result.json` 与 `*.report.md`
- `app/rag.py`：RAG 核心逻辑（切分/索引/检索/证据/回答）
- `qa.py`：RAG 命令行入口（index / ask）
- `server/main.py`：FastAPI 应用入口
- `server/api/routers/*.py`：REST API 路由
- `server/services/*.py`：KB 存储、manifest、RAG 业务封装
- `web/src/routes/TextLab.jsx`：文本处理页面
- `web/src/routes/RAGLab.jsx`：RAG 页面
- `prompts/*.md`：prompt 模板

## 快速开始（从零到可运行）
### 1) 配置环境变量
在项目根目录创建/修改 `.env`（可参考 `.env.example`）：
```env
OPENAI_API_KEY=你的key
```

可选（使用代理可以减少请求超时）：
```env
OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=5
OPENAI_PROXY=http://127.0.0.1:7890（7890替换为你的代理端口）
```

认证与数据库配置（Web 必需）：
```env
JWT_SECRET=your-secret
JWT_EXPIRES_DAYS=7
DB_PATH=data/app.db
HISTORY_LIMIT=100
AUTH_ALLOW_GUEST=false
```


### 2) 安装依赖
后端依赖：
```bash
python -m pip install -r requirements.txt
```

前端依赖：
```bash
cd web
npm install
cd ..
```

### 3) 文本处理（CLI 主流程）
准备输入文本：
- `data/sample.txt`

执行：
```bash
python run.py data/sample.txt
```

输出：
- `data/sample.result.json`：结构化结果
- `data/sample.report.md`：可读性报告

### 4) 本地知识库问答（CLI / RAG）
准备知识库目录（示例：`data/kb/`，支持 `.md/.txt`）

建库：
```bash
python qa.py index --kb data/kb
```

问答：
```bash
python qa.py ask --question "产品 Alpha 正式发布日期是什么时候？" --topk 5 --threshold 0.35
```

### 5) 启动 Web
后端（必须在项目根目录运行）：
```bash
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

前端：
```bash
cd web
npm run dev
```

浏览器访问：`http://localhost:5173`

首次访问请在登录页注册/登录。

### 6) API 连通性测试（可选）
```bash
python 01_smoke_test.py
```

## 鉴权与账号（Web）
- 注册：`POST /api/auth/register`
- 登录：`POST /api/auth/login`
- 业务接口需携带：`Authorization: Bearer <token>`
- 账户信息：`GET /api/auth/me`
- 删除账户：`DELETE /api/auth/me`

## 输出示例（文本处理）
```json
{
  "summary_short": "...",
  "summary_bullets": ["...", "...", "..."],
  "topic": "科技",
  "sentiment": "正面",
  "keywords": ["...", "...", "..."],
  "entities": {"time": null, "location": null, "people": [], "orgs": []},
  "rewrite_formal": "..."
}
```

## 输出示例（RAG）
```json
{
  "question": "餐补标准是多少？",
  "refused": false,
  "answer": "……",
  "top_score": 0.42,
  "threshold": 0.35,
  "citations": [
    {
      "source_file": "company_policy.md",
      "chunk_id": "chunk_000003",
      "chunk_preview": "……",
      "score": 0.42
    }
  ]
}
```

拒答示例：
```json
{
  "question": "……",
  "refused": true,
  "answer": "知识库未覆盖或无法确认。",
  "top_score": 0.12,
  "threshold": 0.35,
  "citations": [],
  "reason": "below_threshold"
}
```

## 历史记录（Web）
- 存储：SQLite `data/app.db`（可用 `DB_PATH` 覆盖）
- 默认保留最近 `HISTORY_LIMIT` 条（默认 100）
- 按用户隔离存储，需登录后访问
- 清空：删除 `data/app.db` 或设置新的 `DB_PATH`

### 历史记录接口
列表：
```http
GET /api/text/history?limit=50
GET /api/rag/history?limit=50
```

详情：
```http
GET /api/text/history/{id}
GET /api/rag/history/{id}
```

TextLab 列表示例：
```json
{
  "limit": 50,
  "items": [
    {
      "id": "c0f9c6...",
      "created_at": "2026-02-26T08:01:12Z",
      "status": "success",
      "input_preview": "……",
      "summary_short": "……",
      "duration_ms": 842
    }
  ]
}
```

RAGLab 详情示例：
```json
{
  "id": "a1d2b3...",
  "created_at": "2026-02-26T08:05:10Z",
  "status": "refused",
  "kb_id": "kb_20260226_...",
  "question": "……",
  "answer": "……",
  "refused": true,
  "top_score": 0.12,
  "threshold": 0.35,
  "citations": [],
  "reason": "below_threshold"
}
```

### 本地验证（历史记录）
1) 启动后端与前端（见 “启动 Web”）。
2) 在 TextLab 或 RAGLab 发起一次请求。
3) 刷新页面，查看“历史记录”列表是否保留。
4) 清空历史：删除 `data/history.db` 或修改 `DB_PATH` 指向新文件。
5) 设置保留条数：设置 `HISTORY_LIMIT`（如 50/100/200）。

## 评估（可选）
文本处理评测：
```bash
python eval.py
```

RAG 评测：
```bash
python eval_qa.py --kb data/kb
```

## 常见问题
1) **Missing required env var**  
未设置 `OPENAI_API_KEY`，请检查 `.env` 是否在项目根目录。

2) **RAG 无法回答/经常拒答**  
请确认已运行建库流程，并适当调整 `--threshold`。

3) **想更换模型**  
`qa.py` 支持 `--embedding-model` 与 `--model` 参数。  
文本处理模型可在 `app/pipeline.py` 中调整。

4) **请求服务超时/拒绝**  
优先检查代理、超时与重试配置（见环境变量部分）。

5) **No module named 'server'**  
通常是你在 `web/` 目录启动了 uvicorn。请回到项目根目录启动后端。

6) **上传后问答无结果**  
请确认：上传完成 -> 对应 `kb_id` 已建索引 -> 再提问。

## 进一步阅读
- `operate.md`：完整操作文档
- `filefunc.md`：文件功能说明

## 可选扩展
- 可接入医疗医疗文献，病例文本，医学指南等知识库信息，实现医疗问答系统（RAG主线）。
- 增加 `data/tests.jsonl` 的样例集，扩展评测维度（比如关键词命中率）。
- 增加命令行参数（如模型选择、摘要长度、是否生成报告）。
- 增加日志与重试策略说明，提升工程稳定性。
- 增加 API 鉴权、用户隔离与审计日志。










