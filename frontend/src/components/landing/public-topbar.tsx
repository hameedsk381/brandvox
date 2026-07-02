"use client";

import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function PublicTopbar() {
  return (
    <nav className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-md border-b border-border transition-all duration-300">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-foreground flex items-center justify-center text-background font-black text-sm group-hover:scale-105 transition-transform">
            R
          </div>
          <span className="font-semibold text-lg tracking-tight">ReputationOS</span>
        </Link>
        
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
          <Link href="#features" className="hover:text-foreground transition-colors">Features</Link>
          <Link href="#showcase" className="hover:text-foreground transition-colors">Platform</Link>
          <Link href="#pricing" className="hover:text-foreground transition-colors">Pricing</Link>
        </div>

        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
            Sign In
          </Link>
          <Button asChild className="hidden sm:inline-flex rounded-full px-6">
            <Link href="/register">Get Started</Link>
          </Button>
        </div>
      </div>
    </nav>
  );
}
