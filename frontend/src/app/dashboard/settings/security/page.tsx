"use client";

import React, { useState, useEffect } from "react";
import { useCurrentUser, useChangePassword, useExportMyData, useDeleteMyAccount } from "@/hooks/use-auth";
import { authAPI } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import toast from "react-hot-toast";

export default function SecurityPage() {
  const user = useCurrentUser();
  const changePassword = useChangePassword();
  const exportMyData = useExportMyData();
  const deleteAccount = useDeleteMyAccount();

  // Password change form
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pwError, setPwError] = useState("");

  // MFA
  const [mfaEnabled, setMfaEnabled] = useState(user?.mfa_enabled || false);
  const [mfaSecret, setMfaSecret] = useState("");
  const [mfaUri, setMfaUri] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [mfaStep, setMfaStep] = useState<"idle" | "setup" | "verify">("idle");
  const [mfaError, setMfaError] = useState("");

  // Confirm delete
  const [confirmDelete, setConfirmDelete] = useState("");

  useEffect(() => {
    if (user) setMfaEnabled(user.mfa_enabled);
  }, [user]);

  const handleChangePassword = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setPwError("Passwords do not match");
      return;
    }
    setPwError("");
    changePassword.mutate(
      { current_password: currentPassword, new_password: newPassword },
      {
        onSuccess: () => { setCurrentPassword(""); setNewPassword(""); setConfirmPassword(""); },
        onError: (err: any) => setPwError(err?.response?.data?.detail || "Failed to change password"),
      }
    );
  };

  const handleSetupMfa = async () => {
    try {
      const res = await authAPI.setupMfa();
      setMfaSecret(res.secret);
      setMfaUri(res.uri);
      setMfaStep("setup");
      setMfaError("");
    } catch (err: any) {
      setMfaError(err?.response?.data?.detail || "Failed to setup MFA");
    }
  };

  const handleVerifyMfa = async () => {
    try {
      await authAPI.verifyMfa({ code: mfaCode });
      setMfaEnabled(true);
      setMfaStep("idle");
      setMfaCode("");
      toast.success("MFA enabled successfully");
    } catch (err: any) {
      setMfaError(err?.response?.data?.detail || "Invalid code");
    }
  };

  const handleDisableMfa = async () => {
    try {
      await authAPI.disableMfa({ code: mfaCode });
      setMfaEnabled(false);
      setMfaStep("idle");
      setMfaCode("");
      toast.success("MFA disabled");
    } catch (err: any) {
      setMfaError(err?.response?.data?.detail || "Invalid code");
    }
  };

  const handleExport = () => {
    exportMyData.mutate(undefined, {
      onSuccess: (data) => {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `reputationos-export-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success("Data exported");
      },
      onError: () => toast.error("Export failed"),
    });
  };

  const handleDeleteAccount = () => {
    if (confirmDelete !== "DELETE") {
      toast.error('Type "DELETE" to confirm');
      return;
    }
    deleteAccount.mutate(undefined, {
      onError: () => toast.error("Failed to delete account"),
    });
  };

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Security</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage your password, MFA, and data</p>
      </div>

      {/* Change Password */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Change Password</CardTitle>
          <CardDescription>Update your account password</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleChangePassword} className="flex flex-col gap-4">
            {pwError && <p className="text-sm text-destructive">{pwError}</p>}
            <Input label="Current Password" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
            <Input label="New Password" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
            <Input label="Confirm New Password" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
            <Button type="submit" loading={changePassword.isPending} className="w-fit">
              Update Password
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* MFA */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Multi-Factor Authentication</CardTitle>
          <CardDescription>{mfaEnabled ? "MFA is currently enabled" : "Add an extra layer of security"}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {mfaError && <p className="text-sm text-destructive">{mfaError}</p>}

          {mfaStep === "setup" && (
            <div className="flex flex-col gap-3 p-4 bg-accent/30 rounded-lg">
              <p className="text-sm text-muted-foreground">
                Scan this QR code with your authenticator app (e.g., Google Authenticator, Authy):
              </p>
              <div className="flex justify-center">
                <img src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(mfaUri)}`} alt="MFA QR Code" className="rounded-lg border" />
              </div>
              <p className="text-xs text-muted-foreground text-center">
                Or enter this key manually: <code className="text-foreground font-mono bg-accent px-1 rounded">{mfaSecret}</code>
              </p>
              <div className="flex items-end gap-2">
                <Input label="Verification Code" placeholder="000000" value={mfaCode} onChange={(e) => setMfaCode(e.target.value)} maxLength={6} />
                <Button onClick={handleVerifyMfa} disabled={mfaCode.length < 6}>Verify</Button>
              </div>
            </div>
          )}

          {mfaStep === "idle" && !mfaEnabled && (
            <Button onClick={handleSetupMfa} variant="outline" className="w-fit">Enable MFA</Button>
          )}

          {mfaEnabled && mfaStep === "idle" && (
            <div className="flex flex-col gap-3">
              <p className="text-xs text-muted-foreground">Enter a code from your authenticator app to disable MFA:</p>
              <div className="flex items-end gap-2">
                <Input label="Verification Code" placeholder="000000" value={mfaCode} onChange={(e) => setMfaCode(e.target.value)} maxLength={6} />
                <Button onClick={handleDisableMfa} variant="destructive" disabled={mfaCode.length < 6}>Disable MFA</Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Export & Delete */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Data & Privacy</CardTitle>
          <CardDescription>Export or delete your personal data</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div>
            <p className="text-sm text-muted-foreground mb-2">Download all your data in JSON format (GDPR compliant).</p>
            <Button onClick={handleExport} variant="outline" loading={exportMyData.isPending}>
              Export My Data
            </Button>
          </div>
          <div className="border-t border-border pt-4">
            <p className="text-sm text-destructive font-medium mb-1">Danger Zone</p>
            <p className="text-xs text-muted-foreground mb-2">Permanently deletes your account and anonymizes your data. This cannot be undone.</p>
            <div className="flex items-end gap-2">
              <Input label='Type "DELETE" to confirm' value={confirmDelete} onChange={(e) => setConfirmDelete(e.target.value)} placeholder="DELETE" />
              <Button onClick={handleDeleteAccount} variant="destructive" disabled={confirmDelete !== "DELETE"} loading={deleteAccount.isPending}>
                Delete Account
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}