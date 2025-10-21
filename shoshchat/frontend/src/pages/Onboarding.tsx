import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api from "../lib/api";
import ChatWidget from "../components/ChatWidget";
import { useTenant } from "../context/TenantContext";

interface EmbedResponse {
  embed_code: string;
}

const Onboarding = () => {
  const { tenant, refresh } = useTenant();
  const [embedCode, setEmbedCode] = useState<string>("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchEmbed = async () => {
      try {
        const response = await api.get<EmbedResponse>("/tenants/me/embed/");
        setEmbedCode(response.data.embed_code);
      } catch (error) {
        console.error("Unable to load embed code", error);
      }
    };
    void fetchEmbed();
    void refresh();
  }, [refresh]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(embedCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy", error);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
      <div className="mx-auto max-w-5xl space-y-10">
        <header className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-2xl">
          <h1 className="text-3xl font-semibold">You're almost ready!</h1>
          <p className="mt-2 text-sm text-slate-400">
            Embed the widget and start chatting with your visitors. Customize the widget and invite teammates from your dashboard.
          </p>
        </header>

        <section className="grid gap-8 lg:grid-cols-2">
          <div className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6">
            <h2 className="text-lg font-semibold">Copy your embed code</h2>
            <p className="mt-1 text-sm text-slate-400">Paste it before the closing &lt;/body&gt; tag on your site.</p>
            <div className="relative mt-4 rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
              <pre className="overflow-x-auto text-xs text-slate-300">
                <code>{embedCode}</code>
              </pre>
              <button
                type="button"
                onClick={handleCopy}
                className="absolute right-4 top-4 rounded-lg border border-slate-800 px-3 py-1 text-xs font-medium text-slate-300 transition hover:border-slate-600 hover:text-white"
              >
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <ul className="mt-6 space-y-2 text-sm text-slate-400">
              <li>• Works on any website or static site builder.</li>
              <li>• Automatically updates when you tweak widget settings.</li>
              <li>• Supports multiple domains via your tenant dashboard.</li>
            </ul>
          </div>
          <div className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6">
            <h2 className="text-lg font-semibold">Preview</h2>
            <p className="mt-1 text-sm text-slate-400">Try the widget with your selected accent.</p>
            <div className="mt-4 flex justify-center">
              <ChatWidget
                tenantId={tenant?.schema_name ?? "preview"}
                accent={(tenant?.widget_accent as "retail" | "finance") ?? "retail"}
              />
            </div>
          </div>
        </section>

        <section className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6">
          <h2 className="text-lg font-semibold">Next steps</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <h3 className="text-sm font-semibold text-slate-100">Customize the widget</h3>
              <p className="mt-2 text-xs text-slate-400">Adjust colors, greeting, and behavior in the dashboard.</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <h3 className="text-sm font-semibold text-slate-100">Invite your team</h3>
              <p className="mt-2 text-xs text-slate-400">Share access so collaborators can manage responses.</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <h3 className="text-sm font-semibold text-slate-100">Monitor usage</h3>
              <p className="mt-2 text-xs text-slate-400">Track message volume and upgrade when you hit limit.</p>
            </div>
          </div>
          <div className="mt-6 flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-300">Ready to explore the full dashboard?</p>
            </div>
            <Link
              to="/"
              className="rounded-xl bg-blue-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-400"
            >
              Go to dashboard
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Onboarding;
