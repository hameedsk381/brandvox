"use client";

import React from "react";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-border bg-background py-12">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8">
        <div className="col-span-2 md:col-span-1">
          <Link href="/" className="flex items-center gap-3 group mb-4">
            <div className="w-8 h-8 rounded-lg bg-foreground flex items-center justify-center text-background font-black text-sm">
              R
            </div>
            <span className="font-semibold tracking-tight">ReputationOS</span>
          </Link>
          <p className="text-sm text-muted-foreground max-w-xs">
            The intelligent way to manage your brand reputation at scale. Built for modern agencies and multi-location businesses.
          </p>
        </div>
        
        <div>
          <h4 className="font-semibold text-foreground mb-4 text-sm">Platform</h4>
          <ul className="flex flex-col gap-3 text-sm text-muted-foreground">
            <li><Link href="#features" className="hover:text-foreground transition-colors">Features</Link></li>
            <li><Link href="#" className="hover:text-foreground transition-colors">Integrations</Link></li>
            <li><Link href="#pricing" className="hover:text-foreground transition-colors">Pricing</Link></li>
            <li><Link href="#" className="hover:text-foreground transition-colors">Changelog</Link></li>
          </ul>
        </div>
        
        <div>
          <h4 className="font-semibold text-foreground mb-4 text-sm">Company</h4>
          <ul className="flex flex-col gap-3 text-sm text-muted-foreground">
            <li><Link href="#" className="hover:text-foreground transition-colors">About</Link></li>
            <li><Link href="#" className="hover:text-foreground transition-colors">Blog</Link></li>
            <li><Link href="#" className="hover:text-foreground transition-colors">Careers</Link></li>
            <li><Link href="#" className="hover:text-foreground transition-colors">Contact</Link></li>
          </ul>
        </div>
        
        <div>
          <h4 className="font-semibold text-foreground mb-4 text-sm">Legal</h4>
          <ul className="flex flex-col gap-3 text-sm text-muted-foreground">
            <li><Link href="#" className="hover:text-foreground transition-colors">Privacy Policy</Link></li>
            <li><Link href="#" className="hover:text-foreground transition-colors">Terms of Service</Link></li>
            <li><Link href="#" className="hover:text-foreground transition-colors">Cookie Policy</Link></li>
          </ul>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-6 mt-12 pt-8 border-t border-border flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
        <p>© {new Date().getFullYear()} ReputationOS AI. All rights reserved.</p>
        <p>Built with ❤️ by the Google Antigravity Team.</p>
      </div>
    </footer>
  );
}
