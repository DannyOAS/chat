import { FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useRegister } from "../hooks/useAuth";
import { usePlans } from "../hooks/usePlans";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ThemeToggle } from "@/components/ThemeToggle";


const defaultWelcome = "Hi there! I'm excited to help you today.";

const Register = () => {
  const { data: plans = [], isLoading: plansLoading } = usePlans();
  const registerMutation = useRegister();
  const [selectedPlan, setSelectedPlan] = useState<string>("");
  const [form, setForm] = useState({
    company_name: "",
    industry: "retail",
    domain: "",
    accent: "retail",
    welcome_message: defaultWelcome,
    primary_color: "#14b8a6",
    username: "",
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    password_confirm: "",
  });

  // Set default plan when plans are loaded
  useMemo(() => {
    if (plans.length > 0 && !selectedPlan) {
      setSelectedPlan(plans[0].slug);
    }
  }, [plans, selectedPlan]);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const selectedPlanDetails = useMemo(() => plans.find((plan) => plan.slug === selectedPlan), [plans, selectedPlan]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    registerMutation.mutate({
      ...form,
      plan: selectedPlan,
    });
  };

  return (
    <div className="min-h-screen bg-background px-6 py-10 text-foreground">
      <div className="absolute right-4 top-4">
        <ThemeToggle />
      </div>
      <div className="mx-auto flex max-w-5xl flex-col gap-10 lg:flex-row">
        <Card className="w-full max-w-md space-y-6 p-8">
          <div>
            <h1 className="text-3xl font-semibold">Create your ShoshChat account</h1>
            <p className="mt-2 text-sm text-slate-400">Start chatting with your customers in minutes.</p>
          </div>
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="company_name">Company Name</Label>
              <Input
                id="company_name"
                name="company_name"
                value={form.company_name}
                onChange={handleChange}
                required
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="industry">Industry</Label>
                <Select value={form.industry} onValueChange={(value) => setForm((prev) => ({ ...prev, industry: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="retail">Retail / E-commerce</SelectItem>
                    <SelectItem value="finance">Finance / Insurance</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="domain">Domain (optional)</Label>
                <Input
                  id="domain"
                  name="domain"
                  value={form.domain}
                  onChange={handleChange}
                  placeholder="chat.yourdomain.com"
                />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="first_name">First Name</Label>
                <Input
                  id="first_name"
                  name="first_name"
                  value={form.first_name}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name">Last Name</Label>
                <Input
                  id="last_name"
                  name="last_name"
                  value={form.last_name}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Business Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                name="username"
                value={form.username}
                onChange={handleChange}
                required
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  value={form.password}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password_confirm">Confirm Password</Label>
                <Input
                  id="password_confirm"
                  name="password_confirm"
                  type="password"
                  value={form.password_confirm}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="welcome_message">Welcome Message</Label>
              <Textarea
                id="welcome_message"
                name="welcome_message"
                value={form.welcome_message}
                onChange={handleChange}
                rows={3}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="accent">Widget Accent</Label>
                <Select value={form.accent} onValueChange={(value) => setForm((prev) => ({ ...prev, accent: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="retail">Retail</SelectItem>
                    <SelectItem value="finance">Finance</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="primary_color">Primary Color</Label>
                <Input
                  id="primary_color"
                  name="primary_color"
                  type="color"
                  value={form.primary_color}
                  onChange={handleChange}
                  className="h-12 cursor-pointer"
                />
              </div>
            </div>

            {registerMutation.error && (
              <Alert variant="destructive">
                <AlertDescription>
                  {(registerMutation.error as any)?.response?.data?.detail ?? "Unable to complete registration"}
                </AlertDescription>
              </Alert>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={registerMutation.isPending}
            >
              {registerMutation.isPending ? "Creating account…" : "Create account"}
            </Button>
            <p className="text-xs text-muted-foreground">
              Already have an account? <Link to="/login" className="text-primary hover:text-primary/80">Sign in</Link>
            </p>
          </form>
        </Card>
        <div className="flex-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Select a plan</CardTitle>
              <CardDescription>Scale your AI assistant with usage-based tiers.</CardDescription>
            </CardHeader>
            <CardContent>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {plansLoading ? (
                <div className="col-span-2 text-center text-muted-foreground">Loading plans...</div>
              ) : (
                plans.map((plan) => (
                <button
                  key={plan.slug}
                  type="button"
                  onClick={() => setSelectedPlan(plan.slug)}
                  className={`rounded-2xl border p-4 text-left transition ${
                    selectedPlan === plan.slug
                      ? "border-blue-500 bg-blue-500/10"
                      : "border-slate-800 bg-slate-900/40 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-slate-100">{plan.name}</h3>
                    <span className="text-sm text-slate-400">${plan.monthly_price}/mo</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-400">{plan.message_quota} messages / month</p>
                  <ul className="mt-3 space-y-1 text-xs text-slate-400">
                    {plan.features.map((feature) => (
                      <li key={feature}>• {feature}</li>
                    ))}
                  </ul>
                </button>
                ))
              )}
            </div>
            {selectedPlanDetails ? (
              <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
                <h3 className="font-semibold text-slate-100">{selectedPlanDetails.name} includes:</h3>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-400">
                  {selectedPlanDetails.features.map((feature) => (
                    <li key={feature}>{feature}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Preview your widget</CardTitle>
              <CardDescription>Customize the look before embedding.</CardDescription>
            </CardHeader>
            <CardContent>
            <div className="mt-4 flex justify-center">
              <div className="w-80 rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
                <div className="space-y-2 text-sm">
                  <p className="text-slate-300">{form.welcome_message}</p>
                  <div className="rounded-xl bg-slate-800/60 p-3">
                    <span className="text-xs uppercase tracking-wide text-slate-400">Accent</span>
                    <p className="text-sm text-slate-100">{form.accent}</p>
                  </div>
                  <div className="rounded-xl bg-slate-800/60 p-3">
                    <span className="text-xs uppercase tracking-wide text-slate-400">Primary Color</span>
                    <div className="mt-2 h-8 w-full rounded-lg" style={{ backgroundColor: form.primary_color }} />
                  </div>
                </div>
              </div>
            </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Register;
