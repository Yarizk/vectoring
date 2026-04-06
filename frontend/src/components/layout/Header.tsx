import { Link, useLocation } from 'react-router-dom';
import { 
  MessageSquare, 
  Activity, 
  LayoutDashboard, 
  Menu, 
  PanelRight,
  Database,
} from 'lucide-react';
import { useUIStore } from '@/stores';
import { cn } from '@/lib/utils';

const navItems = [
  { path: '/chat', label: 'Chat', icon: MessageSquare },
  { path: '/pipeline', label: 'Pipeline', icon: Activity },
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
];

export function Header() {
  const location = useLocation();
  const { toggleLeftPanel, toggleRightPanel, leftPanelOpen, rightPanelOpen } = useUIStore();

  return (
    <header className="h-[60px] flex items-center justify-between px-4 border-b border-[var(--border)] bg-[var(--bg-surface)]">
      {/* Left Section */}
      <div className="flex items-center gap-3">
        <button
          onClick={toggleLeftPanel}
          className={cn(
            'p-2 rounded-lg transition-colors',
            'hover:bg-[var(--bg-surface-hover)] text-[var(--text-secondary)]',
            leftPanelOpen && 'bg-[var(--bg-elevated)] text-[var(--text-primary)]'
          )}
          title="Toggle sidebar"
        >
          <Menu size={20} />
        </button>
        
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[var(--accent)] flex items-center justify-center">
            <Database size={18} className="text-white" />
          </div>
          <span className="font-semibold text-lg tracking-tight">
            KSEI <span className="text-[var(--accent)]">Intelligence</span>
          </span>
        </Link>
      </div>

      {/* Center Navigation */}
      <nav className="flex items-center gap-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path || 
            (item.path === '/chat' && location.pathname === '/');
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-[var(--bg-elevated)] text-[var(--text-primary)]'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-hover)] hover:text-[var(--text-primary)]'
              )}
            >
              <Icon size={16} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Right Section */}
      <div className="flex items-center gap-2">
        <button
          onClick={toggleRightPanel}
          className={cn(
            'p-2 rounded-lg transition-colors',
            'hover:bg-[var(--bg-surface-hover)] text-[var(--text-secondary)]',
            rightPanelOpen && 'bg-[var(--bg-elevated)] text-[var(--text-primary)]'
          )}
          title="Toggle context panel"
        >
          <PanelRight size={20} />
        </button>
      </div>
    </header>
  );
}
