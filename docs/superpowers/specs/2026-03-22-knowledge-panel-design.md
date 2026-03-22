# Knowledge Panel Design

## Overview

Add a "Knowledge Base" tab to the TopNav that replaces the center Preview area with a knowledge management panel. The left AssetPanel and right ChatPanel remain visible.

## Layout

TopNav gains two tab buttons: "壁纸编辑" (active by default) and "知识库". Clicking "知识库" swaps the center panel from PreviewPanel to KnowledgePanel.

## KnowledgePanel Structure

Two sections stacked vertically:

### Import Section (top)
- Text input for file/directory path
- Two action buttons: "导入单个" (POST /api/examples/import) and "批量扫描" (POST /api/examples/scan)
- Status feedback (success count, errors)
- Imported examples list table: title, type, tags, object_count, summary

### Pattern Management Section (bottom)
- Search input (queries GET /api/knowledge/patterns?query=...)
- Pattern card grid, each card shows:
  - Name, category, tags
  - Confidence bar (green >0.8, yellow 0.5-0.8, red <0.5)
  - Verified badge
  - Action buttons: Verify (PUT /api/knowledge/patterns/{id}/verify), Delete (DELETE /api/knowledge/patterns/{id})

## State Management

- `activeTab` state: managed via prop drilling from App.tsx (simple string: "editor" | "knowledge")
- No new Zustand store needed — App-level useState suffices

## New API Hooks (hooks.ts)

- `useExamples()` — already exists
- `useImportExample()` — POST /api/examples/import, invalidates examples query
- `useScanWorkshop()` — POST /api/examples/scan, invalidates examples query
- `useVerifyPattern(id)` — PUT /api/knowledge/patterns/{id}/verify, invalidates patterns query
- `useDeletePattern(id)` — DELETE /api/knowledge/patterns/{id}, invalidates patterns query

## New API Client Functions (client.ts)

- `importExample(path: string)`
- `scanWorkshop(path: string)`
- `verifyPattern(id: number)`
- `deletePattern(id: number)`

## New Files

- `frontend/src/components/KnowledgePanel/KnowledgePanel.tsx`

## Modified Files

- `frontend/src/App.tsx` — add activeTab state, conditional center panel
- `frontend/src/components/TopNav/TopNav.tsx` — add tab buttons, receive activeTab/onTabChange props
- `frontend/src/api/client.ts` — add 4 new endpoint functions
- `frontend/src/api/hooks.ts` — add 4 new mutation hooks

## Styling

Follows existing dark theme: bg-gray-800/900, text-gray-300, blue accent buttons. Tailwind utility classes only.
