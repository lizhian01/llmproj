# 操作文档（operate.md）

本文档面向第一次接触本项目的使用者，说明如何搭建、启动与运行本项目，并给出完整的操作示例与注意事项。

## 1. 项目简介

本项目是一个基于大语言模型（LLM）的中文文本处理辅助系统，提供：
- 文本摘要与要点提取
- 主题/情绪分类
- 关键词与实体抽取
- 正式书面改写
- 本地知识库问答（RAG：检索增强生成）

项目包含两条主线：
1) **文本处理主流程**：输入一段文本，输出结构化结果与可读报告。  
2) **本地知识库问答（RAG）**：对本地文档建立索引，支持基于证据的问答与拒答。

---

## 2. 环境要求

- Python 3.9+
- 操作系统：Windows / macOS / Linux 均可(本人用的Windows11专业版系统)
- 需要网络访问 OpenAI API（其他模型API也可，以下替换即可）
- `.env` 中配置 `OPENAI_API_KEY`

---

## 3. 功能概述

### 3.1 文本处理辅助系统
- 一句话摘要
- 3 条要点列表
- 主题与情绪分类
- 关键词与实体抽取（时间/地点/人物/组织）
- 正式书面改写
- 结构化 JSON 输出 + Markdown 报告

### 3.2 本地知识库问答（RAG）
流程：文档切分 → 向量化索引 → 相似度检索 → 证据驱动回答
- 支持导入本地 `.md/.txt` 目录
- 支持阈值拒答（证据不足时不回答）
- 返回引用信息（来源文件、chunk_id、片段预览）

---

## 4. 依赖安装

在项目根目录执行：

```bash
python -m pip install -r requirements.txt
```

---

## 5. 目录结构（关键部分）

```
.
├─ app/                 # 核心逻辑
│  ├─ pipeline.py       # 文本处理主流程（LLM 调用 + JSON 解析）
│  ├─ schemas.py        # 数据结构定义
│  ├─ prompt_loader.py  # prompt 读取与渲染
│  └─ rag.py            # RAG 相关逻辑（切分/索引/检索/回答）
├─ prompts/             # prompt 模板
│  ├─ extract_all.json.md
│  └─ rag_answer.md
├─ data/                # 示例输入/输出/索引
│  ├─ sample.txt
│  ├─ sample.result.json
│  ├─ sample.report.md
│  ├─ kb/               # 本地知识库示例文件
│  └─ index/            # 向量索引输出
├─ run.py               # 文本处理入口
├─ qa.py                # RAG 命令行入口
├─ eval.py              # 文本处理评测脚本
├─ eval_qa.py           # RAG 评测脚本
├─ client.py            # OpenAI 客户端初始化
├─ config.py            # 环境变量加载
└─ requirements.txt     # 依赖列表
```

---

## 6. 核心文件说明（简要）

- `run.py`：文本处理入口脚本（读取输入文本 → 调用 `app/pipeline.py` → 输出 JSON + 报告）
- `app/pipeline.py`：文本处理主逻辑（加载 prompt、调用模型、解析并补全字段）
- `qa.py`：RAG 命令行入口（建库 / 问答）
- `app/rag.py`：RAG 核心逻辑（切分、嵌入、索引、检索、证据拼接、回答）
- `prompts/extract_all.json.md`：文本处理 prompt 模板
- `prompts/rag_answer.md`：RAG 回答 prompt 模板

---

## 7. 配置与初始化

在项目根目录创建或修改 `.env`：

```env
OPENAI_API_KEY=你的key
```

可选：
```env
OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=5
OPENAI_PROXY=http://127.0.0.1:7890
```

---

## 8. 操作步骤（完整流程）

### 8.1 文本处理（主流程）

1) 准备输入文本  
将文本放在 `data/sample.txt`（或任意路径文件）

2) 执行
```bash
python run.py data/sample.txt
```

3) 查看输出  
- `data/sample.result.json`：结构化结果  
- `data/sample.report.md`：可读性报告

---

### 8.2 本地知识库问答（RAG）

#### (1) 建库 / 建索引

（这里消耗token很多）

将知识库文件放到目录（示例：`data/kb/`），支持 `.md` / `.txt`。

执行：
```bash
python qa.py index --kb data/kb
```

索引输出：
- `data/index/embeddings.jsonl`
- `data/chunks.json`

#### (2) 进行问答
```bash
python qa.py ask --question "产品 Alpha 正式发布日期是什么时候？" --topk 5 --threshold 0.35
```

输出包含：
- `answer`：回答内容  
- `citations`：引用列表（source_file/chunk_id/preview）
- `refused`：是否拒答

#### (3) 评测（可选）
```bash
python eval_qa.py --kb data/kb
```

---

## 9. 示例

### 示例 1：文本处理
```bash
python run.py data/sample.txt
```

输出（简化）：
```json
{
  "summary_short": "...",
  "summary_bullets": ["...", "...", "..."],
  "topic": "科技",
  "sentiment": "正面",
  "keywords": ["...", "..."],
  "entities": {"time": null, "location": null, "people": [], "orgs": []},
  "rewrite_formal": "..."
}
```

### 示例 2：RAG 问答
```bash
python qa.py ask --question "餐补标准是多少？" --topk 5 --threshold 0.35
```

输出（简化）：
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

---

## 10. 常见问题（FAQ）

1) **索引与问答为什么找不到答案？**  
请检查是否已建立索引、`kb` 目录是否有文档、以及问答的 `threshold` 是否过高。

2) **能否更换模型？**  
可以。`qa.py` 的 `--embedding-model` 与 `--model` 支持传入其他模型。

3) **为什么报错 Missing required env var?**  
说明 `.env` 未配置 `OPENAI_API_KEY` 或环境变量未生效。

