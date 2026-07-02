"use client";

import React, { useState, useEffect } from "react";
import { useTenantStore } from "@/stores/tenant-store";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { settingsAPI, UpdateSmartRulesData } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import toast from "react-hot-toast";

const ACTIONS = [
  { value: "auto_reply", label: "Auto-Reply" },
  { value: "approval_required", label: "Approval Required" },
  { value: "escalate", label: "Escalate" },
  { value: "never_auto", label: "Never Auto-Reply" },
];

export default function SmartRulesPage() {
  const currentLocation = useTenantStore((state) => state.currentLocation);
  const queryClient = useQueryClient();

  const { data: rules, isLoading } = useQuery({
    queryKey: ["smart-rules", currentLocation?.id],
    queryFn: () => settingsAPI.getSmartRules(currentLocation!.id),
    enabled: !!currentLocation?.id,
  });

  const [editingRules, setEditingRules] = useState<UpdateSmartRulesData[]>([]);

  useEffect(() => {
    if (rules) {
      setEditingRules(rules.map((r: UpdateSmartRulesData) => ({ ...r })));
    }
  }, [rules]);

  const saveMutation = useMutation({
    mutationFn: () => settingsAPI.updateSmartRules(currentLocation!.id, editingRules),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["smart-rules"] });
      toast.success("Rules saved");
    },
    onError: () => toast.error("Failed to save"),
  });

  const updateRule = (index: number, field: keyof UpdateSmartRulesData, value: boolean | number | string | string[]) => {
    setEditingRules((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const addRule = () => {
    setEditingRules((prev) => [
      ...prev,
      { min_rating: 5, max_rating: 5, action: "auto_reply", notify_roles: [], is_active: true },
    ]);
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
        <h1 className="text-2xl font-bold text-foreground">Smart Rules</h1>
        <p className="text-sm text-muted-foreground mt-1">Auto-reply rules for {currentLocation?.name}</p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Rating-Based Rules</CardTitle>
          <Button size="sm" variant="outline" onClick={addRule}>+ Add Rule</Button>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {editingRules.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">No rules configured yet</p>
          ) : (
            editingRules.map((rule: UpdateSmartRulesData, i) => (
              <div key={i} className="p-4 rounded-lg bg-muted/50 border border-border flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-muted-foreground">Rule {i + 1}</span>
                  <Switch
                    checked={rule.is_active ?? false}
                    onCheckedChange={(v) => updateRule(i, "is_active", v)}
                  />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div>
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase mb-1 block">Min Rating</label>
                    <select
                      className="w-full h-9 rounded-md border border-border bg-background px-2 text-sm text-foreground"
                      value={rule.min_rating}
                      onChange={(e) => updateRule(i, "min_rating", parseInt(e.target.value))}
                    >
                      {[1, 2, 3, 4, 5].map((r) => (
                        <option key={r} value={r}>{r} ★</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase mb-1 block">Max Rating</label>
                    <select
                      className="w-full h-9 rounded-md border border-border bg-background px-2 text-sm text-foreground"
                      value={rule.max_rating}
                      onChange={(e) => updateRule(i, "max_rating", parseInt(e.target.value))}
                    >
                      {[1, 2, 3, 4, 5].map((r) => (
                        <option key={r} value={r}>{r} ★</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase mb-1 block">Action</label>
                    <select
                      className="w-full h-9 rounded-md border border-border bg-background px-2 text-sm text-foreground"
                      value={rule.action}
                      onChange={(e) => updateRule(i, "action", e.target.value)}
                    >
                      {ACTIONS.map((a) => (
                        <option key={a.value} value={a.value}>{a.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            ))
          )}

          {editingRules.length > 0 && (
            <Button onClick={() => saveMutation.mutate()} loading={saveMutation.isPending} className="w-fit">
              Save Rules
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
