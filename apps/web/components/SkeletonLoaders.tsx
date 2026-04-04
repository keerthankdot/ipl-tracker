export function SkeletonBar() {
  return (
    <div className="flex items-center gap-4">
      <div className="w-12 h-4 bg-surface-2 rounded animate-pulse" />
      <div className="flex-1 h-8 bg-surface-2 rounded-lg animate-pulse" />
      <div className="w-16 h-6 bg-surface-2 rounded animate-pulse" />
    </div>
  );
}

export function SkeletonRow() {
  return (
    <tr>
      {Array.from({ length: 7 }).map((_, i) => (
        <td key={i} className="py-2 px-2">
          <div className="h-4 bg-surface-2 rounded animate-pulse" />
        </td>
      ))}
    </tr>
  );
}

export function SkeletonCard() {
  return (
    <div className="bg-surface rounded-lg p-4 border border-border/50 animate-pulse">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="h-4 w-20 bg-surface-2 rounded" />
          <div className="h-4 w-16 bg-surface-2 rounded" />
        </div>
        <div className="h-3 w-12 bg-surface-2 rounded" />
      </div>
      <div className="h-3 w-32 bg-surface-2 rounded mb-3" />
      <div className="flex items-center gap-3">
        <div className="flex-1 h-2 bg-surface-2 rounded-full" />
        <div className="h-4 w-10 bg-surface-2 rounded" />
      </div>
    </div>
  );
}
