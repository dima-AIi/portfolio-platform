import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  children: ReactNode;
}

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  // A bare <button> inside a <form> submits it. Several call sites render
  // Button inside forms for actions that are not "save" (tabs, filters,
  // toggles), so default to an inert button and let callers pass
  // type="submit" explicitly where submission is actually intended.
  type = "button",
  children,
  ...rest
}: ButtonProps) {
  return (
    <button type={type} className={`btn btn-${variant} btn-${size} ${className}`} {...rest}>
      {children}
    </button>
  );
}
