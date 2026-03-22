import { useProjectStore } from '../../stores/projectStore'
import { usePreviewProject } from '../../api/hooks'

export function PreviewPanel() {
  const projectId = useProjectStore((s) => s.currentProjectId)
  const preview = usePreviewProject()

  const handlePreview = () => {
    if (projectId) preview.mutate(projectId)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-2 border-b border-gray-700 flex items-center justify-between">
        <span className="text-sm font-medium">Preview</span>
        {projectId && (
          <button
            onClick={handlePreview}
            disabled={preview.isPending}
            className="text-xs px-3 py-1 bg-blue-600 rounded hover:bg-blue-500 disabled:opacity-50"
          >
            {preview.isPending ? 'Loading...' : 'Refresh Preview'}
          </button>
        )}
      </div>
      <div className="flex-1 flex items-center justify-center">
        {!projectId ? (
          <p className="text-gray-500 text-sm">Select a project to preview</p>
        ) : preview.data?.preview_url ? (
          <img src={preview.data.preview_url} alt="Wallpaper preview" className="max-w-full max-h-full object-contain" />
        ) : preview.data && !preview.data.available ? (
          <div className="text-center text-gray-500">
            <p className="text-sm">Wallpaper Engine not available</p>
            <p className="text-xs mt-1">Install WE for live preview</p>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">Click "Refresh Preview" to render</p>
        )}
      </div>
    </div>
  )
}
