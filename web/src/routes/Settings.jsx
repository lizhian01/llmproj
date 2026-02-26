import { useState } from "react";
import { toast } from "sonner";

import { Button } from "../components/ui/button.jsx";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card.jsx";
import { Input } from "../components/ui/input.jsx";
import { Label } from "../components/ui/label.jsx";
import { Separator } from "../components/ui/separator.jsx";
import { useAuth } from "../lib/auth.jsx";
import { fetchJson } from "../lib/api.js";

export default function Settings() {
  const auth = useAuth();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleDelete(event) {
    event.preventDefault();
    if (!confirm) {
      toast.error("请勾选确认选项");
      return;
    }
    if (password.length < 6) {
      toast.error("请输入有效密码");
      return;
    }

    setLoading(true);
    try {
      await fetchJson("/api/auth/me", {
        method: "DELETE",
        body: JSON.stringify({ password, confirm: true })
      });
      toast.success("账户已删除");
      await auth.logout();
    } catch (error) {
      toast.error(error.message || "删除失败");
    } finally {
      setLoading(false);
      setPassword("");
      setConfirm(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">当前账户</CardTitle>
          <CardDescription>查看登录状态与账号信息。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div>
            <span className="text-muted-foreground">用户名：</span>
            <span className="font-medium">{auth.user?.username || "-"}</span>
          </div>
          <div>
            <span className="text-muted-foreground">用户 ID：</span>
            <span className="mono text-xs">{auth.user?.id || "-"}</span>
          </div>
          <div>
            <span className="text-muted-foreground">创建时间：</span>
            <span>{auth.user?.created_at || "-"}</span>
          </div>
        </CardContent>
      </Card>

      <Card className="border-destructive/40">
        <CardHeader>
          <CardTitle className="text-base text-destructive">删除账户</CardTitle>
          <CardDescription>此操作不可恢复，会清理历史记录与 KB 数据。</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleDelete}>
            <div className="space-y-2">
              <Label htmlFor="delete-password">确认密码</Label>
              <Input
                id="delete-password"
                type="password"
                placeholder="请输入当前密码"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </div>
            <div className="flex items-center gap-2 text-sm">
              <input
                id="delete-confirm"
                type="checkbox"
                checked={confirm}
                onChange={(event) => setConfirm(event.target.checked)}
              />
              <Label htmlFor="delete-confirm">我已知晓删除后无法恢复</Label>
            </div>
            <Separator />
            <Button variant="destructive" type="submit" disabled={loading}>
              {loading ? "处理中" : "永久删除"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
