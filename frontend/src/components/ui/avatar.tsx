import React from "react";
import { cn } from "@/lib/utils";

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string | null;
  fallback: string;
}

export const Avatar = ({ src, fallback, className, ...props }: AvatarProps) => {
  return (
    <div
      className={cn(
        "relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full border border-border bg-muted select-none items-center justify-center text-sm font-semibold text-muted-foreground",
        className
      )}
      {...props}
    >
      {src ? (
        <img src={src} alt="avatar" className="h-full w-full aspect-square object-cover" />
      ) : (
        <span>{fallback.slice(0, 2).toUpperCase()}</span>
      )}
    </div>
  );
};
