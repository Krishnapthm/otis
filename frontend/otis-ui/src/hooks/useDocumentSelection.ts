import { useState, useCallback } from "react";

interface DocumentSelectionState {
  [projectId: string]: string[];
}

export function useDocumentSelection() {
  const [selections, setSelections] = useState<DocumentSelectionState>({});

  const getSelection = useCallback(
    (projectId: string): string[] => {
      return selections[projectId] || [];
    },
    [selections],
  );

  const setSelection = useCallback((projectId: string, docIds: string[]) => {
    setSelections((prev) => ({
      ...prev,
      [projectId]: docIds,
    }));
  }, []);

  const clearSelection = useCallback((projectId: string) => {
    setSelections((prev) => {
      const newState = { ...prev };
      delete newState[projectId];
      return newState;
    });
  }, []);

  return {
    getSelection,
    setSelection,
    clearSelection,
  };
}
