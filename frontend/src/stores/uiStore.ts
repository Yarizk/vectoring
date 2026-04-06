import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Page = 'chat' | 'pipeline' | 'dashboard';

interface UIState {
  // Panel visibility
  leftPanelOpen: boolean;
  rightPanelOpen: boolean;
  
  // Navigation
  activePage: Page;
  
  // Theme (always dark for this design)
  theme: 'dark';
  
  // Actions
  toggleLeftPanel: () => void;
  toggleRightPanel: () => void;
  setRightPanelOpen: (open: boolean) => void;
  setActivePage: (page: Page) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      leftPanelOpen: true,
      rightPanelOpen: true,
      activePage: 'chat',
      theme: 'dark',
      
      toggleLeftPanel: () => set((state) => ({ 
        leftPanelOpen: !state.leftPanelOpen 
      })),
      
      toggleRightPanel: () => set((state) => ({ 
        rightPanelOpen: !state.rightPanelOpen 
      })),
      
      setRightPanelOpen: (open) => set({ rightPanelOpen: open }),
      
      setActivePage: (page) => set({ activePage: page }),
    }),
    {
      name: 'ksei-ui-storage',
      partialize: (state) => ({ 
        leftPanelOpen: state.leftPanelOpen,
        rightPanelOpen: state.rightPanelOpen,
        activePage: state.activePage,
      }),
    }
  )
);
