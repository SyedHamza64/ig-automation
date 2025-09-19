import type { ReactNode, HTMLAttributes } from "react";

export function Table({ children, className = "", ...rest }: HTMLAttributes<HTMLDivElement> & { children: ReactNode }) {
  return (
    <div className={`overflow-x-auto ${className}`} {...rest}>
      <table className="min-w-full text-sm">{children}</table>
    </div>
  );
}

export function THead({ children, className = "", ...rest }: HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead className={`bg-gray-50 text-left text-xs uppercase text-gray-500 ${className}`} {...rest}>
      {children}
    </thead>
  );
}

export function TBody({ children, className = "", ...rest }: HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody className={`divide-y ${className}`} {...rest}>
      {children}
    </tbody>
  );
}

export function TH({ children, className = "", ...rest }: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th className={`px-3 py-2 font-medium ${className}`} {...rest}>
      {children}
    </th>
  );
}

export function TD({ children, className = "", ...rest }: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={`px-3 py-2 align-top ${className}`} {...rest}>
      {children}
    </td>
  );
}
