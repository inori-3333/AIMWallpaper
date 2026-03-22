import { useState } from 'react'
import { TopNav } from './components/TopNav/TopNav'
import { AssetPanel } from './components/AssetPanel/AssetPanel'
import { PreviewPanel } from './components/PreviewPanel/PreviewPanel'
import { ChatPanel } from './components/ChatPanel/ChatPanel'
import { KnowledgePanel } from './components/KnowledgePanel/KnowledgePanel'
import { ErrorBoundary } from './components/common/ErrorBoundary'

function App() {
  const [activeTab, setActiveTab] = useState<'editor' | 'knowledge'>('editor')

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      <ErrorBoundary>
        <TopNav activeTab={activeTab} onTabChange={setActiveTab} />
      </ErrorBoundary>
      <main className="flex-1 flex min-h-0">
        <aside className="w-64 bg-gray-800 border-r border-gray-700 flex-shrink-0">
          <ErrorBoundary>
            <AssetPanel />
          </ErrorBoundary>
        </aside>
        <section className="flex-1 min-w-0">
          <ErrorBoundary>
            {activeTab === 'editor' ? <PreviewPanel /> : <KnowledgePanel />}
          </ErrorBoundary>
        </section>
        <aside className="w-80 bg-gray-800 border-l border-gray-700 flex-shrink-0">
          <ErrorBoundary>
            <ChatPanel />
          </ErrorBoundary>
        </aside>
      </main>
    </div>
  )
}

export default App
