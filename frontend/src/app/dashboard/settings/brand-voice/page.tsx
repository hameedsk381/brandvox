"use client";

import React, { useState, useEffect } from "react";
import { useTenantStore } from "@/stores/tenant-store";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { settingsAPI } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import toast from "react-hot-toast";

export default function BrandVoicePage() {
  const currentClient = useTenantStore((state) => state.currentClient);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["brand-voice", currentClient?.id],
    queryFn: () => settingsAPI.getBrandVoice(currentClient!.id),
    enabled: !!currentClient?.id,
  });

  const [form, setForm] = useState({
    tone: "professional",
    vocabulary_notes: "",
    greeting_style: "",
    closing_style: "",
    example_replies: [] as string[],
    personality_traits: [] as string[],
  });

  useEffect(() => {
    if (data) {
      setForm({
        tone: data.tone || "professional",
        vocabulary_notes: data.vocabulary_notes || "",
        greeting_style: data.greeting_style || "",
        closing_style: data.closing_style || "",
        example_replies: data.example_replies || [],
        personality_traits: data.personality_traits || [],
      });
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: () => settingsAPI.updateBrandVoice(currentClient!.id, form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brand-voice"] });
      toast.success("Brand voice saved");
    },
    onError: () => toast.error("Failed to save"),
  });

  const addArrayItem = (field: "example_replies" | "personality_traits") => {
    setForm((prev) => ({ ...prev, [field]: [...prev[field], ""] }));
  };

  const updateArrayItem = (field: "example_replies" | "personality_traits", index: number, value: string) => {
    setForm((prev) => {
      const arr = [...prev[field]];
      arr[index] = value;
      return { ...prev, [field]: arr };
    });
  };

  const removeArrayItem = (field: "example_replies" | "personality_traits", index: number) => {
    setForm((prev) => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index),
    }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 rounded-full border-t-2 border-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Brand Voice</h1>
        <p className="text-sm text-muted-foreground mt-1">Configure how AI replies sound for {currentClient?.name}</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Voice Configuration</CardTitle></CardHeader>
        <CardContent className="flex flex-col gap-5">
          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1 block">Tone</label>
            <select
              className="w-full h-10 rounded-md border border-border bg-background px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/60"
              value={form.tone}
              onChange={(e) => setForm({ ...form, tone: e.target.value })}
            >
              <option value="professional">Professional</option>
              <option value="friendly">Friendly</option>
              <option value="formal">Formal</option>
              <option value="casual">Casual</option>
              <option value="empathetic">Empathetic</option>
            </select>
          </div>

          <Input
            label="Vocabulary Notes"
            placeholder="Words to use / avoid..."
            value={form.vocabulary_notes}
            onChange={(e) => setForm({ ...form, vocabulary_notes: e.target.value })}
          />

          <Input
            label="Greeting Style"
            placeholder="e.g., Dear [name],"
            value={form.greeting_style}
            onChange={(e) => setForm({ ...form, greeting_style: e.target.value })}
          />

          <Input
            label="Closing Style"
            placeholder="e.g., Best regards,"
            value={form.closing_style}
            onChange={(e) => setForm({ ...form, closing_style: e.target.value })}
          />

          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 block">Personality Traits</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {form.personality_traits.map((trait, i) => (
                <div key={i} className="flex items-center gap-1">
                  <Badge variant="secondary" className="text-[10px] px-2 py-1">{trait || "(empty)"}</Badge>
                  <button onClick={() => removeArrayItem("personality_traits", i)} className="text-rose-400 text-xs hover:text-rose-300 cursor-pointer">&times;</button>
                </div>
              ))}
            </div>
            <Button size="sm" variant="outline" onClick={() => addArrayItem("personality_traits")}>+ Add Trait</Button>
            {form.personality_traits.map((trait, i) => (
              <input
                key={i}
                className="hidden"
                value={form.personality_traits[i]}
                onChange={(e) => updateArrayItem("personality_traits", i, e.target.value)}
              />
            ))}
          </div>

          <Button onClick={() => saveMutation.mutate()} loading={saveMutation.isPending}>
            Save Changes
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
