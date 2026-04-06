import { LayoutDashboard, BarChart3, TrendingUp, PieChart } from 'lucide-react';

export function DashboardPage() {
  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Dashboard</h1>
          <p className="text-[var(--text-secondary)] mt-1">
            Overview of market data and analytics
          </p>
        </div>
      </div>

      {/* Placeholder Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <PlaceholderCard
          icon={BarChart3}
          title="Market Overview"
          description="Top gainers, losers, and volume leaders"
        />
        <PlaceholderCard
          icon={TrendingUp}
          title="Foreign Flow"
          description="Daily foreign buying/selling by sector"
        />
        <PlaceholderCard
          icon={PieChart}
          title="Sector Analysis"
          description="Ownership breakdown by industry"
        />
        <PlaceholderCard
          icon={LayoutDashboard}
          title="Custom Reports"
          description="Saved queries and scheduled reports"
        />
      </div>

      {/* Coming Soon Notice */}
      <div className="p-8 rounded-xl bg-[var(--bg-surface)] border border-[var(--border)] text-center">
        <LayoutDashboard size={48} className="mx-auto mb-4 text-[var(--accent)] opacity-50" />
        <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-2">
          Dashboard Coming Soon
        </h2>
        <p className="text-[var(--text-secondary)] max-w-md mx-auto">
          This dashboard will integrate with Stockbit API to provide real-time market data, 
          foreign flow analysis, and sector breakdowns.
        </p>
        <div className="mt-6 flex items-center justify-center gap-4 text-sm text-[var(--text-muted)]">
          <span className="px-3 py-1 rounded-full bg-[var(--bg-elevated)]">Stockbit Integration</span>
          <span className="px-3 py-1 rounded-full bg-[var(--bg-elevated)]">Real-time Data</span>
          <span className="px-3 py-1 rounded-full bg-[var(--bg-elevated)]">Custom Reports</span>
        </div>
      </div>
    </div>
  );
}

function PlaceholderCard({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
}) {
  return (
    <div className="p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border)] opacity-60">
      <Icon size={24} className="text-[var(--accent)] mb-3" />
      <h3 className="font-medium text-[var(--text-primary)] mb-1">{title}</h3>
      <p className="text-sm text-[var(--text-secondary)]">{description}</p>
    </div>
  );
}
