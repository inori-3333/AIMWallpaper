import { TopNav } from './components/TopNav/TopNav'
import { AssetPanel } from './components/AssetPanel/AssetPanel'
import { PreviewPanel } from './components/PreviewPanel/PreviewPanel'
import { ChatPanel } from './components/ChatPanel/ChatPanel'
import { ErrorBoundary } from './components/common/ErrorBoundary'

function App() {
  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      <ErrorBoundary>
        <TopNav />
      </ErrorBoundary>
      <main className="flex-1 flex min-h-0">
        <aside className="w-64 bg-gray-800 border-r border-gray-700 flex-shrink-0">
          <ErrorBoundary>
            <AssetPanel />
          </ErrorBoundary>
        </aside>
        <section className="flex-1 min-w-0">
          <ErrorBoundary>
            <PreviewPanel />
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
