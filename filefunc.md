# 文件功能说明（filefunc.md）

本文档按功能域划分，说明项目中每个文件的用途，并明确哪些文件属于：
- 基于大语言模型的文本处理辅助系统
- 本地知识库问答（RAG）

同时给出完整目录树与文件作用说明。

---

## 1. 项目全量目录与文件作用

```
.
├─ .dockerignore              # Docker 构建忽略列表
├─ .env                       # 环境变量（本地配置，不建议提交）
├─ .gitignore                 # Git 忽略规则
├─ 01_smoke_test.py           # OpenAI API 连通性测试脚本
├─ AGENTS.md                  # 项目执行/协作规则
├─ client.py                  # OpenAI 客户端初始化（读取环境变量、超时、重试）
├─ config.py                  # dotenv 加载与环境变量校验
├─ Dockerfile                 # Docker 构建配置
├─ eval.py                    # 文本处理评测脚本（基于 tests.jsonl）
├─ eval_qa.py                 # RAG 评测脚本
├─ llmproj_test.ipynb         # 实验/测试 Notebook
├─ operate.md                 # 操作文档（本次新增）
├─ project_analysis.md        # 项目分析文档
├─ qa.py                      # RAG 命令行入口（建库/问答）
├─ README.md                  # 项目说明
├─ reproduce.ps1              # 复现/运行辅助脚本（PowerShell）
├─ requirements.txt           # Python 依赖列表
├─ run.py                     # 文本处理主入口脚本
├─ tool.py                    # Notebook 辅助工具（封装 get_completion）
├─ app/                       # 核心逻辑
│  ├─ pipeline.py             # 文本处理主流程
│  ├─ prompt_loader.py        # prompt 读取/渲染工具
│  ├─ rag.py                  # RAG 核心逻辑
│  └─ schemas.py              # 数据结构定义
├─ data/                      # 示例数据/输出/索引
│  ├─ chunks.json             # KB 切分后的 chunk 列表
│  ├─ eval_qa.jsonl            # RAG 评测数据集
│  ├─ sample.report.md        # 文本处理输出报告示例
│  ├─ sample.result.json      # 文本处理输出结构化结果示例
│  ├─ sample.txt              # 文本处理输入示例
│  ├─ tests.jsonl             # 文本处理评测数据集
│  ├─ index/                  # 向量索引输出目录
│  │  └─ embeddings.jsonl      # 向量索引数据
│  └─ kb/                     # 本地知识库示例文件
│     ├─ company_policy.md     # 公司政策示例
│     ├─ handbook.md           # 员工手册示例
│     ├─ ops_notes.txt         # 运维/事故记录示例
│     └─ product_alpha.txt     # 产品文档示例
├─ docs/                      # 其它文档/说明
├─ examples/                  # 示例脚本
├─ prompts/                   # prompt 模板
│  ├─ extract_all.json.md      # 文本处理 prompt
│  └─ rag_answer.md            # RAG 回答 prompt
└─ __pycache__/               # Python 字节码缓存
```

---

## 2. 功能域划分

### 2.1 基于大语言模型的文本处理辅助系统（Text Processing）

**核心文件**
- `run.py`：文本处理主入口
- `app/pipeline.py`：核心处理逻辑
- `app/schemas.py`：数据结构定义
- `prompts/extract_all.json.md`：任务 prompt

**相关文件**
- `eval.py`：文本处理评测脚本
- `data/sample.txt`：示例输入
- `data/sample.result.json`：示例输出（结构化）
- `data/sample.report.md`：示例输出（报告）
- `data/tests.jsonl`：评测数据

**支撑文件（共用）**
- `client.py`、`config.py`：OpenAI 客户端与环境变量
- `app/prompt_loader.py`：prompt 渲染工具
- `requirements.txt`：依赖
- `.env`：API Key 配置

---

### 2.2 本地知识库问答（RAG）

**核心文件**
- `qa.py`：RAG 命令行入口（建库/问答）
- `app/rag.py`：RAG 核心流程（切分、向量化、检索、回答）
- `prompts/rag_answer.md`：RAG 回答 prompt

**相关文件**
- `eval_qa.py`：RAG 评测脚本
- `data/kb/`：本地知识库样例
- `data/index/embeddings.jsonl`：向量索引输出
- `data/chunks.json`：切分结果
- `data/eval_qa.jsonl`：RAG 评测数据

**支撑文件（共用）**
- `client.py`、`config.py`：OpenAI 客户端与环境变量
- `app/prompt_loader.py`：prompt 渲染工具
- `requirements.txt`：依赖
- `.env`：API Key 配置

