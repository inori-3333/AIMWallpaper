import { useState } from 'react'
import { useProjects, useCreateProject } from '../../api/hooks'
import { useProjectStore } from '../../stores/projectStore'
import { useChatStore } from '../../stores/chatStore'

export function TopNav() {
  const { data: projects = [] } = useProjects()
  const createProject = useCreateProject()
  const { currentProjectId, setCurrentProject } = useProjectStore()
  const clearMessages = useChatStore((s) => s.clearMessages)
  const [showNew, setShowNew] = useState(false)
  const [newName, setNewName] = useState('')

  const handleCreate = () => {
    if (!newName.trim()) return
    createProject.mutate({ name: newName.trim() }, {
      onSuccess: (project) => {
        setCurrentProject(project.project_id)
        clearMessages()
        setNewName('')
        setShowNew(false)
      },
    })
  }

  const handleSelect = (id: string) => {
    setCurrentProject(id)
    clearMessages()
  }

  return (
    <header className="h-12 bg-gray-800 flex items-center px-4 border-b border-gray-700 gap-4">
      <h1 className="text-lg font-semibold whitespace-nowrap">AIMWallpaper</h1>

      <select
        value={currentProjectId || ''}
        onChange={(e) => handleSelect(e.target.value)}
        className="bg-gray-700 text-sm text-white rounded px-2 py-1 focus:outline-none"
      >
        <option value="">Select project...</option>
        {projects.map((p) => (
          <option key={p.project_id} value={p.project_id}>{p.name}</option>
        ))}
      </select>

      {showNew ? (
        <div className="flex gap-2">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Project name"
            className="bg-gray-700 text-sm text-white rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            autoFocus
          />
          <button onClick={handleCreate} className="text-xs px-2 py-1 bg-blue-600 rounded hover:bg-blue-500">Create</button>
          <button onClick={() => setShowNew(false)} className="text-xs px-2 py-1 bg-gray-600 rounded hover:bg-gray-500">Cancel</button>
        </div>
      ) : (
        <button onClick={() => setShowNew(true)} className="text-xs px-3 py-1 bg-blue-600 rounded hover:bg-blue-500">
          + New Project
        </button>
      )}
    </header>
  )
}
