import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {}

export const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, ...props }, ref) => {
    return (
      <label
        ref={ref}
        className={twMerge(
          clsx(
            "text-xs font-semibold uppercase tracking-wider text-slate-300 select-none",
            className
          )
        )}
        {...props}
      />
    );
  }
);

Label.displayName = "Label";
export default Label;
