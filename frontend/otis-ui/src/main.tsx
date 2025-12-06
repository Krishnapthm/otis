import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { LoginForm } from "./components/login-form.tsx";
import { SignupForm } from "./components/signup-form.tsx";
import { RequireAuth } from "./components/requireAuth.tsx";
import { ThemeProvider } from "next-themes";
import App from "./App.tsx";
import { AuthProvider } from "./authContext.tsx";
import Dashboard from "./components/dashboard.tsx";
import Projects from "./components/projects.tsx";
import ProjectDetailPage from "./components/ProjectDetailPage.tsx";

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
        element: (
          <>
            <Dashboard />,
          </>
        ),
      },
      {
        path: "/Projects",
        element: <Projects />,
      },
      {
        path: "p/:projectId",
        element: <ProjectDetailPage />,
      },
    ],
  },
  {
    path: "/Login",
    element: <LoginForm className="max-w-sm mx-auto justify-center h-screen" />,
  },
  {
    path: "/Signup",
    element: (
      <SignupForm className="max-w-sm mx-auto justify-center h-screen" />
    ),
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem
      disableTransitionOnChange
    >
      <AuthProvider>
        <div className="h-screen w-screen overflow-hidden">
          <RouterProvider router={router} />
        </div>
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>
);
