# 基于大语言模型的文本处理辅助系统

> 这是一个面向中文文本的轻量级处理工具。以“快速、直观、可复现”为目标，做了一个从输入文本到结构化结果的完整项目

## 简介
本项目设计并实现了一套基于大语言模型的文本处理辅助系统，系统能够对输入文本进行摘要、要点提取、主题分类、情绪判断、实体抽取和正式改写，并通过结构化 JSON 输出与自动评估机制，实现了一个可运行、可评估、可扩展的端到端工程系统。

## 环境要求
- Python 3.9+
- 依赖：`openai`、`python-dotenv`
- 需要在 `.env` 中配置 `OPENAI_API_KEY`

安装依赖：
```bash
python -m pip install -r requirements.txt
```

## 功能概览
- 一句话摘要（短句、直观）
- 3 条要点列表（便于快速理解）
- 主题与情绪分类（固定枚举）
- 关键词与实体信息抽取（时间、地点、人、组织）
- 正式书面改写（不添加事实）
- 自动生成：`*.result.json` 与 `*.report.md`

## 目录结构与功能
```
.
├─ app/                 # 核心逻辑
│  ├─ pipeline.py       # 调用 LLM + 解析结果
│  └─ schemas.py        # 数据结构定义
├─ data/                # 示例数据与输出
│  └─ sample.txt
├─ examples/            # 参考脚本（扩展/学习用）
├─ run.py               # 主入口：处理文本并输出结果
├─ eval.py              # 简易评测脚本（基于 tests.jsonl）
├─ 01_smoke_test.py     # API 连通性测试
├─ client.py            # OpenAI 客户端初始化
├─ config.py            # 环境变量加载
└─ requirements.txt     # 依赖列表
```

## 核心文件说明
- `app/pipeline.py`：核心流程，按顺序调用模型完成各子任务，并进行 JSON 解析与容错。
- `run.py`：读取输入文本，生成 `*.result.json` 与 `*.report.md`。
- `eval.py`：读取 `data/tests.jsonl`，统计主题/情绪命中率（用于演示评测思路）。

## 如何开始（从零到可运行）
1) 配置环境变量：在项目根目录创建/修改 `.env`
```env
OPENAI_API_KEY=你的key
```

2) 安装依赖
```bash
python -m pip install -r requirements.txt
```

3) 准备输入文本

- `data/sample.txt`

4) 运行主程序
```bash
python run.py data/sample.txt
```

5) 查看输出
- `data/sample.result.json`：结构化结果
- `data/sample.report.md`：可读性报告

## 输出示例
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

## 可选扩展
- 增加 `data/tests.jsonl` 的样例集，扩展评测维度（比如关键词命中率）。
- 增加命令行参数（如模型选择、摘要长度、是否生成报告）。
- 增加日志与重试策略说明，提升工程稳定性。
- 将结果写入前端页面或简单 Web UI，做交互式展示。


