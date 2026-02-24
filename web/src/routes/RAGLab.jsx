import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, Copy, Database, Loader2, Search, Upload } from "lucide-react";
import { toast } from "sonner";

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../components/ui/accordion.jsx";
import { Badge } from "../components/ui/badge.jsx";
import { Button } from "../components/ui/button.jsx";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card.jsx";
import { Input } from "../components/ui/input.jsx";
import { Label } from "../components/ui/label.jsx";
import { Progress } from "../components/ui/progress.jsx";
import { Separator } from "../components/ui/separator.jsx";
import { Skeleton } from "../components/ui/skeleton.jsx";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table.jsx";
import { Textarea } from "../components/ui/textarea.jsx";
import { fetchJson } from "../lib/api.js";

const selectClassName =
  "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

function AskResultSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-5 w-32" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-11/12" />
      <Skeleton className="h-2 w-full" />
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-12 w-full" />
    </div>
  );
}

export default function RAGLab() {
  const [kbs, setKbs] = useState([]);
  const [selectedKb, setSelectedKb] = useState("");
  const [kbIdInput, setKbIdInput] = useState("");
  const [kbNameInput, setKbNameInput] = useState("");
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [asking, setAsking] = useState(false);
  const [question, setQuestion] = useState("");
  const [topk, setTopk] = useState("5");
  const [threshold, setThreshold] = useState("0.35");
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("");
  const [lastError, setLastError] = useState("");

  const loadKbs = useCallback(async (silent = false) => {
    try {
      const data = await fetchJson("/api/kb/list");
      const list = data.kbs || [];
      setKbs(list);
      setSelectedKb((current) => {
        if (current && list.some((item) => item.kb_id === current)) {
          return current;
        }
        return list[0]?.kb_id || "";
      });
    } catch (error) {
      if (!silent) {
        const message = error.message || "加载 KB 列表失败";
        setLastError(message);
        toast.error(message);
      }
    }
  }, []);

  useEffect(() => {
    loadKbs();
  }, [loadKbs]);

  const activeKb = selectedKb;
  const activeKbMeta = useMemo(
    () => kbs.find((item) => item.kb_id === activeKb) || null,
    [activeKb, kbs]
  );

  const kbProgress = useMemo(() => {
    if (uploading) return 35;
    if (indexing) return 72;
    if (!activeKbMeta) return 10;
    return activeKbMeta.index?.built ? 100 : 45;
  }, [activeKbMeta, indexing, uploading]);

  const scoreThreshold = useMemo(() => {
    if (typeof result?.threshold === "number") return result.threshold;
    const parsed = Number(threshold);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : 0.35;
  }, [result, threshold]);

  const scorePercent = useMemo(() => {
    if (typeof result?.top_score !== "number" || scoreThreshold <= 0) return 0;
    return Math.min((result.top_score / scoreThreshold) * 100, 100);
  }, [result, scoreThreshold]);

  async function handleUpload() {
    if (!files.length) {
      toast.error("请先选择上传文件");
      return;
    }

    setUploading(true);
    setLastError("");
    setStatus("");

    try {
      const form = new FormData();
      files.forEach((file) => form.append("files", file));
      if (kbIdInput.trim()) form.append("kb_id", kbIdInput.trim());
      if (kbNameInput.trim()) form.append("kb_name", kbNameInput.trim());

      const data = await fetchJson("/api/kb/upload", {
        method: "POST",
        body: form
      });

      setStatus(`已上传 ${data.files?.length || 0} 个文件到 ${data.kb_id}`);
      setSelectedKb(data.kb_id);
      setKbIdInput("");
      setKbNameInput("");
      setFiles([]);
      toast.success("上传完成");
      await loadKbs(true);
    } catch (error) {
      const message = error.message || "上传失败";
      setLastError(message);
      toast.error(message);
    } finally {
      setUploading(false);
    }
  }

  async function handleIndex() {
    if (!activeKb) {
      toast.error("请先选择 KB");
      return;
    }

    setIndexing(true);
    setLastError("");
    setStatus("");

    try {
      const data = await fetchJson(`/api/kb/${activeKb}/index`, {
        method: "POST"
      });
      setStatus(`索引完成，chunks=${data.stats?.chunks ?? "-"}`);
      toast.success("索引构建完成");
      await loadKbs(true);
    } catch (error) {
      const message = error.message || "索引失败";
      setLastError(message);
      toast.error(message);
    } finally {
      setIndexing(false);
    }
  }

  async function handleAsk() {
    if (!activeKb) {
      toast.error("请先选择 KB");
      return;
    }
    if (!question.trim()) {
      toast.error("请输入问题");
      return;
    }

    setAsking(true);
    setLastError("");

    try {
      const data = await fetchJson("/api/rag/ask", {
        method: "POST",
        body: JSON.stringify({
          kb_id: activeKb,
          question,
          topk: Number(topk) || 5,
          threshold: Number(threshold) || 0.35
        })
      });

      setResult(data);
      if (data.refused) {
        toast.warning("已按阈值策略拒答");
      } else {
        toast.success("问答完成");
      }
    } catch (error) {
      const message = error.message || "问答失败";
      setLastError(message);
      toast.error(message);
    } finally {
      setAsking(false);
    }
  }

  async function handleCopyAnswer() {
    if (!result?.answer) {
      toast.error("暂无可复制答案");
      return;
    }
    try {
      await navigator.clipboard.writeText(result.answer);
      toast.success("答案已复制");
    } catch (error) {
      toast.error("复制失败，请检查浏览器权限");
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">KB 管理</CardTitle>
          <CardDescription>管理知识库、上传文档并构建索引。</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-[1fr_220px]">
              <div className="space-y-2">
                <Label htmlFor="kb-select">当前 KB</Label>
                <select
                  id="kb-select"
                  className={selectClassName}
                  value={activeKb}
                  onChange={(event) => setSelectedKb(event.target.value)}
                >
                  <option value="">请选择 KB</option>
                  {kbs.map((kb) => (
                    <option key={kb.kb_id} value={kb.kb_id}>
                      {kb.name || kb.kb_id}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label>索引状态</Label>
                <div className="flex h-9 items-center rounded-md border px-3 text-sm">
                  {activeKbMeta?.index?.built ? (
                    <>
                      <CheckCircle2 className="mr-2 h-4 w-4 text-green-600" />
                      已构建
                    </>
                  ) : (
                    <>
                      <AlertCircle className="mr-2 h-4 w-4 text-amber-500" />
                      未构建
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>KB</TableHead>
                    <TableHead className="w-20 text-right">文件</TableHead>
                    <TableHead className="w-24 text-right">状态</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {kbs.length ? (
                    kbs.map((kb) => {
                      const selected = kb.kb_id === activeKb;
                      return (
                        <TableRow
                          key={kb.kb_id}
                          className={selected ? "bg-muted/50" : ""}
                          onClick={() => setSelectedKb(kb.kb_id)}
                        >
                          <TableCell>
                            <div className="max-w-[320px] truncate font-medium">{kb.name || kb.kb_id}</div>
                            <div className="mono text-xs text-muted-foreground">{kb.kb_id}</div>
                          </TableCell>
                          <TableCell className="text-right text-sm">{kb.files?.length || 0}</TableCell>
                          <TableCell className="text-right">
                            <Badge variant={kb.index?.built ? "secondary" : "outline"}>
                              {kb.index?.built ? "Ready" : "Pending"}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  ) : (
                    <TableRow>
                      <TableCell colSpan={3} className="py-6 text-center text-sm text-muted-foreground">
                        暂无知识库
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="kb-id-input">可选 kb_id</Label>
              <Input
                id="kb-id-input"
                placeholder="不填则自动生成"
                value={kbIdInput}
                onChange={(event) => setKbIdInput(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="kb-name-input">可选 KB 名称</Label>
              <Input
                id="kb-name-input"
                placeholder="例如：网络协议文档"
                value={kbNameInput}
                onChange={(event) => setKbNameInput(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="kb-file-input">上传文档</Label>
              <Input
                id="kb-file-input"
                type="file"
                multiple
                accept=".txt,.md"
                onChange={(event) => setFiles(Array.from(event.target.files || []))}
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <Button onClick={handleUpload} disabled={uploading}>
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                {uploading ? "上传中" : "上传"}
              </Button>
              <Button variant="outline" onClick={handleIndex} disabled={indexing || !activeKb}>
                {indexing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Database className="h-4 w-4" />}
                {indexing ? "建库中" : "开始建库"}
              </Button>
            </div>

            <Separator />

            <div className="space-y-3 rounded-md border bg-muted/20 p-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">任务状态</span>
                <span className="font-medium">{status || "等待操作"}</span>
              </div>
              <Progress value={kbProgress} indicatorClassName={indexing ? "bg-amber-500" : "bg-primary"} />
              <div className="text-xs text-muted-foreground">
                {activeKbMeta ? `当前 KB: ${activeKbMeta.kb_id}` : "请先选择或上传 KB"}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">问答输入</CardTitle>
            <CardDescription>设置参数后发起 RAG 问答。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="rag-question">问题</Label>
              <Textarea
                id="rag-question"
                rows={8}
                placeholder="请输入你的问题..."
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="rag-topk">TopK</Label>
                <Input
                  id="rag-topk"
                  type="number"
                  min={1}
                  max={20}
                  value={topk}
                  onChange={(event) => setTopk(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rag-threshold">Threshold</Label>
                <Input
                  id="rag-threshold"
                  type="number"
                  min={0}
                  max={1}
                  step="0.01"
                  value={threshold}
                  onChange={(event) => setThreshold(event.target.value)}
                />
              </div>
            </div>
            <Button className="w-full" onClick={handleAsk} disabled={asking}>
              {asking ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              {asking ? "检索中" : "发起问答"}
            </Button>
            {lastError ? <div className="text-sm text-destructive">{lastError}</div> : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle className="text-base">问答输出</CardTitle>
                <CardDescription>展示答案、阈值判断和引用证据。</CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={handleCopyAnswer} disabled={!result?.answer}>
                <Copy className="h-4 w-4" />
                复制答案
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {asking ? (
              <AskResultSkeleton />
            ) : result ? (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={result.refused ? "destructive" : "secondary"}>
                    {result.refused ? "Refused" : "Answered"}
                  </Badge>
                  {result.reason ? <Badge variant="outline">原因: {result.reason}</Badge> : null}
                </div>

                <div className="rounded-md border bg-muted/20 p-4 text-sm leading-7">{result.answer}</div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>top_score</span>
                    <span className="mono">
                      {typeof result.top_score === "number" ? result.top_score.toFixed(4) : "-"} / {scoreThreshold}
                    </span>
                  </div>
                  <Progress
                    value={scorePercent}
                    indicatorClassName={result.refused ? "bg-destructive" : "bg-primary"}
                  />
                </div>

                <Separator />

                <div className="space-y-2">
                  <div className="text-sm font-medium">Citations ({result.citations?.length || 0})</div>
                  {result.citations?.length ? (
                    <Accordion type="single" collapsible className="w-full rounded-md border px-3">
                      {result.citations.map((citation, index) => (
                        <AccordionItem key={`${citation.chunk_id || index}`} value={`cite-${index}`}>
                          <AccordionTrigger className="py-2 hover:no-underline">
                            <div className="flex w-full items-center justify-between pr-3 text-left">
                              <span className="max-w-[320px] truncate text-sm">{citation.source_file}</span>
                              <span className="mono text-xs text-muted-foreground">
                                score {Number(citation.score || 0).toFixed(4)}
                              </span>
                            </div>
                          </AccordionTrigger>
                          <AccordionContent>
                            <div className="rounded-sm bg-muted/30 p-3 text-xs leading-6 text-muted-foreground">
                              {citation.chunk_preview || "(empty)"}
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  ) : (
                    <div className="text-sm text-muted-foreground">暂无引用证据</div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">尚未发起问答。</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}