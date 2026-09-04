export function Card({
  children,
  className = "",
  title,
}: {
  children: React.ReactNode;
  className?: string;
  title?: string;
}) {
  return (
    <div className={`rounded-xl border border-white/10 bg-neutral-900/60 p-4 ${className}`}>
      {title && <h3 className="mb-3 text-sm font-medium text-neutral-300">{title}</h3>}
      {children}
    </div>
  );
}
