import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Loader2,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
} from "lucide-react";
import { DocumentPreview } from "@/components/features/documents/DocumentPreview";
import { ConceptSelector } from "@/components/features/generation/ConceptSelector";
import { useAgentStream } from "@/hooks/useAgentStream";
import type { Document } from "@/api/docApi";
import type { Concept } from "@/api/agentApi";

interface GenerateTabProps {
  projectId: string;
  selectedDocIds: string[];
  documents: Document[];
}

export function GenerateTab({
  projectId: _projectId,
  selectedDocIds,
  documents,
}: GenerateTabProps) {
  // Filter to only selected documents
  const selectedDocuments = useMemo(
    () => documents.filter((doc) => selectedDocIds.includes(doc.doc_id)),
    [documents, selectedDocIds],
  );

  // Agent stream hook
  const {
    phase,
    status,
    overviews,
    error,
    startStream,
    resumeWithConcepts,
    reset,
  } = useAgentStream();

  // Local state for concept selection
  const [selectedConcepts, setSelectedConcepts] = useState<Concept[]>([]);

  // Handlers
  const handleStartExtraction = async () => {
    if (selectedDocIds.length === 0) return;
    setSelectedConcepts([]);
    await startStream(
      selectedDocIds,
      "Generate multiple-choice questions from the selected documents.",
    );
  };

  const handleContinue = async () => {
    if (selectedConcepts.length === 0) return;
    await resumeWithConcepts(selectedConcepts);
  };

  const handleReset = () => {
    setSelectedConcepts([]);
    reset();
  };

  // Render phase-specific content
  const renderPhaseContent = () => {
    switch (phase) {
      case "idle":
        return (
          <div className="space-y-6">
            {/* Document Preview */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Selected Documents</CardTitle>
              </CardHeader>
              <CardContent>
                <DocumentPreview documents={selectedDocuments} />
              </CardContent>
            </Card>

            {/* Start Button */}
            <div className="flex justify-center">
              <Button
                size="lg"
                onClick={handleStartExtraction}
                disabled={selectedDocIds.length === 0}
                className="gap-2"
              >
                <Sparkles className="h-5 w-5" />
                Extract Concepts
              </Button>
            </div>

            {selectedDocIds.length === 0 && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Please select documents in the Documents tab to begin concept
                  extraction.
                </AlertDescription>
              </Alert>
            )}
          </div>
        );

      case "extracting":
        return (
          <div className="space-y-6">
            {/* Document Preview */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Selected Documents</CardTitle>
              </CardHeader>
              <CardContent>
                <DocumentPreview documents={selectedDocuments} />
              </CardContent>
            </Card>

            <Separator />

            {/* Status Display */}
            <Card className="border-primary/20">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  <div>
                    <p className="font-medium">Processing...</p>
                    <p className="text-sm text-muted-foreground">{status}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        );

      case "selecting":
        return (
          <div className="space-y-6">
            {/* Document Preview - Collapsed */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Selected Documents</CardTitle>
              </CardHeader>
              <CardContent>
                <DocumentPreview documents={selectedDocuments} />
              </CardContent>
            </Card>

            <Separator />

            {/* Concept Selection */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  Concepts Extracted
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Select the concepts you want to generate MCQs for. Click on a
                  concept to toggle selection.
                </p>
                <ConceptSelector
                  overviews={overviews}
                  selectedConcepts={selectedConcepts}
                  onSelectionChange={setSelectedConcepts}
                />
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex justify-between items-center">
              <Button variant="outline" onClick={handleReset}>
                Start Over
              </Button>
              <Button
                onClick={handleContinue}
                disabled={selectedConcepts.length === 0}
                className="gap-2"
              >
                Continue with {selectedConcepts.length} concept
                {selectedConcepts.length !== 1 ? "s" : ""}
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        );

      case "processing":
        return (
          <div className="space-y-6">
            {/* Compact doc preview */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Processing</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  <div>
                    <p className="font-medium">Generating content...</p>
                    <p className="text-sm text-muted-foreground">{status}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Selected concepts display */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Selected Concepts ({selectedConcepts.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {selectedConcepts.map((concept, idx) => (
                    <Button key={idx} variant="secondary" size="sm" disabled>
                      {concept.name}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        );

      case "complete":
        return (
          <div className="space-y-6">
            <Card className="border-green-500/30 bg-green-500/5">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-6 w-6 text-green-500" />
                  <div>
                    <p className="font-medium text-green-700 dark:text-green-400">
                      Generation Complete!
                    </p>
                    <p className="text-sm text-muted-foreground">{status}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-center">
              <Button onClick={handleReset}>Generate More</Button>
            </div>
          </div>
        );

      case "error":
        return (
          <div className="space-y-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {error || "An error occurred"}
              </AlertDescription>
            </Alert>

            <div className="flex justify-center">
              <Button onClick={handleReset} variant="outline">
                Try Again
              </Button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-semibold">Generate MCQs</h2>
        <p className="text-sm text-muted-foreground">
          Extract concepts from documents and generate multiple choice questions
        </p>
      </div>

      {/* Phase Content */}
      <div className="flex-1">{renderPhaseContent()}</div>
    </div>
  );
}
