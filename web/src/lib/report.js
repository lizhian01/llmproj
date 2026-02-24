export function buildReportMarkdown(sourceText, result) {
  const previewLen = 800;
  let previewText = (sourceText || "").trim();
  if (previewText.length > previewLen) {
    previewText = `${previewText.slice(0, previewLen)} ...（略）`;
  }

  const bullets = result?.summary_bullets || [];
  const keywords = result?.keywords || [];
  const entities = result?.entities || {};
  const time = entities.time ?? null;
  const location = entities.location ?? null;
  const people = entities.people ?? [];
  const orgs = entities.orgs ?? [];

  const lines = [];
  lines.push("# 文本处理辅助系统报告\n");
  lines.push(`- 生成时间：${new Date().toLocaleString()}\n`);

  lines.push("## 1. 原文（截断预览）");
  lines.push("```");
  lines.push(previewText);
  lines.push("```\n");

  lines.push("## 2. 一句话摘要");
  lines.push(`${(result?.summary_short || "").trim()}\n`);

  lines.push("## 3. 要点摘要（3条）");
  if (bullets.length) {
    bullets.forEach((b, i) => lines.push(`${i + 1}. ${b}`));
  } else {
    lines.push("（无）");
  }
  lines.push("");

  lines.push("## 4. 分类与情绪");
  lines.push(`- 主题（topic）：**${result?.topic || ""}**`);
  lines.push(`- 情绪（sentiment）：**${result?.sentiment || ""}**\n`);

  lines.push("## 5. 关键词");
  if (keywords.length) {
    lines.push(`- ${keywords.join("、")}\n`);
  } else {
    lines.push("- （无）\n");
  }

  lines.push("## 6. 实体信息抽取");
  lines.push(`- 时间：${time}`);
  lines.push(`- 地点：${location}`);
  lines.push(`- 人物：${people}`);
  lines.push(`- 组织：${orgs}\n`);

  lines.push("## 7. 正式书面改写");
  lines.push(`${(result?.rewrite_formal || "").trim()}\n`);

  return lines.join("\n");
}
