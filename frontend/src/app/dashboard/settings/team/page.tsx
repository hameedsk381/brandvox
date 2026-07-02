"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { settingsAPI } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { ROLE_LABELS } from "@/lib/constants";
import toast from "react-hot-toast";

export default function TeamPage() {
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);

  const { data: users, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: settingsAPI.getUsers,
  });

  const [showInvite, setShowInvite] = useState(false);
  const [inviteForm, setInviteForm] = useState({ name: "", email: "", password: "", role: "read_only" });

  const createUser = useMutation({
    mutationFn: () => settingsAPI.createUser(inviteForm),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setShowInvite(false);
      setInviteForm({ name: "", email: "", password: "", role: "read_only" });
      toast.success("User created");
    },
    onError: () => toast.error("Failed to create user"),
  });

  const isSuperOrAgency = user?.role === "super_admin" || user?.role === "agency_admin";

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Team</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage users and roles</p>
        </div>
        {isSuperOrAgency && (
          <Button size="sm" onClick={() => setShowInvite(true)}>+ Add User</Button>
        )}
      </div>

      <Card>
        <CardHeader><CardTitle>Team Members</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-8 h-8 rounded-full border-t-2 border-primary animate-spin" />
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {users?.map((u: any) => (
                <div key={u.id} className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 border border-border">
                  <Avatar fallback={u.name} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold text-foreground truncate">{u.name}</div>
                    <div className="text-xs text-muted-foreground truncate">{u.email}</div>
                  </div>
                  <Badge variant="secondary" className="text-[10px]">{ROLE_LABELS[u.role] || u.role}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog isOpen={showInvite} onClose={() => setShowInvite(false)} title="Add User">
        <div className="flex flex-col gap-4">
          <Input label="Name" value={inviteForm.name} onChange={(e) => setInviteForm({ ...inviteForm, name: e.target.value })} />
          <Input label="Email" type="email" value={inviteForm.email} onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })} />
          <Input label="Password" type="password" value={inviteForm.password} onChange={(e) => setInviteForm({ ...inviteForm, password: e.target.value })} />
          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1 block">Role</label>
            <select
              className="w-full h-10 rounded-md border border-border bg-background px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/60"
              value={inviteForm.role}
              onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
            >
              {Object.entries(ROLE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
          <Button onClick={() => createUser.mutate()} loading={createUser.isPending}>
            Add User
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
