import { Header } from './Header';
import { LeftSidebar } from './LeftSidebar';
import { RightPanel } from './RightPanel';
import { useUIStore } from '@/stores';
import { cn } from '@/lib/utils';

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const { leftPanelOpen, rightPanelOpen } = useUIStore();

  return (
    <div className="flex flex-col h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] overflow-hidden">
      <Header />
      
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <aside
          className={cn(
            'flex-shrink-0 border-r border-[var(--border)] bg-[var(--bg-surface)] transition-all duration-300',
            leftPanelOpen ? 'w-[260px]' : 'w-0 overflow-hidden'
          )}
        >
          <LeftSidebar />
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden bg-[var(--bg-primary)]">
          {children}
        </main>

        {/* Right Panel */}
        <aside
          className={cn(
            'flex-shrink-0 border-l border-[var(--border)] bg-[var(--bg-surface)] transition-all duration-300',
            rightPanelOpen ? 'w-[380px]' : 'w-0 overflow-hidden'
          )}
        >
          <RightPanel />
        </aside>
      </div>
    </div>
  );
}
