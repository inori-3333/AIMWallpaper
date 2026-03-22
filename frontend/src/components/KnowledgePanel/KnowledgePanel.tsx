import { useState } from 'react'
import {
  useExamples,
  useImportExample,
  useScanWorkshop,
  usePatterns,
  useVerifyPattern,
  useDeletePattern,
} from '../../api/hooks'
import type { EffectPattern, ExampleEntry } from '../../types'

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color = value >= 0.8 ? 'bg-green-500' : value >= 0.5 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-400 w-8 text-right">{pct}%</span>
    </div>
  )
}

function ImportSection() {
  const [path, setPath] = useState('')
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const { data: examples = [] } = useExamples()
  const importOne = useImportExample()
  const scanAll = useScanWorkshop()

  const showMsg = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 5000)
  }

  const handleImport = () => {
    if (!path.trim()) return
    importOne.mutate(path.trim(), {
      onSuccess: (entry) => showMsg('success', `imported "${entry.title}" (${entry.object_count} objects)`),
      onError: (err) => showMsg('error', err.message),
    })
  }

  const handleScan = () => {
    if (!path.trim()) return
    scanAll.mutate(path.trim(), {
      onSuccess: (res) => showMsg('success', `scanned ${res.imported_count} projects (total: ${res.total_count})`),
      onError: (err) => showMsg('error', err.message),
    })
  }

  const isLoading = importOne.isPending || scanAll.isPending

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Import Examples</h2>

      <div className="flex gap-2">
        <input
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="WE project folder or workshop directory path..."
          className="flex-1 bg-gray-700 text-sm text-white rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
          onKeyDown={(e) => e.key === 'Enter' && handleImport()}
        />
        <button
          onClick={handleImport}
          disabled={isLoading || !path.trim()}
          className="text-xs px-3 py-1.5 bg-blue-600 rounded hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {importOne.isPending ? 'Importing...' : 'Import'}
        </button>
        <button
          onClick={handleScan}
          disabled={isLoading || !path.trim()}
          className="text-xs px-3 py-1.5 bg-green-600 rounded hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {scanAll.isPending ? 'Scanning...' : 'Batch Scan'}
        </button>
      </div>

      {message && (
        <div className={`text-xs px-3 py-2 rounded ${message.type === 'success' ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
          {message.text}
        </div>
      )}

      {examples.length > 0 && (
        <div className="overflow-auto max-h-48">
          <table className="w-full text-xs text-left">
            <thead className="text-gray-400 border-b border-gray-700">
              <tr>
                <th className="py-1.5 pr-3">Title</th>
                <th className="py-1.5 pr-3">Type</th>
                <th className="py-1.5 pr-3">Tags</th>
                <th className="py-1.5 pr-3">Objects</th>
              </tr>
            </thead>
            <tbody className="text-gray-300">
              {examples.map((ex: ExampleEntry, i: number) => (
                <tr key={i} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                  <td className="py-1.5 pr-3">{ex.title || 'Untitled'}</td>
                  <td className="py-1.5 pr-3">{ex.type}</td>
                  <td className="py-1.5 pr-3">{ex.tags?.join(', ') || '-'}</td>
                  <td className="py-1.5 pr-3">{ex.object_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function PatternCard({ pattern, onVerify, onDelete }: {
  pattern: EffectPattern
  onVerify: () => void
  onDelete: () => void
}) {
  return (
    <div className="bg-gray-700/50 rounded-lg p-3 space-y-2">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-sm font-medium text-white">{pattern.name}</span>
          {pattern.verified && (
            <span className="ml-2 text-[10px] px-1.5 py-0.5 bg-green-800 text-green-300 rounded">verified</span>
          )}
        </div>
        <div className="flex gap-1 flex-shrink-0">
          {!pattern.verified && (
            <button onClick={onVerify} className="text-[10px] px-2 py-0.5 bg-blue-600 rounded hover:bg-blue-500">
              Verify
            </button>
          )}
          <button onClick={onDelete} className="text-[10px] px-2 py-0.5 bg-red-600 rounded hover:bg-red-500">
            Delete
          </button>
        </div>
      </div>
      {pattern.description && (
        <p className="text-xs text-gray-400 line-clamp-2">{pattern.description}</p>
      )}
      <div className="flex gap-2 text-[10px] text-gray-500">
        {pattern.category && <span className="px-1.5 py-0.5 bg-gray-600 rounded">{pattern.category}</span>}
        {pattern.tags && pattern.tags.split(',').filter(Boolean).map((tag) => (
          <span key={tag.trim()} className="px-1.5 py-0.5 bg-gray-600 rounded">{tag.trim()}</span>
        ))}
      </div>
      <ConfidenceBar value={pattern.confidence} />
    </div>
  )
}

function PatternSection() {
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState<string | undefined>(undefined)
  const { data: patterns = [] } = usePatterns(query)
  const verifyPattern = useVerifyPattern()
  const deletePattern = useDeletePattern()

  const handleSearch = () => {
    setQuery(search.trim() || undefined)
  }

  return (
    <div className="space-y-3 flex-1 min-h-0 flex flex-col">
      <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Effect Patterns</h2>

      <div className="flex gap-2">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search patterns..."
          className="flex-1 bg-gray-700 text-sm text-white rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button
          onClick={handleSearch}
          className="text-xs px-3 py-1.5 bg-blue-600 rounded hover:bg-blue-500 whitespace-nowrap"
        >
          Search
        </button>
      </div>

      {patterns.length === 0 ? (
        <p className="text-xs text-gray-500 text-center py-8">No patterns found. Import examples to build your knowledge base.</p>
      ) : (
        <div className="flex-1 overflow-auto space-y-2">
          {patterns.map((p: EffectPattern) => (
            <PatternCard
              key={p.id}
              pattern={p}
              onVerify={() => verifyPattern.mutate(p.id)}
              onDelete={() => deletePattern.mutate(p.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function KnowledgePanel() {
  return (
    <div className="h-full flex flex-col gap-4 p-4 overflow-hidden">
      <ImportSection />
      <div className="border-t border-gray-700" />
      <PatternSection />
    </div>
  )
}
