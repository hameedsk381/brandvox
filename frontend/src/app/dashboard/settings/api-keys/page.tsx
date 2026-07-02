"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import toast from "react-hot-toast";

interface ApiKeyItem {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  is_active: boolean;
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [newKey, setNewKey] = useState<string | null>(null);

  const loadKeys = async () => {
    try {
      const res = await api.get("/api/api-keys");
      setKeys(res.data);
    } catch {
      toast.error("Failed to load API keys");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadKeys(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      const res = await api.post("/api/api-keys", { name: name.trim(), scopes: ["read"] });
      setNewKey(res.data.raw_key);
      setName("");
      await loadKeys();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to create key");
    }
  };

  const handleToggle = async (key: ApiKeyItem) => {
    try {
      await api.patch(`/api/api-keys/${key.id}`, { is_active: !key.is_active });
      await loadKeys();
      toast.success(key.is_active ? "Key deactivated" : "Key activated");
    } catch {
      toast.error("Failed to update key");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this API key? This cannot be undone.")) return;
    try {
      await api.delete(`/api/api-keys/${id}`);
      await loadKeys();
      toast.success("Key deleted");
    } catch {
      toast.error("Failed to delete key");
    }
  };

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">API Keys</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage API keys for programmatic access</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Create API Key</CardTitle>
          <CardDescription>Generate a new key for external integrations</CardDescription>
        </CardHeader>
        <CardContent>
          {newKey && (
            <div className="mb-4 p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
              <p className="text-xs font-medium text-amber-400 mb-1">Key created — copy it now, it won&apos;t be shown again:</p>
              <code className="text-sm bg-background px-3 py-2 rounded border border-border block font-mono break-all select-all">{newKey}</code>
              <Button size="sm" variant="outline" className="mt-2" onClick={() => { navigator.clipboard.writeText(newKey); toast.success("Copied!"); }}>
                Copy
              </Button>
            </div>
          )}
          <form onSubmit={handleCreate} className="flex items-end gap-2">
            <Input label="Key Name" placeholder="e.g. Production CI" value={name} onChange={(e) => setName(e.target.value)} required className="flex-1" />
            <Button type="submit" disabled={!name.trim()}>Generate</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Active Keys</CardTitle>
          <CardDescription>{keys.length} key{keys.length !== 1 ? "s" : ""} configured</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : keys.length === 0 ? (
            <p className="text-sm text-muted-foreground">No API keys yet. Create one above.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {keys.map((k) => (
                <div key={k.id} className="flex items-center justify-between p-3 rounded-lg border border-border bg-accent/20">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-foreground">{k.name}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${k.is_active ? "bg-emerald-500/10 text-emerald-400" : "bg-muted text-muted-foreground"}`}>
                        {k.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground font-mono mt-0.5">{k.key_prefix}...</p>
                    {k.last_used_at && <p className="text-[10px] text-muted-foreground mt-0.5">Last used: {new Date(k.last_used_at).toLocaleDateString()}</p>}
                  </div>
                  <div className="flex items-center gap-1 ml-3">
                    <Button size="sm" variant="ghost" onClick={() => handleToggle(k)}>
                      {k.is_active ? "Deactivate" : "Activate"}
                    </Button>
                    <Button size="sm" variant="ghost" className="text-destructive hover:text-destructive" onClick={() => handleDelete(k.id)}>
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}