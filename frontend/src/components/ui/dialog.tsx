import React from "react";
import { cn } from "@/lib/utils";

export interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const Dialog = ({ isOpen, onClose, title, children, className }: DialogProps) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm cursor-pointer transition-opacity duration-300"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div 
        className={cn(
          "relative w-full max-w-lg rounded-xl border border-border bg-background p-6 shadow-2xl z-10 animate-in fade-in-50 zoom-in-95 duration-200 text-foreground flex flex-col gap-4 max-h-[90vh] overflow-y-auto",
          className
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          {title && <h2 className="text-lg font-bold tracking-tight">{title}</h2>}
          <button 
            onClick={onClose}
            className="rounded-full p-1.5 hover:bg-accent text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Body */}
        <div className="flex-1">{children}</div>
      </div>
    </div>
  );
};
