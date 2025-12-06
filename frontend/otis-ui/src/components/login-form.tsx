import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label"; // Make sure to add this component
import { Link, useNavigate } from "react-router-dom";
import { useState, useEffect, type FormEvent } from "react";
import { login } from "@/api/authApi";
import { useAuth } from "@/authContext";
import Otis2 from "../assets/Otis2.svg";
import Otis3 from "../assets/Otis3.svg";
import Otis5 from "../assets/Otis5.svg";
import Otis4 from "../assets/Otis4.svg";
import Otis1 from "../assets/Otis1.svg";
import Otis6 from "../assets/Otis6.svg";

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

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const { refreshUser } = useAuth();
  const navigate = useNavigate();

  // State
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [currentImage, setCurrentImage] = useState(LOGIN_IMAGES[0]);

  // 2. Random Image Logic
  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * LOGIN_IMAGES.length);
    setCurrentImage(LOGIN_IMAGES[randomIndex]);
  }, []);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");

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
    <div className="w-full lg:grid lg:min-h-[600px] lg:grid-cols-2 xl:min-h-[900px] ">
      <div className=" bg-muted  relative flex items-end">
        <img
          src={currentImage}
          alt="Login visual"
          className="absolute inset-0 h-full w-full object-cover duration-500"
          style={{ objectPosition: "center bottom" }}
        />
      </div>

      {/* RIGHT SIDE: Form Column */}
      <div className="items-center justify-center py-12">
        <div className={cn("mx-auto  w-[400px] ", className)} {...props}>
          <div className="text-center pt-20">
            <h1 className="text-3xl font-bold">Login to your Otis Account</h1>

            <p className="text-balance mt-4 text-muted-foreground ">
              Enter your email below to login to your account
            </p>
          </div>

          <form onSubmit={handleSubmit} className="grid gap-4 mt-16">
            {error && (
              <div className="text-red-500 text-sm font-medium text-center">
                {error}
              </div>
            )}

            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="m@example.com"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
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
              <Input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-foreground hover:bg-accent-foreground text-accent cursor-pointer"
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
