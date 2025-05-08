import React from "react";
import cn from "classnames";

export function Card({ children, className="", ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("bg-white rounded-lg shadow", className)} {...props}>{children}</div>;
}

export function CardContent({ children, className="", ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-4", className)} {...props}>{children}</div>;
}
