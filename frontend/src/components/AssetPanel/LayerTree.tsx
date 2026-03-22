import type { Asset } from '../../types'
import { useDeleteAsset } from '../../api/hooks'

interface Props {
  assets: Asset[]
}

export function LayerTree({ assets }: Props) {
  const deleteAsset = useDeleteAsset()

  if (assets.length === 0) {
    return <p className="text-sm text-gray-500 py-2">No assets uploaded yet</p>
  }

  return (
    <ul className="space-y-1">
      {assets.map((asset) => (
        <li key={asset.asset_id} className="flex items-center justify-between group px-2 py-1 rounded hover:bg-gray-700">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-xs text-gray-400">
              {asset.content_type.startsWith('image') ? '\u{1F5BC}' : asset.content_type.startsWith('video') ? '\u{1F3AC}' : '\u{1F4C4}'}
            </span>
            <span className="text-sm text-gray-200 truncate">{asset.filename}</span>
          </div>
          <button
            onClick={() => deleteAsset.mutate(asset.asset_id)}
            className="text-xs text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            \u2715
          </button>
        </li>
      ))}
    </ul>
  )
}
