"use client";

import React, { useRef } from "react";
import { cn } from "@/lib/utils";

interface Props {
 label: string;
 value: string;
 onChange: (color: string) => void;
}

export default function ColorPicker({ label, value, onChange }: Props) {
 const inputRef = useRef<HTMLInputElement>(null);

 return (
 <div className="flex flex-col gap-1.5">
 <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">{label}</label>
 <button
 type="button"
 onClick={() => inputRef.current?.click()}
 className={cn(
 "h-10 rounded-md border border-border flex items-center gap-2 px-3 cursor-pointer hover:border-foreground/50 transition-colors",
 "bg-background"
 )}
 >
 <div className="w-5 h-5 rounded-full border border-border shrink-0" style={{ backgroundColor: value }} />
 <span className="text-xs font-mono text-muted-foreground">{value}</span>
 </button>
 <input
 ref={inputRef}
 type="color"
 value={value}
 onChange={(e) => onChange(e.target.value)}
 className="sr-only"
 />
 </div>
 );
}
