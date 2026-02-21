import { useState, useCallback } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { DocumentsTab } from "@/components/features/documents/DocumentsTab";
import { GenerateTab } from "@/components/features/generation/GenerateTab";
import { ReviewTab } from "@/components/features/generation/ReviewTab";
import type { Document } from "@/api/docApi";

// Use Radix ScrollArea named exports and alias them so intent is clear
import {
  Root as ScrollAreaRoot,
  Viewport as ScrollAreaViewport,
  Scrollbar as ScrollAreaScrollbar,
  Thumb as ScrollAreaThumb,
  Corner as ScrollAreaCorner,
} from "@radix-ui/react-scroll-area";

// Tab configuration - Embeddings moved to dedicated Vector Store page
const TABS = [
  { id: "documents", label: "Documents" },
  { id: "generate", label: "Generate" },
  { id: "review", label: "Review" },
];

interface ProjectDetailProps {
  projectId: string;
  projectName: string;
  onTabChange?: (tab: string) => void;
}

export default function ProjectDetail({
  projectId,
  projectName: _projectName,
  onTabChange,
}: ProjectDetailProps) {
  const [activeTab, setActiveTab] = useState("documents");
  const [hasDocuments, setHasDocuments] = useState(false);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);

  // Callback to receive documents from DocumentsTab
  const handleDocumentsLoaded = useCallback((docs: Document[]) => {
    setDocuments(docs);
    setHasDocuments(docs.length > 0);
  }, []);

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    onTabChange?.(value);
  };
  const hasSelection = selectedDocIds.length > 0;

  // Get current tab index
  const currentTabIndex = TABS.findIndex((tab) => tab.id === activeTab);
  const hasPrevious = currentTabIndex > 0;
  const hasNext = currentTabIndex < TABS.length - 1;

  // Check if next button should be disabled
  const isNextDisabled =
    activeTab === "documents" && (!hasDocuments || !hasSelection);

  // Navigation handlers
  const goToPreviousTab = () => {
    if (hasPrevious) {
      const previousTab = TABS[currentTabIndex - 1];
      handleTabChange(previousTab.id);
    }
  };

  const goToNextTab = () => {
    if (hasNext && !isNextDisabled) {
      const nextTab = TABS[currentTabIndex + 1];
      handleTabChange(nextTab.id);
    }
  };

  return (
    // root container must be a column flex and a fixed height so ScrollArea can size correctly
    <div className="flex flex-col h-full w-full pt-1 bg-background/80 ">
      <Tabs
        value={activeTab}
        onValueChange={handleTabChange}
        className="flex flex-col h-full "
      >
        {/* Centered Tab List */}
        <div className="flex justify-center ">
          <TabsList className="grid w-full max-w-2xl grid-cols-3 ">
            {TABS.map((tab) => (
              <TabsTrigger key={tab.id} value={tab.id}>
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </div>

        {/*
          IMPORTANT: Wrap the tab panel area with a Radix ScrollArea Root + Viewport.
          Make sure the ScrollArea consumes the remaining space (flex-1) so it fills the
          container height. The Viewport is where the TabsContent will render and will
          be the scrollable region.
        */}
        <div className="flex-1 min-h-0 ">
          {/* min-h-0 allows children to shrink for proper flex scrolling */}
          <ScrollAreaRoot className="h-4/5 w-full rounded-md ">
            <ScrollAreaViewport className="h-full w-full p-6 min-h-0">
              {/* Keep TabsContent children here — only the active tab content will be visible */}

              <TabsContent value="documents" className="m-0 p-0 h-full">
                <div className="h-full">
                  <DocumentsTab
                    projectId={projectId}
                    selectedDocIds={selectedDocIds}
                    onSelectionChange={setSelectedDocIds}
                    onDocumentsChange={setHasDocuments}
                    onDocumentsLoaded={handleDocumentsLoaded}
                  />
                </div>
              </TabsContent>

              <TabsContent value="generate" className="m-0 p-0 h-full">
                <div className="h-full">
                  <GenerateTab
                    projectId={projectId}
                    selectedDocIds={selectedDocIds}
                    documents={documents}
                  />
                </div>
              </TabsContent>

              <TabsContent value="review" className="m-0 p-0 h-full">
                <div className="h-full">
                  <ReviewTab />
                </div>
              </TabsContent>
            </ScrollAreaViewport>

            {/* Vertical scrollbar — style with utility classes or your design tokens.
                You can hide the scrollbar until hover by adding opacity utilities if desired. */}
            <ScrollAreaScrollbar
              orientation="vertical"
              className="w-2 bg-transparent hover:bg-accent/20 transition-colors p-0.5"
            >
              <ScrollAreaThumb className="flex-1 bg-muted-foreground/50 rounded-full" />
            </ScrollAreaScrollbar>

            <ScrollAreaScrollbar
              orientation="horizontal"
              className="h-2 bg-transparent hover:bg-accent/20 transition-colors p-0.5"
            >
              <ScrollAreaThumb className="flex-1 bg-muted-foreground/50 rounded-full" />
            </ScrollAreaScrollbar>

            <ScrollAreaCorner />
          </ScrollAreaRoot>
        </div>
      </Tabs>

      {/* Navigation Buttons - Fixed Position */}
      <div className="fixed bottom-6 right-6 z-50 flex gap-2 ">
        {hasPrevious && (
          <Button
            variant="outline"
            onClick={goToPreviousTab}
            className="gap-2 "
          >
            <ChevronLeft className="h-4 w-4" />
            {TABS[currentTabIndex - 1].label}
          </Button>
        )}

        {hasNext && !isNextDisabled && (
          <Button onClick={goToNextTab} className="gap-2 mr-2">
            {TABS[currentTabIndex + 1].label}
            <ChevronRight className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
