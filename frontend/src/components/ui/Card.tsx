import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-2xl border bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800 ${className}`}>{children}</div>;
}

export function CardHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="border-b px-4 py-3 dark:border-gray-700">
      <div className="text-sm text-gray-500 dark:text-gray-400">{subtitle}</div>
      <h3 className="text-lg font-semibold leading-tight text-gray-900 dark:text-white">{title}</h3>
    </div>
  );
}

export function CardBody({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`px-4 py-4 ${className}`}>{children}</div>;
}