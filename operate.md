# 完整操作文档（operate.md）
本文档按“从零到可联调”的顺序说明 llmproj 的完整使用方法。

## 1. 目标与范围
- 提供文本处理能力（摘要、分类、实体、改写）。
- 提供本地知识库 RAG 能力（上传、建库、问答、拒答）。
- 同时支持 CLI 与 Web（FastAPI + Vite React）。
- 支持历史记录查看（TextLab / RAGLab）。

## 2. 前置条件
- Python 3.9+
- Node.js 18+
- 可访问模型 API
- 项目根目录具备 `.env`

## 3. 环境配置

### 3.1 配置 `.env`
在项目根目录创建：
```env
OPENAI_API_KEY=your_key
```

可选：
```env
OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=5
OPENAI_PROXY=http://127.0.0.1:7890
```

历史记录可选配置：
```env
HISTORY_MAX_RECORDS=100
HISTORY_DB_PATH=data/history.db
```

### 3.2 安装 Python 依赖
```bash
python -m pip install -r requirements.txt
```

### 3.3 安装前端依赖
```bash
cd web
npm install
cd ..
```

## 4. 启动服务

### 4.1 启动后端（终端 A）
必须在项目根目录执行：
```bash
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

提示：若在 `web/` 目录启动，可能出现 `No module named 'server'`。

### 4.2 启动前端（终端 B）
```bash
cd web
npm run dev
```

默认访问：`http://localhost:5173`

如需自定义后端地址：
```bash
# Windows PowerShell
$env:VITE_API_BASE="http://localhost:8000"
npm run dev
```

## 5. Web 端操作流程

### 5.1 TextLab
1. 打开 `TextLab` 页面。
2. 粘贴文本或上传 `.txt/.md` 文件。
3. 点击“开始处理”。
4. 查看右侧卡片结果。
5. 在下方切换 `JSON` / `Markdown` 视图。
6. 使用“复制/下载”导出结果。
7. 在“历史记录”区域查看最近生成记录与详情。

### 5.2 RAGLab
1. 在 KB 管理区上传知识库文件。
2. 选择目标 KB，点击“开始建库”。
3. 在问答区输入问题并设置 `TopK` 与 `Threshold`。
4. 点击“发起问答”。
5. 查看以下信息：
   - `answer`
   - `refused` 状态
   - `top_score / threshold` 进度条
   - `citations` 折叠列表
6. 在“历史记录”区域查看近期问答与检索详情。

### 5.3 历史记录说明
- 数据持久化存储在 `data/history.db`（SQLite）。
- 默认保留最近 `HISTORY_MAX_RECORDS` 条。
- 清空历史：删除 `data/history.db` 或设置新的 `HISTORY_DB_PATH`。

## 6. API 联调流程（推荐）

### 6.1 上传 KB
```bash
curl -X POST "http://localhost:8000/api/kb/upload" \
  -F "files=@data/kb/company_policy.md" \
  -F "kb_name=policy"
```
记录返回的 `kb_id`。

### 6.2 建索引
```bash
curl -X POST "http://localhost:8000/api/kb/<kb_id>/index"
```

### 6.3 发起问答
```bash
curl -X POST "http://localhost:8000/api/rag/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id":"<kb_id>",
    "question":"udp 特点是什么？",
    "topk":5,
    "threshold":0.35
  }'
```

### 6.4 文本处理
```bash
curl -X POST "http://localhost:8000/api/text/process" \
  -H "Content-Type: application/json" \
  -d '{"text":"在这里放待处理文本"}'
```

### 6.5 历史记录接口
```bash
curl "http://localhost:8000/api/text/history?limit=50"
curl "http://localhost:8000/api/text/history/<id>"

curl "http://localhost:8000/api/rag/history?limit=50"
curl "http://localhost:8000/api/rag/history/<id>"
```

## 7. CLI 操作流程

### 7.1 文本处理
```bash
python run.py data/sample.txt
```
输出：
- `data/sample.result.json`
- `data/sample.report.md`

### 7.2 RAG 建库
```bash
python qa.py index --kb data/kb
```

### 7.3 RAG 问答
```bash
python qa.py ask --question "udp 特点是什么" --topk 5 --threshold 0.35
```

## 8. 数据落盘说明

### 8.1 Web 模式（多 KB）
- 上传原文：`data/kbs/{kb_id}/raw/`
- 索引目录：`data/kbs/{kb_id}/index/`
- chunk 文件：`data/kbs/{kb_id}/chunks.json`
- 元信息：`data/kbs/manifest.json`
- 历史记录：`data/history.db`

### 8.2 CLI 默认路径
- 索引目录：`data/index/`
- chunk 文件：`data/chunks.json`

## 9. 参数建议
- `topk`：默认 `5`，可按知识库规模调整。
- `threshold`：默认 `0.35`。
- 如问答经常拒答，先查看 `top_score` 与 `threshold` 差距。
- 修改知识库文件或切分策略后必须重建索引。
- 历史记录条数可用 `HISTORY_MAX_RECORDS` 调整。

## 10. 常见问题排查

### 10.1 `No module named 'server'`
原因：后端在错误目录启动。
解决：回到项目根目录执行 `uvicorn server.main:app ...`。

### 10.2 RAG 返回“证据不足/拒答”
排查顺序：
1. 是否使用正确 `kb_id`。
2. 上传后是否重建索引。
3. 返回 `reason` 是否为 `below_threshold`。
4. 检查 `top_score` 与 `threshold` 差距。

### 10.3 前端请求失败
- 后端是否启动在 `http://localhost:8000`。
- 前端是否指向正确 `VITE_API_BASE`。
- 控制台是否有跨域或 4xx/5xx 错误。

### 10.4 上传成功但无法建库
- 确认上传的是 `.txt/.md`。
- 检查 `data/kbs/{kb_id}/raw/` 是否存在文件。

### 10.5 历史记录为空
- 检查是否有成功请求。
- 确认 `HISTORY_DB_PATH` 指向的数据库文件存在。

## 11. 日常维护建议
- 先改 `app/` 算法，再在 `server/services/` 封装业务，再补前端交互。
- 每次改 API 字段时同步更新 `README.md` 与 `operate.md`。
- 定期清理 `data/kbs/` 旧索引，避免无效占用。
