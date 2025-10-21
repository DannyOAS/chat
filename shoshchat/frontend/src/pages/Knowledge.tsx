import { ChangeEvent, FormEvent, useEffect, useState } from "react";

import api from "../lib/api";
import { useTenant } from "../context/TenantContext";

interface KnowledgeSource {
  id: number;
  title: string;
  source_type: "file" | "url" | "text";
  status: "pending" | "processing" | "ready" | "failed";
  metadata: Record<string, unknown>;
  error_message: string;
  created_at: string;
  updated_at: string;
  chunk_count: number;
}

const Knowledge = () => {
  const { tenant } = useTenant();
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState<"file" | "url" | "text">("file");

  const fetchSources = async () => {
    try {
      setLoading(true);
      const response = await api.get<KnowledgeSource[]>("/knowledge/sources/");
      setSources(response.data);
    } catch (err) {
      console.error("Failed to load knowledge sources", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchSources();
  }, []);

  const resetForm = () => {
    setTitle("");
    setUrl("");
    setText("");
    setFile(null);
  };

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("title", title || file?.name || url || "Untitled");
      formData.append("source_type", sourceType);
      if (sourceType === "file" && file) {
        formData.append("file", file);
      }
      if (sourceType === "url") {
        formData.append("url", url);
      }
      if (sourceType === "text") {
        formData.append("raw_text", text);
      }
      await api.post("/knowledge/sources/", formData);
      resetForm();
      await fetchSources();
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail ?? "Unable to upload source");
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0];
    setFile(selected ?? null);
    if (selected && !title) {
      setTitle(selected.name.replace(/\.[^/.]+$/, ""));
    }
  };

  return (
    <div className="space-y-8">
      <section className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl">
        <h1 className="text-2xl font-semibold">Knowledge base</h1>
        <p className="mt-2 text-sm text-slate-400">
          Upload documents, URLs, or paste text to teach ShoshChat about {tenant?.name ?? "your business"}.
        </p>
        <form className="mt-6 grid gap-4 md:grid-cols-3" onSubmit={handleUpload}>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-wide text-slate-400">Source type</label>
            <select
              className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-slate-500"
              value={sourceType}
              onChange={(event) => setSourceType(event.target.value as typeof sourceType)}
            >
              <option value="file">File (PDF, DOCX, TXT)</option>
              <option value="url">URL</option>
              <option value="text">Text snippet</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-wide text-slate-400">Title</label>
            <input
              className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-slate-500"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Customer support handbook"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-wide text-slate-400">Upload</label>
            {sourceType === "file" && (
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm"
              />
            )}
            {sourceType === "url" && (
              <input
                type="url"
                value={url}
                required
                onChange={(event) => setUrl(event.target.value)}
                placeholder="https://"
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-slate-500"
              />
            )}
            {sourceType === "text" && (
              <textarea
                value={text}
                required
                onChange={(event) => setText(event.target.value)}
                rows={3}
                placeholder="Paste business context here"
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-slate-500"
              />
            )}
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              className="w-full rounded-xl bg-blue-500 px-4 py-3 text-sm font-medium text-white transition hover:bg-blue-400 disabled:opacity-60"
              disabled={uploading || (sourceType === "file" && !file)}
            >
              {uploading ? "Uploading…" : "Add to knowledge"}
            </button>
          </div>
        </form>
        {error ? (
          <div className="mt-4 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        ) : null}
      </section>

      <section className="rounded-3xl border border-slate-800 bg-slate-900/50 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Sources</h2>
            <p className="mt-1 text-sm text-slate-400">Track processing status and ingestion results.</p>
          </div>
          <button
            type="button"
            onClick={() => void fetchSources()}
            className="rounded-xl border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300 transition hover:border-slate-500 hover:text-white"
          >
            Refresh
          </button>
        </div>
        <div className="mt-6 overflow-x-auto">
          {loading ? (
            <p className="text-sm text-slate-400">Loading knowledge sources…</p>
          ) : sources.length === 0 ? (
            <p className="text-sm text-slate-400">No knowledge sources yet. Upload your first document above.</p>
          ) : (
            <table className="min-w-full divide-y divide-slate-800 text-left text-sm text-slate-300">
              <thead>
                <tr>
                  <th className="py-3">Title</th>
                  <th className="py-3">Type</th>
                  <th className="py-3">Status</th>
                  <th className="py-3">Chunks</th>
                  <th className="py-3">Updated</th>
                  <th className="py-3">Error</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {sources.map((source) => (
                  <tr key={source.id}>
                    <td className="py-3 font-medium text-white">{source.title}</td>
                    <td className="py-3 uppercase text-xs text-slate-400">{source.source_type}</td>
                    <td className="py-3">
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-medium ${
                          source.status === "ready"
                            ? "bg-emerald-500/10 text-emerald-300"
                            : source.status === "failed"
                            ? "bg-red-500/10 text-red-300"
                            : "bg-slate-700/40 text-slate-300"
                        }`}
                      >
                        {source.status}
                      </span>
                    </td>
                    <td className="py-3 text-xs text-slate-400">{source.chunk_count}</td>
                    <td className="py-3 text-xs text-slate-400">{new Date(source.updated_at).toLocaleString()}</td>
                    <td className="py-3 text-xs text-red-300">{source.error_message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
      <section className="rounded-3xl border border-slate-800 bg-slate-900/50 p-6">
        <h2 className="text-lg font-semibold">How it works</h2>
        <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-slate-300">
          <li>Upload documents, paste curated text, or link to public pages.</li>
          <li>ShoshChat extracts and chunks the content automatically.</li>
          <li>Embeddings are generated per chunk and stored securely.</li>
          <li>During conversations, relevant chunks are retrieved and supplied to the LLM.</li>
        </ol>
      </section>
    </div>
  );
};

export default Knowledge;
