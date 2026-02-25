import { useMemo, useState } from "react";
import { Copy, Download, FileUp, Loader2, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { toast } from "sonner";

import { Badge } from "../components/ui/badge.jsx";
import { Button } from "../components/ui/button.jsx";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card.jsx";
import { Input } from "../components/ui/input.jsx";
import { Label } from "../components/ui/label.jsx";
import { Separator } from "../components/ui/separator.jsx";
import { Skeleton } from "../components/ui/skeleton.jsx";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs.jsx";
import { Textarea } from "../components/ui/textarea.jsx";
import { fetchJson } from "../lib/api.js";
import { buildReportMarkdown } from "../lib/report.js";

const EMPTY_ENTITIES = { time: null, location: null, people: [], orgs: [] };

function OutputSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {Array.from({ length: 6 }).map((_, idx) => (
        <Card key={idx}>
          <CardHeader className="space-y-3">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-3/4" />
          </CardHeader>
        </Card>
      ))}
    </div>
  );
}

export default function TextLab() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState("json");

  const entities = result?.entities || EMPTY_ENTITIES;

  const reportMarkdown = useMemo(() => {
    if (!result) return "";
    return buildReportMarkdown(text, result);
  }, [text, result]);

  const jsonView = useMemo(() => {
    if (!result) return "";
    return JSON.stringify(result, null, 2);
  }, [result]);

  const metrics = useMemo(() => {
    const keywords = result?.keywords?.length || 0;
    const bullets = result?.summary_bullets?.length || 0;
    const entityCount = (entities.people?.length || 0) + (entities.orgs?.length || 0);
    const charCount = text.trim().length;
    return [
      { label: "文本长度", value: charCount },
      { label: "要点数", value: bullets },
      { label: "关键词", value: keywords },
      { label: "实体数", value: entityCount }
    ];
  }, [entities, result, text]);

  async function handleProcess() {
    if (!text.trim()) {
      toast.error("请输入需要处理的文本");
      return;
    }

    setLoading(true);
    try {
      const data = await fetchJson("/api/text/process", {
        method: "POST",
        body: JSON.stringify({ text })
      });
      setResult(data);
      toast.success("文本处理完成");
    } catch (error) {
      toast.error(error.message || "请求失败");
    } finally {
      setLoading(false);
    }
  }

  async function handleFileUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const fileText = await file.text();
      setText(fileText);
      toast.success(`已载入 ${file.name}`);
    } catch (error) {
      toast.error("读取文件失败");
    } finally {
      event.target.value = "";
    }
  }

  async function handleCopy() {
    if (!result) {
      toast.error("暂无可复制内容");
      return;
    }

    const payload = tab === "json" ? jsonView : reportMarkdown;
    try {
      await navigator.clipboard.writeText(payload);
      toast.success(tab === "json" ? "JSON 已复制" : "Markdown 已复制");
    } catch (error) {
      toast.error("复制失败，请检查浏览器权限");
    }
  }

  function handleDownload() {
    if (!result) {
      toast.error("暂无可下载内容");
      return;
    }

    const isJson = tab === "json";
    const payload = isJson ? jsonView : reportMarkdown;
    const filename = isJson
      ? `textlab-result-${Date.now()}.json`
      : `textlab-report-${Date.now()}.md`;
    const mimeType = isJson ? "application/json;charset=utf-8" : "text/markdown;charset=utf-8";

    const blob = new Blob([payload], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    toast.success(isJson ? "JSON 已下载" : "Markdown 已下载");
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">文本输入</CardTitle>
            <CardDescription>支持直接粘贴文本或上传 .txt/.md 文件。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="text-file">上传文本文件</Label>
              <Input id="text-file" type="file" accept=".txt,.md" onChange={handleFileUpload} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="text-input">文本内容</Label>
              <Textarea
                id="text-input"
                rows={16}
                placeholder="请输入待分析文本..."
                value={text}
                onChange={(event) => setText(event.target.value)}
              />
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button onClick={handleProcess} disabled={loading}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {loading ? "处理中" : "开始处理"}
              </Button>
              <Button variant="outline" onClick={() => setText("")} disabled={loading || !text}>
                清空
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="min-w-0 space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {metrics.map((item) => (
              <Card key={item.label}>
                <CardHeader className="space-y-1 px-4 py-3">
                  <CardDescription className="text-xs">{item.label}</CardDescription>
                  <CardTitle className="text-xl font-semibold">{item.value}</CardTitle>
                </CardHeader>
              </Card>
            ))}
          </div>

          {loading ? (
            <OutputSkeleton />
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>摘要</CardDescription>
                  <CardTitle className="text-sm font-medium">一句话总结</CardTitle>
                </CardHeader>
                <CardContent className="break-words text-sm leading-6 text-muted-foreground">
                  {result?.summary_short || "暂无结果"}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>分类</CardDescription>
                  <CardTitle className="text-sm font-medium">主题 / 情绪</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-2">
                  <Badge variant="secondary">主题: {result?.topic || "-"}</Badge>
                  <Badge variant="outline">情绪: {result?.sentiment || "-"}</Badge>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>要点</CardDescription>
                  <CardTitle className="text-sm font-medium">Summary Bullets</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    {(result?.summary_bullets || []).length ? (
                      result.summary_bullets.map((item, index) => (
                        <li key={index} className="leading-6">
                          {index + 1}. {item}
                        </li>
                      ))
                    ) : (
                      <li>暂无结果</li>
                    )}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>关键词</CardDescription>
                  <CardTitle className="text-sm font-medium">Keywords</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-2">
                  {(result?.keywords || []).length ? (
                    result.keywords.map((keyword, index) => (
                      <Badge key={index} variant="outline">
                        {keyword}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-sm text-muted-foreground">暂无结果</span>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>实体</CardDescription>
                  <CardTitle className="text-sm font-medium">Entities</CardTitle>
                </CardHeader>
                <CardContent className="space-y-1 text-sm text-muted-foreground">
                  <p>时间: {String(entities.time ?? "-")}</p>
                  <p>地点: {String(entities.location ?? "-")}</p>
                  <p>人物: {(entities.people || []).join("、") || "-"}</p>
                  <p>组织: {(entities.orgs || []).join("、") || "-"}</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>改写</CardDescription>
                  <CardTitle className="text-sm font-medium">Formal Rewrite</CardTitle>
                </CardHeader>
                <CardContent className="break-words text-sm leading-6 text-muted-foreground">
                  {result?.rewrite_formal || "暂无结果"}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>

      <Card className="min-w-0">
        <CardHeader className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <CardTitle className="text-base">结果视图</CardTitle>
              <CardDescription>支持 JSON 与 Markdown 两种格式。</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleCopy}>
                <Copy className="h-4 w-4" />
                复制当前视图
              </Button>
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <Download className="h-4 w-4" />
                下载当前视图
              </Button>
            </div>
          </div>
          <Separator />
        </CardHeader>
        <CardContent>
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList>
              <TabsTrigger value="json">JSON</TabsTrigger>
              <TabsTrigger value="markdown">Markdown</TabsTrigger>
            </TabsList>

            <TabsContent value="json" className="min-w-0">
              {loading ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-5/6" />
                  <Skeleton className="h-4 w-4/6" />
                </div>
              ) : (
                <pre className="mono max-h-[420px] overflow-y-auto overflow-x-hidden whitespace-pre-wrap break-words rounded-md border bg-muted/30 p-4 text-xs leading-6">
                  {jsonView || "暂无数据"}
                </pre>
              )}
            </TabsContent>

            <TabsContent value="markdown" className="min-w-0">
              {loading ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-5/6" />
                  <Skeleton className="h-4 w-4/6" />
                </div>
              ) : (
                <div className="min-w-0 max-h-[420px] overflow-y-auto overflow-x-hidden rounded-md border bg-muted/20 p-4 text-sm leading-7 [overflow-wrap:anywhere]">
                  {reportMarkdown ? (
                    <ReactMarkdown
                      components={{
                        h1: ({ ...props }) => <h1 className="mb-3 break-words text-lg font-semibold" {...props} />,
                        h2: ({ ...props }) => <h2 className="mb-2 mt-4 break-words text-base font-semibold" {...props} />,
                        p: ({ ...props }) => <p className="mb-2 break-words" {...props} />,
                        li: ({ ...props }) => <li className="mb-1 break-words" {...props} />,
                        pre: ({ ...props }) => (
                          <pre
                            className="mono my-2 max-w-full overflow-x-auto whitespace-pre-wrap break-all rounded bg-muted/30 p-3 text-xs leading-6"
                            {...props}
                          />
                        ),
                        code: ({ inline, ...props }) =>
                          inline ? (
                            <code className="mono rounded bg-muted px-1.5 py-0.5 text-xs break-all" {...props} />
                          ) : (
                            <code className="mono whitespace-pre-wrap break-all" {...props} />
                          )
                      }}
                    >
                      {reportMarkdown}
                    </ReactMarkdown>
                  ) : (
                    <p className="text-sm text-muted-foreground">暂无报告</p>
                  )}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <div className="rounded-md border border-dashed bg-muted/10 px-3 py-2 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <FileUp className="h-3.5 w-3.5" />
          上传文本后会直接填充到输入框，不改变后端处理逻辑。
        </div>
      </div>
    </div>
  );
}
