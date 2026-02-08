# 基于大语言模型的文本处理辅助系统

> 面向中文文本的轻量级处理工具。以“快速、直观、可复现”为目标，从输入文本到结构化结果提供一条完整可运行的工程链路。

## 简介
本项目包含两条主线能力：
1) **文本处理辅助系统**：对输入文本进行摘要、要点提取、主题/情绪分类、实体抽取、正式改写，并输出结构化 JSON 与 Markdown 报告。
2) **本地知识库问答（RAG）**：对本地 `.md/.txt` 文档建索引，检索相关证据并基于证据回答。

## 环境要求
- Python 3.9+
- 依赖：`openai`、`python-dotenv`
- 需要在 `.env` 中配置 `OPENAI_API_KEY`

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
- 文档切分 → 向量化索引 → 相似度检索
- 证据不足时拒答（阈值门控）
- 返回引用信息（来源文件/片段）

## 目录结构与功能
```
.
├─ app/                 # 核心逻辑
│  ├─ pipeline.py       # 调用 LLM + 解析结果
│  ├─ prompt_loader.py  # prompt 读取/渲染
│  ├─ rag.py            # RAG 逻辑（切分/索引/检索/回答）
│  └─ schemas.py        # 数据结构定义
├─ prompts/             # prompt 模板
│  ├─ extract_all.json.md
│  └─ rag_answer.md
├─ data/                # 示例数据与输出
│  └─ sample.txt
├─ examples/            # 参考脚本（扩展/学习用）
├─ run.py               # 主入口：处理文本并输出结果
├─ eval.py              # 简易评测脚本（基于 tests.jsonl）
├─ qa.py                # 本地知识库问答（RAG）入口
├─ eval_qa.py            # RAG 评测脚本
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
- `eval.py`：文本处理评测脚本
- `eval_qa.py`：RAG 评测脚本
- `prompts/*.md`：prompt 模板

## 快速开始（从零到可运行）
### 1) 配置环境变量
在项目根目录创建/修改 `.env`：
```env
OPENAI_API_KEY=你的key
```

可选（使用代理的同学可以按照我这种的方式试一下，可以解决请求超时问题）：
```env
OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=5
OPENAI_PROXY=http://127.0.0.1:7890（7890替换为你的代理端口）
```

### 2) 安装依赖
```bash
python -m pip install -r requirements.txt
```

### 3) 文本处理（主流程）
准备输入文本：
- `data/sample.txt`

执行：
```bash
python run.py data/sample.txt
```

输出：
- `data/sample.result.json`：结构化结果
- `data/sample.report.md`：可读性报告

### 4) 本地知识库问答（RAG）
准备知识库目录（示例：`data/kb/`，支持 `.md/.txt`）

建库：
```bash
python qa.py index --kb data/kb
```

问答：
```bash
python qa.py ask --question "产品 Alpha 正式发布日期是什么时候？" --topk 5 --threshold 0.35
```

### 5) API 连通性测试（可选）
```bash
python 01_smoke_test.py
```

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
      "chunk_preview": "……"
    }
  ]
}
```

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
请确认已运行 `qa.py index` 建库，并适当调整 `--threshold`。

3) **想更换模型**  
`qa.py` 支持 `--embedding-model` 与 `--model` 参数。  
文本处理模型可在 `app/pipeline.py` 中调整。

4) **请求服务超时/拒绝**

解决方法见配置环境变量处。

## 进一步阅读
- `operate.md`：完整操作文档
- `filefunc.md`：文件功能说明

## 可选扩展
- 增加 `data/tests.jsonl` 的样例集，扩展评测维度（比如关键词命中率）。
- 增加命令行参数（如模型选择、摘要长度、是否生成报告）。
- 增加日志与重试策略说明，提升工程稳定性。
- 将结果写入前端页面或简单 Web UI，做交互式展示。
