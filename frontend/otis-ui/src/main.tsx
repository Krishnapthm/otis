import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { LoginForm } from "./components/features/auth/login-form.tsx";
import { SignupForm } from "./components/features/auth/signup-form.tsx";
import { RequireAuth } from "./components/features/auth/requireAuth.tsx";
import { ThemeProvider } from "next-themes";
import App from "./App.tsx";
import { AuthProvider } from "@/authContext.tsx";

const queryClient = new QueryClient();
import Dashboard from "./components/features/dashboard/dashboard.tsx";
import ChatPage from "./components/features/chat/chat-page.tsx";
import Projects from "./components/features/projects/projects.tsx";
import ProjectDetailPage from "./components/features/projects/ProjectDetailPage.tsx";
import DataLibrary from "@/pages/data-library.tsx";
import VectorStore from "@/pages/vector-store.tsx";
import Reports from "@/pages/reports.tsx";
import WordAssistant from "@/pages/word-assistant.tsx";
import Settings from "@/pages/settings.tsx";
import Help from "@/pages/help.tsx";
import Search from "@/pages/search.tsx";
import MCQs from "@/pages/mcqs.tsx";
import ChatsPage from "@/pages/chats.tsx";

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <RequireAuth>
        <App />
      </RequireAuth>
    ),
    children: [
      {
        index: true,
        element: <ChatPage />,
      },
      {
        path: "c/:chatId",
        element: <ChatPage />,
      },
      {
        path: "dashboard",
        element: <Dashboard />,
      },
      {
        path: "chats",
        element: <ChatsPage />,
      },
      {
        path: "projects",
        element: <Projects />,
      },
      {
        path: "p/:projectId",
        element: <ProjectDetailPage />,
      },
      // {
      //   path: "analytics",
      //   element: <Analytics />,
      // },
      // {
      //   path: "team",
      //   element: <Team />,
      // },
      // {
      //   path: "capture",
      //   element: <Capture />,
      // },
      // {
      //   path: "proposal",
      //   element: <Proposal />,
      // },
      // {
      //   path: "prompts",
      //   element: <Prompts />,
      // },
      {
        path: "data-library",
        element: <DataLibrary />,
      },
      {
        path: "vector-store",
        element: <VectorStore />,
      },
      {
        path: "reports",
        element: <Reports />,
      },
      {
        path: "word-assistant",
        element: <WordAssistant />,
      },
      {
        path: "mcqs",
        element: <MCQs />,
      },
      {
        path: "settings",
        element: <Settings />,
      },
      {
        path: "help",
        element: <Help />,
      },
      {
        path: "search",
        element: <Search />,
      },
    ],
  },
  {
    path: "/login",
    element: <LoginForm />,
  },
  {
    path: "/signup",
    element: <SignupForm />,
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider
      attribute="class"
      defaultTheme="light"
      enableSystem
      disableTransitionOnChange
    >
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <div className="h-screen w-screen overflow-hidden">
            <RouterProvider router={router} />
          </div>
          <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>,
);
