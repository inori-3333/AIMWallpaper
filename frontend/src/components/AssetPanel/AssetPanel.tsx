import { AssetUpload } from './AssetUpload'
import { LayerTree } from './LayerTree'
import { useAssets } from '../../api/hooks'

export function AssetPanel() {
  const { data: assets = [], isLoading } = useAssets()

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-2 border-b border-gray-700">
        <span className="text-sm font-medium">Assets & Layers</span>
      </div>
      <div className="p-3">
        <AssetUpload />
      </div>
      <div className="flex-1 overflow-y-auto px-3 pb-3">
        <h3 className="text-xs font-medium text-gray-400 uppercase mb-2">Files</h3>
        {isLoading ? (
          <p className="text-sm text-gray-500">Loading...</p>
        ) : (
          <LayerTree assets={assets} />
        )}
      </div>
    </div>
  )
}
