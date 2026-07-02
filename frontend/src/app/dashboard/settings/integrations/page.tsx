"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/stores/auth-store";
import { KeyRound, ExternalLink, Save, RefreshCw } from "lucide-react";
import toast from "react-hot-toast";
import { api } from "@/lib/api";

export default function IntegrationSettingsPage() {
  const user = useAuthStore((state) => state.user);
  const agencyId = user?.agency_id;
  
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [hasSecret, setHasSecret] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (agencyId) {
      fetchCredentials();
    }
  }, [agencyId]);

  const fetchCredentials = async () => {
    try {
      setIsLoading(true);
      const { data } = await api.get(`/api/agencies/${agencyId}/google-credentials`);
      if (data.client_id) setClientId(data.client_id);
      if (data.has_secret) setHasSecret(true);
    } catch (error) {
      console.error("Failed to fetch credentials", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!agencyId) return;
    if (!clientId.trim() || (!hasSecret && !clientSecret.trim())) {
      toast.error("Both Client ID and Client Secret are required");
      return;
    }
    
    try {
      setIsSaving(true);
      await api.put(`/api/agencies/${agencyId}/google-credentials`, {
 client_id: clientId,
 client_secret: clientSecret
 });
 toast.success("Google OAuth Credentials saved successfully");
 setHasSecret(true);
 setClientSecret(""); // Clear secret from UI for security
 } catch (error) {
 toast.error("Failed to save credentials");
 } finally {
 setIsSaving(false);
 }
 };

 if (isLoading) {
 return <div className="flex justify-center p-12"><RefreshCw className="w-6 h-6 animate-spin text-primary" /></div>;
 }

 return (
 <div className="max-w-4xl mx-auto flex flex-col gap-6">
 <div>
 <h1 className="text-2xl font-bold text-foreground ">Integration Settings</h1>
 <p className="text-sm text-muted-foreground dark:text-muted-foreground mt-1">Manage global API credentials for your agency</p>
 </div>

 <Card className="bg-background/5 backdrop-blur-xl border-border dark:bg-[#0a0a0f]/50">
 <CardHeader>
 <div className="flex items-center gap-2">
 <KeyRound className="w-5 h-5 text-primary" />
 <CardTitle>Google Business Profile OAuth</CardTitle>
 </div>
 <CardDescription>
 Configure your Google Cloud Platform credentials. This allows your clients to connect their Google accounts directly to your white-labeled application.
 </CardDescription>
 </CardHeader>
 <CardContent className="flex flex-col gap-6">
 
 <div className="p-4 rounded-lg bg-primary/10 border border-primary/20 text-sm text-primary flex flex-col gap-2">
 <p><strong>Setup Instructions:</strong></p>
 <ol className="list-decimal list-inside space-y-1">
 <li>Go to the <a href="https://console.cloud.google.com" target="_blank" rel="noreferrer" className="underline font-medium hover:text-primary/80 inline-flex items-center">Google Cloud Console <ExternalLink className="w-3 h-3 ml-1" /></a></li>
 <li>Create a new Project and enable the <strong>Google Business Profile API</strong></li>
 <li>Configure the OAuth Consent Screen</li>
 <li>Create OAuth 2.0 Client IDs (Web application)</li>
 <li>Add this Authorized redirect URI: <code>{typeof window !== 'undefined' ? window.location.origin : 'https://yourdomain.com'}/dashboard/integrations</code></li>
 </ol>
 </div>

 <div className="grid gap-4">
 <div className="space-y-2">
 <label className="text-sm font-medium text-foreground ">Google Client ID</label>
 <Input
 placeholder="e.g. 1234567890-abc...apps.googleusercontent.com"
 value={clientId}
 onChange={(e) => setClientId(e.target.value)}
 />
 </div>
 
 <div className="space-y-2">
 <label className="text-sm font-medium text-foreground flex justify-between">
 <span>Google Client Secret</span>
 {hasSecret && <span className="text-emerald-500 text-xs flex items-center">✓ Secret is configured</span>}
 </label>
 <Input
 type="password"
 placeholder={hasSecret ? "•••••••••••••••• (Leave blank to keep existing)" : "Enter Client Secret"}
 value={clientSecret}
 onChange={(e) => setClientSecret(e.target.value)}
 />
 <p className="text-xs text-muted-foreground">The secret is encrypted and never exposed in the API after saving.</p>
 </div>
 </div>
 
 <div className="flex justify-end">
 <Button onClick={handleSave} disabled={isSaving}>
 {isSaving ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
 Save Credentials
 </Button>
 </div>
 </CardContent>
 </Card>
 </div>
 );
}
