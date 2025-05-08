import React from "react";
import cn from "classnames";

export function Button({
  children,
  variant = "primary",
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" }) {
  const base = "px-4 py-2 rounded-lg font-medium";
  const style = variant === "primary"
    ? "bg-indigo-600 text-white hover:bg-indigo-700"
    : "bg-gray-200 text-gray-800 hover:bg-gray-300";
  return (
    <button className={cn(base, style, className)} {...props}>
      {children}
    </button>
  );
}
