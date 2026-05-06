import * as React from "react";

import { cn } from "./utils";

type InputProps = React.ComponentProps<"input"> & {
  label?: string;
  error?: string;
  fullWidth?: boolean;
  helperText?: string;
};

function Input({
  className,
  type,
  label,
  error,
  fullWidth = false,
  helperText,
  id,
  ...props
}: InputProps) {
  const inputElement = (
    <input
      id={id}
      type={type}
      data-slot="input"
        className={cn(
        "file:text-foreground placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground dark:bg-input/30 border-input flex h-9 w-full min-w-0 rounded-md border px-3 py-1 text-base bg-input-background transition-[color,box-shadow] outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
        "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
          error && "border-destructive",
          fullWidth && "w-full",
        className,
      )}
      {...props}
    />
  );

  if (!label) {
    return (
      <div className="grid gap-1.5">
        {inputElement}
        {!error && helperText ? (
          <span className="text-xs text-muted-foreground">{helperText}</span>
        ) : null}
        {error ? <span className="text-xs text-destructive">{error}</span> : null}
      </div>
    );
  }

  return (
    <label className="grid gap-1.5 text-sm font-medium text-foreground" htmlFor={id}>
      <span>{label}</span>
      {inputElement}
      {!error && helperText ? (
        <span className="text-xs text-muted-foreground">{helperText}</span>
      ) : null}
      {error ? <span className="text-xs text-destructive">{error}</span> : null}
    </label>
  );
}

export { Input };
