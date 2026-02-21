import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Empty } from "@/components/ui/empty";
import { DataCard } from "@/components/features/dashboard/data-card";
import { Database, RefreshCw, Loader2, AlertCircle } from "lucide-react";
import {
  syncEmbeddings,
  getEmbeddingStatus,
  type VectorstoreStatus,
} from "@/api/embeddingsApi";
import { toast } from "sonner";

const SYNCING_STATE_KEY = "vectorstore_syncing_state";

export default function VectorStore() {
  const [status, setStatus] = useState<VectorstoreStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  // Track if user has started a sync - prevents showing empty component during sync
  const [hasSyncStarted, setHasSyncStarted] = useState(false);
  // Use ref to track pending count at sync start to detect completion
  const pendingAtSyncStart = useRef<number>(0);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await getEmbeddingStatus();
      setStatus(data);
      // If backend reports syncing, ensure our state reflects it
      if (data.status === "syncing") {
        setIsSyncing(true);
        setHasSyncStarted(true);
        sessionStorage.setItem(SYNCING_STATE_KEY, "true");
      }
    } catch (error) {
      console.error("Failed to fetch vectorstore status:", error);
      toast.error("Failed to fetch vectorstore status");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Polling effect - only runs when sync has started
  useEffect(() => {
    if (!hasSyncStarted) return;

    const intervalId = setInterval(async () => {
      try {
        const data = await getEmbeddingStatus();
        setStatus(data);

        // Sync is complete when:
        // 1. Backend status is not "syncing" AND
        // 2. Either all documents are embedded OR there's an error
        const isComplete =
          data.status !== "syncing" &&
          (data.pending_documents === 0 || data.status === "error");

        if (isComplete) {
          setIsSyncing(false);
          setHasSyncStarted(false);
          sessionStorage.removeItem(SYNCING_STATE_KEY);

          if (data.status === "error") {
            toast.error("Sync failed", {
              description: "There was an error embedding your documents.",
            });
          } else if (data.pending_documents === 0) {
            toast.success("Sync complete", {
              description: "All documents have been successfully embedded.",
            });
          }
        }
      } catch (error) {
        console.error("Polling error:", error);
      }
    }, 3000);

    return () => clearInterval(intervalId);
  }, [hasSyncStarted]);

  // On mount, check if we were syncing and restore state
  useEffect(() => {
    const wasSyncing = sessionStorage.getItem(SYNCING_STATE_KEY) === "true";
    if (wasSyncing) {
      setIsSyncing(true);
      setHasSyncStarted(true);
    }
    fetchStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSync = async () => {
    if (isSyncing) return;

    // Set both flags immediately - this ensures we show data cards
    setIsSyncing(true);
    setHasSyncStarted(true);
    sessionStorage.setItem(SYNCING_STATE_KEY, "true");
    pendingAtSyncStart.current = status?.pending_documents || 0;

    // Optimistically update status to syncing
    if (status) {
      setStatus({ ...status, status: "syncing" });
    }

    try {
      await syncEmbeddings();
      toast.success("Sync job queued", {
        description: "Processing documents...",
      });
    } catch (error: unknown) {
      console.error("Failed to sync embeddings:", error);
      const errorMessage =
        (error as any)?.response?.data?.message || "An error occurred";
      toast.error("Failed to sync embeddings", {
        description: errorMessage,
      });
      setIsSyncing(false);
      setHasSyncStarted(false);
      sessionStorage.removeItem(SYNCING_STATE_KEY);
      // Revert status on error
      if (status) {
        setStatus({ ...status, status: "error" });
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-200px)]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Empty state: no documents at all
  if (status && status.total_documents === 0) {
    return (
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6 px-4 md:px-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold">Vector Store</h1>
          <p className="text-muted-foreground">
            Manage your document embeddings for AI-powered search
          </p>
        </div>

        <Empty
          icon={Database}
          title="No documents uploaded"
          description="Visit Data Library to upload your first documents."
          action={
            <Button onClick={() => (window.location.href = "/data-library")}>
              Go to Data Library
            </Button>
          }
        />
      </div>
    );
  }

  // Empty state: documents but none embedded AND sync has NOT been started
  // Key change: only show this if hasSyncStarted is false
  if (
    status &&
    status.embedded_documents === 0 &&
    status.pending_documents > 0 &&
    !hasSyncStarted &&
    !isSyncing &&
    status.status !== "syncing"
  ) {
    return (
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6 px-4 md:px-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold">Vector Store</h1>
          <p className="text-muted-foreground">
            Manage your document embeddings for AI-powered search
          </p>
        </div>

        <Empty
          icon={AlertCircle}
          title={`You have ${status.pending_documents} pending document${status.pending_documents !== 1 ? "s" : ""}`}
          description="Click Sync to embed your documents and enable AI-powered search."
          action={
            <Button onClick={handleSync} disabled={isSyncing}>
              {isSyncing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Syncing...
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Sync Documents
                </>
              )}
            </Button>
          }
        />
      </div>
    );
  }

  // Main view with stats
  return (
    <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6 px-4 md:px-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold">Vector Store</h1>
        <p className="text-muted-foreground">
          Manage your document embeddings for AI-powered search
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <DataCard
          title="Total Documents"
          value={status?.total_documents || 0}
          description="Documents in your library"
        />
        <DataCard
          title="Embedded"
          value={status?.embedded_documents || 0}
          description="Ready for AI search"
          status={
            status?.status === "error"
              ? "error"
              : status?.embedded_documents === status?.total_documents &&
                  (status?.total_documents ?? 0) > 0
                ? "success"
                : "idle"
          }
        />
        <DataCard
          title="Pending"
          value={status?.pending_documents || 0}
          description="Awaiting embedding"
          status={
            isSyncing || status?.status === "syncing"
              ? "syncing"
              : status?.status === "error"
                ? "error"
                : (status?.pending_documents || 0) === 0
                  ? "success"
                  : "idle"
          }
          variant={(status?.pending_documents || 0) > 0 ? "warning" : "default"}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sync Documents</CardTitle>
          <CardDescription>
            Embed all pending documents to enable AI-powered search across your
            entire library.
            {status?.pending_documents && status.pending_documents > 0 ? (
              <span className="block mt-2 font-medium text-foreground">
                {status.pending_documents} document
                {status.pending_documents !== 1 ? "s" : ""} ready to be
                embedded.
              </span>
            ) : null}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            onClick={handleSync}
            disabled={isSyncing || (status?.pending_documents || 0) === 0}
            size="lg"
          >
            {isSyncing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Syncing...
              </>
            ) : (status?.pending_documents || 0) > 0 ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Sync Pending Documents
              </>
            ) : (
              "No New Documents to Sync"
            )}
          </Button>

          {status?.status === "syncing" && (
            <p className="text-sm text-muted-foreground mt-4 flex items-center">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Embedding in progress... This may take a few moments.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
