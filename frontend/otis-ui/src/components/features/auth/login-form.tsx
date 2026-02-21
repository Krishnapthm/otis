import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { Label } from "@/components/ui/label";
import { Link, useNavigate } from "react-router-dom";
import { useState, useEffect, type FormEvent } from "react";
import { login } from "@/api/authApi";
import { useAuth } from "@/authContext";
import Otis2 from "@/assets/Otis2.svg";
import Otis3 from "@/assets/Otis3.svg";
import Otis5 from "@/assets/Otis5.svg";
import Otis4 from "@/assets/Otis4.svg";
import Otis1 from "@/assets/Otis1.svg";
import Otis6 from "@/assets/Otis6.svg";

// 1. Define your images array here
const LOGIN_IMAGES = [
  Otis2,
  Otis1,
  Otis3,
  Otis4,
  Otis5,
  Otis6,

  // "https://images.unsplash.com/photo-1590069261209-f8e9b8642343?q=80&w=1000&auto=format&fit=crop"
];

// Validation helpers
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FieldErrors {
  email?: string;
  password?: string;
}

export function LoginForm() {
  const { refreshUser } = useAuth();
  const navigate = useNavigate();

  // State
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [currentImage, setCurrentImage] = useState(LOGIN_IMAGES[0]);

  // 2. Random Image Logic
  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * LOGIN_IMAGES.length);
    setCurrentImage(LOGIN_IMAGES[randomIndex]);
  }, []);

  // Validate individual fields
  function validateEmail(value: string): string | undefined {
    if (!value.trim()) {
      return "Email is required";
    }
    if (!EMAIL_REGEX.test(value)) {
      return "Please enter a valid email address";
    }
    return undefined;
  }

  function validatePassword(value: string): string | undefined {
    if (!value) {
      return "Password is required";
    }
    // Note: We don't enforce password complexity on login
    // The backend will validate the actual credentials
    return undefined;
  }

  // Validate all fields
  function validateForm(): boolean {
    const errors: FieldErrors = {};

    const emailError = validateEmail(email);
    if (emailError) errors.email = emailError;

    const passwordError = validatePassword(password);
    if (passwordError) errors.password = passwordError;

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  // Handle field changes with error clearing
  function handleEmailChange(value: string) {
    setEmail(value);
    if (fieldErrors.email) {
      setFieldErrors((prev) => ({ ...prev, email: undefined }));
    }
    if (error) setError("");
  }

  function handlePasswordChange(value: string) {
    setPassword(value);
    if (fieldErrors.password) {
      setFieldErrors((prev) => ({ ...prev, password: undefined }));
    }
    if (error) setError("");
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");

    if (!validateForm()) {
      return;
    }

    try {
      await login(email, password);
      await refreshUser();
      navigate("/");
    } catch (err) {
      console.error(err);
      setError("Invalid email or password");
    }
  }

  return (
    <div className="w-full h-screen lg:grid lg:grid-cols-2">
      {/* LEFT SIDE: Image */}
      <div className="hidden lg:block bg-muted relative overflow-hidden h-screen">
        <img
          src={currentImage}
          alt="Login visual"
          className="absolute bottom-0 right-0 h-full w-full object-cover object-bottom-right"
        />
      </div>

      {/* RIGHT SIDE: Form Column */}
      <div className="flex items-center justify-center h-screen py-12">
        <div className="mx-auto w-[400px] px-4">
          <div className="text-center">
            <h1 className="text-3xl font-bold">Login to your Otis Account</h1>

            <p className="text-balance mt-4 text-muted-foreground ">
              Enter your email below to login to your account
            </p>
          </div>

          <form onSubmit={handleSubmit} className="grid gap-4 mt-8">
            {error && (
              <div className="text-destructive text-sm font-medium text-center p-2 bg-destructive/10 rounded-md border border-destructive/20">
                {error}
              </div>
            )}

            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="m@example.com"
                value={email}
                onChange={(e) => handleEmailChange(e.target.value)}
                aria-invalid={!!fieldErrors.email}
                aria-describedby={fieldErrors.email ? "email-error" : undefined}
              />
              {fieldErrors.email && (
                <p id="email-error" className="text-destructive text-sm">
                  {fieldErrors.email}
                </p>
              )}
            </div>

            <div className="grid gap-2">
              <div className="flex items-center">
                <Label htmlFor="password">Password</Label>
                <a
                  href="#" // Replace with actual forgot password route
                  className="ml-auto inline-block text-sm underline"
                >
                  Forgot your password?
                </a>
              </div>
              <PasswordInput
                className="squircle"
                id="password"
                value={password}
                onChange={(e) => handlePasswordChange(e.target.value)}
                aria-invalid={!!fieldErrors.password}
                aria-describedby={
                  fieldErrors.password ? "password-error" : undefined
                }
              />
              {fieldErrors.password && (
                <p id="password-error" className="text-destructive text-sm">
                  {fieldErrors.password}
                </p>
              )}
            </div>

            <Button
              type="submit"
              className="squircle   w-full bg-foreground hover:bg-accent-foreground text-accent cursor-pointer"
            >
              Login
            </Button>

            <Button
              variant="outline"
              type="button"
              className="w-full cursor-pointer"
            >
              Login with Google
            </Button>
          </form>

          <div className="mt-4 text-center text-sm">
            Don&apos;t have an account?{" "}
            <Link to="/Signup" className="underline">
              Sign up
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
