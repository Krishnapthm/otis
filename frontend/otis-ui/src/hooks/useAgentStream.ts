import { useState, useCallback, useRef } from "react";
import {
  startGraphStream,
  resumeGraphStream,
  type Concept,
  type Overview,
  type AgentEvent,
} from "@/api/agentApi";

// ============================================================================
// Types
// ============================================================================

export type AgentPhase =
  | "idle"
  | "extracting"
  | "selecting"
  | "processing"
  | "complete"
  | "error";

export interface AgentStreamState {
  phase: AgentPhase;
  status: string;
  overviews: Overview[];
  threadId: string | null;
  error: string | null;
  retrievedDocsCount: number | null;
}

export interface UseAgentStreamReturn extends AgentStreamState {
  startStream: (docIds: string[]) => Promise<void>;
  resumeWithConcepts: (selectedConcepts: Concept[]) => Promise<void>;
  reset: () => void;
}

// ============================================================================
// Hook
// ============================================================================

const initialState: AgentStreamState = {
  phase: "idle",
  status: "",
  overviews: [],
  threadId: null,
  error: null,
  retrievedDocsCount: null,
};

export function useAgentStream(): UseAgentStreamReturn {
  const [state, setState] = useState<AgentStreamState>(initialState);
  const closeRef = useRef<(() => void) | null>(null);

  const handleEvent = useCallback((event: AgentEvent) => {
    const { payload } = event;

    // Update status if present
    if (payload.status) {
      setState((prev) => ({ ...prev, status: payload.status! }));
    }

    // Check for overview/concepts extracted (interrupt point)
    if (payload.overview) {
      setState((prev) => ({
        ...prev,
        overviews: payload.overview!,
        phase: "selecting",
        status: "Concepts extracted - please select concepts to continue",
      }));
    }

    // Alternative: overview_for_user from interrupt
    if (payload.overview_for_user) {
      setState((prev) => ({
        ...prev,
        overviews: payload.overview_for_user!,
        phase: "selecting",
        status: "Concepts extracted - please select concepts to continue",
      }));
    }

    // Check for retrieval complete
    if (payload.docs !== undefined) {
      setState((prev) => ({
        ...prev,
        retrievedDocsCount: payload.docs!,
      }));
    }
  }, []);

  const handleError = useCallback((error: string) => {
    setState((prev) => ({
      ...prev,
      phase: "error",
      error,
      status: `Error: ${error}`,
    }));
  }, []);

  const handleComplete = useCallback(() => {
    setState((prev) => {
      // Only mark complete if we're past the selecting phase
      if (prev.phase === "processing") {
        return { ...prev, phase: "complete", status: "Generation complete" };
      }
      return prev;
    });
  }, []);

  const startStream = useCallback(
    async (docIds: string[]) => {
      // Clean up any existing stream
      if (closeRef.current) {
        closeRef.current();
        closeRef.current = null;
      }

      setState({
        ...initialState,
        phase: "extracting",
        status: "Starting concept extraction...",
      });

      try {
        const { close, threadIdPromise } = await startGraphStream(
          docIds,
          handleEvent,
          handleError,
          handleComplete,
        );

        closeRef.current = close;

        const threadId = await threadIdPromise;
        setState((prev) => ({ ...prev, threadId }));
      } catch (error) {
        handleError(
          error instanceof Error ? error.message : "Failed to start stream",
        );
      }
    },
    [handleEvent, handleError, handleComplete],
  );

  const resumeWithConcepts = useCallback(
    async (selectedConcepts: Concept[]) => {
      if (!state.threadId) {
        handleError("No thread ID available for resume");
        return;
      }

      // Clean up existing stream
      if (closeRef.current) {
        closeRef.current();
        closeRef.current = null;
      }

      setState((prev) => ({
        ...prev,
        phase: "processing",
        status: "Processing selected concepts...",
      }));

      try {
        const { close } = await resumeGraphStream(
          state.threadId,
          selectedConcepts,
          handleEvent,
          handleError,
          handleComplete,
        );

        closeRef.current = close;
      } catch (error) {
        handleError(
          error instanceof Error ? error.message : "Failed to resume stream",
        );
      }
    },
    [state.threadId, handleEvent, handleError, handleComplete],
  );

  const reset = useCallback(() => {
    if (closeRef.current) {
      closeRef.current();
      closeRef.current = null;
    }
    setState(initialState);
  }, []);

  return {
    ...state,
    startStream,
    resumeWithConcepts,
    reset,
  };
}
