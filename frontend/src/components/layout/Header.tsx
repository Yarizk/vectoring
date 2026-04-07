import { Link, useLocation } from 'react-router-dom';
import { MessageSquare, Activity, LayoutDashboard, Menu, PanelRight } from 'lucide-react';
import { useUIStore } from '@/stores';
import { cn } from '@/lib/utils';
import { KseiLogo } from '@/components/ui/KseiLogo';

const navItems = [
  { path: '/chat', label: 'Chat', icon: MessageSquare },
  { path: '/pipeline', label: 'Pipeline', icon: Activity },
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
];

export function Header() {
  const location = useLocation();
  const { toggleLeftPanel, toggleRightPanel, leftPanelOpen, rightPanelOpen } = useUIStore();

  return (
    <header className="h-[40px] flex items-center justify-between px-3 border-b border-[var(--border)] bg-[var(--bg-surface)]">
      {/* Left Section */}
      <div className="flex items-center gap-2">
        <button
          onClick={toggleLeftPanel}
          className={cn(
            'p-1.5 rounded transition-colors',
            'hover:bg-[var(--bg-surface-hover)] text-[var(--text-secondary)]',
            leftPanelOpen && 'bg-[var(--bg-elevated)] text-[var(--text-primary)]'
          )}
          title="Toggle sidebar"
        >
          <Menu size={15} />
        </button>

        <Link to="/" className="flex items-center gap-1.5">
          <KseiLogo size={20} />
          <span className="font-semibold text-sm tracking-tight">
            KSEI <span className="text-[var(--accent)]">Intelligence</span>
          </span>
        </Link>
      </div>

      {/* Center Navigation */}
      <nav className="flex items-center gap-0.5">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path ||
            (item.path === '/chat' && location.pathname === '/');

          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors',
                isActive
                  ? 'bg-[var(--bg-elevated)] text-[var(--text-primary)]'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-hover)] hover:text-[var(--text-primary)]'
              )}
            >
              <Icon size={13} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Right Section */}
      <div className="flex items-center gap-1">
        <button
          onClick={toggleRightPanel}
          className={cn(
            'p-1.5 rounded transition-colors',
            'hover:bg-[var(--bg-surface-hover)] text-[var(--text-secondary)]',
            rightPanelOpen && 'bg-[var(--bg-elevated)] text-[var(--text-primary)]'
          )}
          title="Toggle context panel"
        >
          <PanelRight size={15} />
        </button>
      </div>
    </header>
  );
}
