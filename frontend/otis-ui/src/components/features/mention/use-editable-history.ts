import { useCallback, useRef, useState } from "react";

export interface EditableHistorySnapshot {
  value: string;
  selection: { start: number; end: number };
}

interface EditableHistoryOptions {
  maxEntries?: number;
  coalesceMs?: number;
}

function snapshotsEqual(
  a: EditableHistorySnapshot,
  b: EditableHistorySnapshot,
) {
  return (
    a.value === b.value &&
    a.selection.start === b.selection.start &&
    a.selection.end === b.selection.end
  );
}

export function useEditableHistory(options: EditableHistoryOptions = {}) {
  const { maxEntries = 200, coalesceMs = 400 } = options;

  const [undoDepth, setUndoDepth] = useState(0);
  const [redoDepth, setRedoDepth] = useState(0);

  const undoStackRef = useRef<EditableHistorySnapshot[]>([]);
  const redoStackRef = useRef<EditableHistorySnapshot[]>([]);
  const latestRef = useRef<EditableHistorySnapshot | null>(null);
  const lastPushAtRef = useRef<number>(0);

  const syncDepth = useCallback(() => {
    setUndoDepth(undoStackRef.current.length);
    setRedoDepth(redoStackRef.current.length);
  }, []);

  const initialize = useCallback(
    (snapshot: EditableHistorySnapshot) => {
      latestRef.current = snapshot;
      undoStackRef.current = [];
      redoStackRef.current = [];
      lastPushAtRef.current = 0;
      syncDepth();
    },
    [syncDepth],
  );

  const capture = useCallback(
    (snapshot: EditableHistorySnapshot, forceBoundary = false) => {
      const latest = latestRef.current;

      if (!latest) {
        initialize(snapshot);
        return;
      }

      if (snapshotsEqual(latest, snapshot)) {
        return;
      }

      const now = Date.now();
      const shouldCreateBoundary =
        forceBoundary ||
        now - lastPushAtRef.current > coalesceMs ||
        latest.selection.start !== latest.selection.end ||
        snapshot.selection.start !== snapshot.selection.end;

      if (shouldCreateBoundary) {
        undoStackRef.current.push(latest);
        if (undoStackRef.current.length > maxEntries) {
          undoStackRef.current.splice(
            0,
            undoStackRef.current.length - maxEntries,
          );
        }
        lastPushAtRef.current = now;
      }

      latestRef.current = snapshot;
      redoStackRef.current = [];
      syncDepth();
    },
    [coalesceMs, initialize, maxEntries, syncDepth],
  );

  const canUndo = undoDepth > 0;
  const canRedo = redoDepth > 0;

  const undo = useCallback((): EditableHistorySnapshot | null => {
    const latest = latestRef.current;
    const prev = undoStackRef.current.pop();

    if (!latest || !prev) {
      syncDepth();
      return null;
    }

    redoStackRef.current.push(latest);
    latestRef.current = prev;
    syncDepth();
    return prev;
  }, [syncDepth]);

  const redo = useCallback((): EditableHistorySnapshot | null => {
    const latest = latestRef.current;
    const next = redoStackRef.current.pop();

    if (!latest || !next) {
      syncDepth();
      return null;
    }

    undoStackRef.current.push(latest);
    latestRef.current = next;
    syncDepth();
    return next;
  }, [syncDepth]);

  const clear = useCallback(() => {
    undoStackRef.current = [];
    redoStackRef.current = [];
    latestRef.current = null;
    lastPushAtRef.current = 0;
    syncDepth();
  }, [syncDepth]);

  return {
    initialize,
    capture,
    undo,
    redo,
    clear,
    canUndo,
    canRedo,
  };
}
