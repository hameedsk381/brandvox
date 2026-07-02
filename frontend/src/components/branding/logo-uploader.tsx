"use client";

import React, { useRef } from "react";
import { useBrandingStore } from "@/stores/branding-store";
import { Button } from "@/components/ui/button";
import { Upload } from "lucide-react";
import toast from "react-hot-toast";

export default function LogoUploader() {
  const inputRef = useRef<HTMLInputElement>(null);
  const config = useBrandingStore((state) => state.brandingConfig);

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast.error("Please upload an image file");
      return;
    }

    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target?.result as string;
      // Store in localStorage for POC (no blob storage)
      localStorage.setItem("brand-logo", dataUrl);
      toast.success("Logo uploaded (stored locally for POC)");
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="flex flex-col gap-2">
      <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Logo</label>
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-lg bg-muted border border-border flex items-center justify-center overflow-hidden">
          {config?.logo_url ? (
            <img src={config.logo_url} alt="logo" className="w-full h-full object-contain" />
          ) : (
            <span className="text-xl font-bold text-primary">R</span>
          )}
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleUpload}
        />
        <Button size="sm" variant="outline" onClick={() => inputRef.current?.click()}>
          <Upload className="w-3.5 h-3.5 mr-1" /> Upload
        </Button>
      </div>
    </div>
  );
}
