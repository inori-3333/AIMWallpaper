import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from './client'
import type { ProjectCreate } from '../types'

export function useProjects() {
  return useQuery({ queryKey: ['projects'], queryFn: api.listProjects })
}

export function useProject(id: string) {
  return useQuery({ queryKey: ['project', id], queryFn: () => api.getProject(id), enabled: !!id })
}

export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ProjectCreate) => api.createProject(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })
}

export function useAssets() {
  return useQuery({ queryKey: ['assets'], queryFn: api.listAssets })
}

export function useUploadAsset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => api.uploadAsset(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['assets'] }),
  })
}

export function useDeleteAsset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.deleteAsset(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['assets'] }),
  })
}

export function usePatterns(query?: string) {
  return useQuery({ queryKey: ['patterns', query], queryFn: () => api.listPatterns(query) })
}

export function useExamples() {
  return useQuery({ queryKey: ['examples'], queryFn: api.listExamples })
}

export function usePreviewProject() {
  return useMutation({ mutationFn: (id: string) => api.previewProject(id) })
}
