import { Routes, Route } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { ChatPage } from '@/pages/ChatPage';
import { PipelinePage } from '@/pages/PipelinePage';
import { DashboardPage } from '@/pages/DashboardPage';

function App() {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/pipeline" element={<PipelinePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Routes>
    </MainLayout>
  );
}

export default App;
