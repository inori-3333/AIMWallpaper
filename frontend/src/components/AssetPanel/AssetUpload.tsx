import { useCallback } from 'react'
import { useUploadAsset } from '../../api/hooks'

export function AssetUpload() {
  const upload = useUploadAsset()

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files)
    files.forEach((file) => upload.mutate(file))
  }, [upload])

  const handleDragOver = (e: React.DragEvent) => e.preventDefault()

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    files.forEach((file) => upload.mutate(file))
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      className="border-2 border-dashed border-gray-600 rounded-lg p-4 text-center cursor-pointer hover:border-blue-500 transition-colors"
    >
      <input
        type="file"
        onChange={handleFileSelect}
        className="hidden"
        id="asset-upload"
        multiple
        accept="image/*,video/*,audio/*,.pkg,.json"
      />
      <label htmlFor="asset-upload" className="cursor-pointer">
        <p className="text-sm text-gray-400">Drop files here or click to upload</p>
        <p className="text-xs text-gray-500 mt-1">Images, videos, audio, .pkg files</p>
      </label>
      {upload.isPending && <p className="text-xs text-blue-400 mt-2">Uploading...</p>}
    </div>
  )
}
