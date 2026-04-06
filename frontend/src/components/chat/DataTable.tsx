import { useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { cn, formatNumber, formatPercentage } from '@/lib/utils';

interface DataTableProps<TData> {
  data: TData[];
  columns: ColumnDef<TData>[];
  className?: string;
}

export function DataTable<TData>({ data, columns, className }: DataTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className={cn('overflow-x-auto rounded-lg border border-[var(--border)]', className)}>
      <table className="w-full text-sm">
        <thead className="bg-[var(--bg-elevated)]">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className={cn(
                    'px-4 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider',
                    header.column.getCanSort() && 'cursor-pointer select-none hover:text-[var(--text-primary)]'
                  )}
                  onClick={header.column.getToggleSortingHandler()}
                >
                  <div className="flex items-center gap-1">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getIsSorted() === 'asc' && (
                      <ChevronUp size={14} className="text-[var(--accent)]" />
                    )}
                    {header.column.getIsSorted() === 'desc' && (
                      <ChevronDown size={14} className="text-[var(--accent)]" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="divide-y divide-[var(--border)]">
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              className="hover:bg-[var(--bg-surface-hover)] transition-colors"
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-3 text-[var(--text-primary)]">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Helper component for rendering change values with colors
export function ChangeCell({ value }: { value: number }) {
  const isPositive = value >= 0;
  return (
    <span
      className={cn(
        'font-medium',
        isPositive ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'
      )}
    >
      {isPositive ? '▲' : '▼'} {formatPercentage(Math.abs(value))}
    </span>
  );
}

// Helper for percentage bars
export function PercentageBar({ value, max = 100 }: { value: number; max?: number }) {
  const percentage = Math.min((value / max) * 100, 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-[var(--bg-elevated)] rounded-full overflow-hidden">
        <div
          className="h-full bg-[var(--accent)] rounded-full transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs text-[var(--text-secondary)] w-12 text-right">
        {formatPercentage(value)}
      </span>
    </div>
  );
}

// Predefined columns for common financial data
export const tickerColumns: ColumnDef<any>[] = [
  {
    accessorKey: 'ticker',
    header: 'Ticker',
    cell: ({ getValue }) => (
      <span className="font-semibold text-[var(--accent)]">{getValue() as string}</span>
    ),
  },
  {
    accessorKey: 'company',
    header: 'Company',
    cell: ({ getValue }) => (
      <span className="text-[var(--text-secondary)]">{getValue() as string}</span>
    ),
  },
  {
    accessorKey: 'change',
    header: 'Change',
    cell: ({ getValue }) => <ChangeCell value={getValue() as number} />,
  },
  {
    accessorKey: 'current',
    header: 'Current',
    cell: ({ getValue }) => (
      <span className="font-medium">{formatPercentage(getValue() as number)}</span>
    ),
  },
];
