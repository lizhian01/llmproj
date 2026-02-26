import { useMemo, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "../components/ui/button.jsx";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card.jsx";
import { Input } from "../components/ui/input.jsx";
import { Label } from "../components/ui/label.jsx";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs.jsx";
import { useAuth } from "../lib/auth.jsx";

const USERNAME_RULE = "3-32 个字符，建议字母数字";
const PASSWORD_RULE = "至少 6 位";

export default function Login() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const canSubmit = useMemo(() => username.trim().length >= 3 && password.length >= 6, [username, password]);

  if (auth.user && !auth.loading) {
    return <Navigate to="/text" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!canSubmit) {
      toast.error("请填写有效的用户名与密码");
      return;
    }
    setLoading(true);
    try {
      if (tab === "login") {
        await auth.login(username.trim(), password);
        toast.success("登录成功");
      } else {
        await auth.register(username.trim(), password);
        toast.success("注册成功");
      }
      navigate("/text", { replace: true });
    } catch (error) {
      toast.error(error.message || "操作失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-2 text-center">
          <CardTitle className="text-2xl">LLM + RAG Console</CardTitle>
          <CardDescription>登录后访问 TextLab / RAGLab</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">登录</TabsTrigger>
              <TabsTrigger value="register">注册</TabsTrigger>
            </TabsList>
            <TabsContent value="login">
              <form className="space-y-4" onSubmit={handleSubmit}>
                <div className="space-y-2">
                  <Label htmlFor="login-username">用户名</Label>
                  <Input
                    id="login-username"
                    placeholder={USERNAME_RULE}
                    autoComplete="username"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="login-password">密码</Label>
                  <Input
                    id="login-password"
                    type="password"
                    placeholder={PASSWORD_RULE}
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                </div>
                <Button className="w-full" type="submit" disabled={loading}>
                  {loading ? "处理中" : "登录"}
                </Button>
              </form>
            </TabsContent>
            <TabsContent value="register">
              <form className="space-y-4" onSubmit={handleSubmit}>
                <div className="space-y-2">
                  <Label htmlFor="register-username">用户名</Label>
                  <Input
                    id="register-username"
                    placeholder={USERNAME_RULE}
                    autoComplete="username"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-password">密码</Label>
                  <Input
                    id="register-password"
                    type="password"
                    placeholder={PASSWORD_RULE}
                    autoComplete="new-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                </div>
                <Button className="w-full" type="submit" disabled={loading}>
                  {loading ? "处理中" : "注册"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
