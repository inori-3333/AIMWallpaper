import { useCallback, useState } from 'react'
import { useUploadAsset } from '../../api/hooks'

const ALLOWED_EXTENSIONS = new Set([
  '.png', '.jpg', '.jpeg', '.bmp', '.tga',
  '.mp4', '.webm',
  '.ogg', '.mp3', '.wav',
  '.pkg', '.json',
])

const MAX_SIZE_MB = 500

function getExtension(filename: string): string {
  const dot = filename.lastIndexOf('.')
  return dot >= 0 ? filename.slice(dot).toLowerCase() : ''
}

function validateFile(file: File): string | null {
  const ext = getExtension(file.name)
  if (!ALLOWED_EXTENSIONS.has(ext)) {
    return `"${file.name}": unsupported file type (${ext || 'no extension'}). Allowed: ${[...ALLOWED_EXTENSIONS].join(', ')}`
  }
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    return `"${file.name}": file too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Max: ${MAX_SIZE_MB}MB`
  }
  return null
}

export function AssetUpload() {
  const upload = useUploadAsset()
  const [errors, setErrors] = useState<string[]>([])

  const processFiles = useCallback((files: File[]) => {
    const newErrors: string[] = []
    const valid: File[] = []

    for (const file of files) {
      const err = validateFile(file)
      if (err) {
        newErrors.push(err)
      } else {
        valid.push(file)
      }
    }

    setErrors(newErrors)
    valid.forEach((file) => upload.mutate(file))

    if (newErrors.length > 0) {
      setTimeout(() => setErrors([]), 5000)
    }
  }, [upload])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    processFiles(Array.from(e.dataTransfer.files))
  }, [processFiles])

  const handleDragOver = (e: React.DragEvent) => e.preventDefault()

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    processFiles(Array.from(e.target.files || []))
    e.target.value = ''
  }

  return (
    <div>
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
          accept=".png,.jpg,.jpeg,.bmp,.tga,.mp4,.webm,.ogg,.mp3,.wav,.pkg,.json"
        />
        <label htmlFor="asset-upload" className="cursor-pointer">
          <p className="text-sm text-gray-400">Drop files here or click to upload</p>
          <p className="text-xs text-gray-500 mt-1">
            Images (.png .jpg .bmp .tga), Videos (.mp4 .webm), Audio (.ogg .mp3 .wav), .pkg, .json
          </p>
        </label>
        {upload.isPending && <p className="text-xs text-blue-400 mt-2">Uploading...</p>}
      </div>
      {errors.length > 0 && (
        <div className="mt-2 space-y-1">
          {errors.map((err, i) => (
            <p key={i} className="text-xs text-red-400">{err}</p>
          ))}
        </div>
      )}
    </div>
  )
}
