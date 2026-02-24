import { Database, FlaskConical, LayoutDashboard } from "lucide-react";
import { NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { Toaster } from "sonner";

import { cn } from "./lib/utils.js";
import RAGLab from "./routes/RAGLab.jsx";
import TextLab from "./routes/TextLab.jsx";

const navItems = [
  { path: "/text", label: "TextLab", icon: LayoutDashboard },
  { path: "/rag", label: "RAGLab", icon: Database }
];

const headerMeta = {
  "/text": {
    title: "TextLab",
    subtitle: "文本处理、结构化提取与报告输出"
  },
  "/rag": {
    title: "RAGLab",
    subtitle: "知识库管理、索引构建与问答检索"
  }
};

function SidebarNav({ compact = false }) {
  return (
    <nav className={cn("flex gap-2", compact ? "flex-row" : "flex-col")}>
      {navItems.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                "inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                compact ? "justify-center border" : "justify-start",
                isActive
                  ? "bg-secondary text-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )
            }
          >
            <Icon className="h-4 w-4" />
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}

export default function App() {
  const location = useLocation();
  const meta = headerMeta[location.pathname] || headerMeta["/text"];

  return (
    <div className="min-h-screen bg-muted/20">
      <div className="grid min-h-screen md:grid-cols-[240px_1fr]">
        <aside className="hidden border-r bg-background md:block">
          <div className="flex h-14 items-center gap-2 border-b px-4">
            <FlaskConical className="h-5 w-5 text-primary" />
            <div className="text-sm font-semibold">LLM + RAG Console</div>
          </div>
          <div className="space-y-6 p-4">
            <SidebarNav />
            <div className="rounded-md border bg-muted/30 p-3 text-xs text-muted-foreground">
              面向内部场景的文本与知识库工作台。
            </div>
          </div>
        </aside>

        <div className="flex min-h-screen flex-col">
          <header className="sticky top-0 z-20 border-b bg-background/95 backdrop-blur">
            <div className="flex h-14 items-center justify-between px-4 md:px-6">
              <div>
                <p className="text-sm font-semibold">{meta.title}</p>
                <p className="hidden text-xs text-muted-foreground sm:block">{meta.subtitle}</p>
              </div>
            </div>
            <div className="border-t px-4 py-2 md:hidden">
              <SidebarNav compact />
            </div>
          </header>

          <main className="flex-1 p-4 md:p-6">
            <Routes>
              <Route path="/" element={<Navigate to="/text" replace />} />
              <Route path="/text" element={<TextLab />} />
              <Route path="/rag" element={<RAGLab />} />
            </Routes>
          </main>
        </div>
      </div>
      <Toaster richColors position="top-right" closeButton />
    </div>
  );
}