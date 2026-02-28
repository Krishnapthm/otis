import { useEffect, useState } from "react";
import { Empty } from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import mcqApi, { type ReadMCQ } from "@/api/mcqApi";
import { MCQExportButton } from "@/components/features/mcq/mcq-export-button";

export default function MCQs() {
  const [tests, setTests] = useState<ReadMCQ[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchTests = async () => {
      try {
        const data = await mcqApi.getAll();
        if (!isMounted) return;
        setTests(data);
      } catch (error) {
        console.error("Failed to fetch MCQ tests", error);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchTests();
    return () => {
      isMounted = false;
    };
  }, []);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3 py-4 md:gap-6 md:py-6 px-4 md:px-6">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  if (tests.length === 0) {
    return (
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6 px-4 md:px-6">
        <Empty
          title="No MCQ tests yet"
          description="Generated MCQ tests will appear here once available."
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6 px-4 md:px-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold">MCQ Tests</h1>
        <p className="text-muted-foreground text-sm">
          Read-only list of generated tests.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {tests.map((test) => {
          const createdAt = test.mcq.created_at
            ? new Date(test.mcq.created_at).toLocaleString()
            : "Unknown date";

          return (
            <Card key={test.mcq_id}>
              <CardHeader className="flex flex-row items-start justify-between gap-3">
                <div>
                  <CardTitle>
                    {test.mcq.test_name || "Untitled MCQ Test"}
                  </CardTitle>
                  <CardDescription>Test ID: {test.mcq.test_id}</CardDescription>
                </div>
                <MCQExportButton mcqId={test.mcq_id} />
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground space-y-1">
                <p>Saved: {createdAt}</p>
                <p>Questions: {test.mcq.questions?.length ?? 0}</p>
                <p>Documents: {test.mcq.doc_ids?.length ?? 0}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
