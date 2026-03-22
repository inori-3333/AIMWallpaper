import { describe, it, expect } from 'vitest'
import { useProjectStore } from '../../src/stores/projectStore'

describe('projectStore', () => {
  it('starts with no project selected', () => {
    const state = useProjectStore.getState()
    expect(state.currentProjectId).toBeNull()
  })

  it('sets current project', () => {
    useProjectStore.getState().setCurrentProject('1')
    expect(useProjectStore.getState().currentProjectId).toBe('1')
  })

  it('clears current project', () => {
    useProjectStore.getState().setCurrentProject('1')
    useProjectStore.getState().setCurrentProject(null)
    expect(useProjectStore.getState().currentProjectId).toBeNull()
  })
})
