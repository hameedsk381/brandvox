"use client";

import React from "react";
import { useAuthStore } from "@/stores/auth-store";
import { useBrandingStore } from "@/stores/branding-store";
import TenantSwitcher from "./tenant-switcher";
import { Avatar } from "@/components/ui/avatar";
import { useLogout } from "@/hooks/use-auth";
import { Bell, LogOut, Menu } from "lucide-react";
import { cn } from "@/lib/utils";

interface TopbarProps {
  onMenuToggle: () => void;
}

export default function Topbar({ onMenuToggle }: TopbarProps) {
  const user = useAuthStore((state) => state.user);
  const config = useBrandingStore((state) => state.brandingConfig);
  const logout = useLogout();

  return (
    <header className="h-16 bg-background border-b border-border flex items-center justify-between px-4 lg:px-6 sticky top-0 z-20">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuToggle}
          className="lg:hidden p-2 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
        >
          <Menu className="w-5 h-5" />
        </button>
        <TenantSwitcher />
      </div>

      <div className="flex items-center gap-3">
        <button className="relative p-2 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-destructive ring-2 ring-background" />
        </button>

        <div className="flex items-center gap-3 pl-3 border-l border-border">
          <Avatar fallback={user?.name || "U"} />
          <div className="hidden md:block">
            <div className="text-sm font-medium text-foreground">{user?.name}</div>
            <div className="text-[10px] text-muted-foreground uppercase tracking-wider">
              {user?.role?.replace("_", " ")}
            </div>
          </div>
          <button
            onClick={logout}
            className="p-2 rounded-md hover:bg-accent text-muted-foreground hover:text-destructive transition-colors cursor-pointer hidden md:block"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
