"use client";

import { useEffect, useMemo, useState } from "react";
import { IconTrendingDown, IconTrendingUp } from "@tabler/icons-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type ReadMCQ = {
  mcq_id: string;
  generated_at: string;
  mcq: any;
};

import mcqApi from "@/api/mcqApi";

export function SectionCards() {
  const [mcqs, setMcqs] = useState<ReadMCQ[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    mcqApi
      .getAll()
      .then((data: ReadMCQ[]) => {
        if (!mounted) return;
        const list = Array.isArray(data) ? data : [];
        // sort descending by generated_at so latest is first
        list.sort(
          (a, b) => +new Date(b.generated_at) - +new Date(a.generated_at),
        );
        setMcqs(list);
      })
      .catch((err) => {
        console.error("mcq fetch error", err);
        if (!mounted) return;
        setError(String(err));
      })
      .finally(() => mounted && setLoading(false));

    return () => {
      mounted = false;
    };
  }, []);

  const total = mcqs.length;

  const todayCount = useMemo(() => {
    const today = new Date();
    return mcqs.filter((m) => {
      try {
        const d = new Date(m.generated_at);
        return (
          d.getFullYear() === today.getFullYear() &&
          d.getMonth() === today.getMonth() &&
          d.getDate() === today.getDate()
        );
      } catch {
        return false;
      }
    }).length;
  }, [mcqs]);

  const avgQuestions = useMemo(() => {
    if (mcqs.length === 0) return 0;
    const counts = mcqs.map((m) => {
      const payload = m.mcq;
      if (!payload) return 0;
      // backend MCQ shape: { questions: [...] }
      if (Array.isArray(payload.questions)) return payload.questions.length;
      // sometimes payload may be wrapped: { mcq: { questions: [...] } }
      if (payload.mcq && Array.isArray(payload.mcq.questions))
        return payload.mcq.questions.length;
      // fallback if payload itself is an array
      if (Array.isArray(payload)) return payload.length;
      return 0;
    });
    const totalQ = counts.reduce((a, b) => a + b, 0);
    return Math.round((totalQ / mcqs.length) * 10) / 10;
  }, [mcqs]);

  const latest = mcqs[0];

  return (
    <div className="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
      {error && (
        <Card className="@container/card col-span-ful">
          <CardHeader>
            <CardDescription>Error fetching MCQs</CardDescription>
            <CardTitle className="text-sm font-medium text-destructive">
              {error}
            </CardTitle>
          </CardHeader>
        </Card>
      )}
      <Card className="@container/card squircle">
        <CardHeader>
          <CardDescription>Total MCQs</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {loading ? "..." : total}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">
              <IconTrendingUp />
              {total > 0
                ? `+${Math.round((total / Math.max(1, total)) * 100)}%`
                : "0%"}
            </Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            Total MCQs generated
          </div>
          <div className="text-muted-foreground">Endpoint: /mcqs</div>
        </CardFooter>
      </Card>

      <Card className="@container/card">
        <CardHeader>
          <CardDescription>MCQs Today</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {loading ? "..." : todayCount}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">
              <IconTrendingDown />
              {todayCount >= 0 ? `${todayCount}` : "0"}
            </Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            Generated today
          </div>
          <div className="text-muted-foreground">
            Keep an eye on generation volume
          </div>
        </CardFooter>
      </Card>

      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Avg Questions / MCQ</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {loading ? "..." : avgQuestions}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">
              <IconTrendingUp />
              {avgQuestions >= 0 ? `${avgQuestions}` : "-"}
            </Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            Average number of questions per MCQ
          </div>
          <div className="text-muted-foreground">
            Useful when endpoint adds more data
          </div>
        </CardFooter>
      </Card>

      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Latest MCQ</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {loading ? "..." : latest ? latest.mcq_id.slice(0, 8) : "—"}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">Recent</Badge>
          </CardAction>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            {latest
              ? new Intl.DateTimeFormat(undefined, {
                  dateStyle: "medium",
                  timeStyle: "short",
                }).format(new Date(latest.generated_at))
              : "No data"}
          </div>
          <div className="text-muted-foreground">
            Click Projects to inspect individual MCQs
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
