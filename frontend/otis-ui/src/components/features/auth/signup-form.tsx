import { signup } from "@/api/authApi";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import {
  ValidationChecklist,
  type ValidationRule,
} from "@/components/ui/validation-checklist";
import { useState, useMemo, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

// Validation constants
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 8;
const MIN_NAME_LENGTH = 2;

interface FieldErrors {
  uname?: string;
  email?: string;
  password?: string;
  confirmPass?: string;
}

export function SignupForm() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [uname, setUname] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPass, setConfirmPass] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  // Real-time password validation rules for the checklist
  const passwordValidationRules: ValidationRule[] = useMemo(
    () => [
      {
        id: "length",
        label: `At least ${MIN_PASSWORD_LENGTH} characters`,
        isValid: password.length >= MIN_PASSWORD_LENGTH,
      },
      {
        id: "uppercase",
        label: "At least one uppercase letter",
        isValid: /[A-Z]/.test(password),
      },
      {
        id: "lowercase",
        label: "At least one lowercase letter",
        isValid: /[a-z]/.test(password),
      },
      {
        id: "number",
        label: "At least one number",
        isValid: /[0-9]/.test(password),
      },
      {
        id: "special",
        label: "At least one special character",
        isValid: /[!"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~]/.test(password),
      },
      {
        id: "match",
        label: "Passwords match",
        isValid:
          password.length > 0 &&
          confirmPass.length > 0 &&
          password === confirmPass,
      },
    ],
    [password, confirmPass],
  );

  // Validation functions
  function validateName(value: string): string | undefined {
    if (!value.trim()) {
      return "Name is required";
    }
    if (value.trim().length < MIN_NAME_LENGTH) {
      return `Name must be at least ${MIN_NAME_LENGTH} characters`;
    }
    return undefined;
  }

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
    if (value.length < MIN_PASSWORD_LENGTH) {
      return `Password must be at least ${MIN_PASSWORD_LENGTH} characters`;
    }
    // Check for uppercase
    if (!/[A-Z]/.test(value)) {
      return "Password must contain at least one uppercase letter";
    }
    // Check for lowercase
    if (!/[a-z]/.test(value)) {
      return "Password must contain at least one lowercase letter";
    }
    // Check for number
    if (!/[0-9]/.test(value)) {
      return "Password must contain at least one number";
    }
    // Check for special character
    if (!/[!"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~]/.test(value)) {
      return "Password must contain at least one special character";
    }
    return undefined;
  }

  function validateConfirmPassword(
    value: string,
    passwordValue: string,
  ): string | undefined {
    if (!value) {
      return "Please confirm your password";
    }
    if (value !== passwordValue) {
      return "Passwords do not match";
    }
    return undefined;
  }

  // Validate all fields
  function validateForm(): boolean {
    const errors: FieldErrors = {};

    const nameError = validateName(uname);
    if (nameError) errors.uname = nameError;

    const emailError = validateEmail(email);
    if (emailError) errors.email = emailError;

    const passwordError = validatePassword(password);
    if (passwordError) errors.password = passwordError;

    const confirmError = validateConfirmPassword(confirmPass, password);
    if (confirmError) errors.confirmPass = confirmError;

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  // Handle field changes with error clearing
  function handleNameChange(value: string) {
    setUname(value);
    if (fieldErrors.uname) {
      setFieldErrors((prev) => ({ ...prev, uname: undefined }));
    }
    if (error) setError("");
  }

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
    // Also clear confirm password error if passwords now match
    if (fieldErrors.confirmPass && value === confirmPass) {
      setFieldErrors((prev) => ({ ...prev, confirmPass: undefined }));
    }
    if (error) setError("");
  }

  function handleConfirmPasswordChange(value: string) {
    setConfirmPass(value);
    if (fieldErrors.confirmPass) {
      setFieldErrors((prev) => ({ ...prev, confirmPass: undefined }));
    }
    if (error) setError("");
  }

  async function handleSubmit(e: FormEvent<HTMLElement>) {
    e.preventDefault();
    setError("");

    if (!validateForm()) {
      return;
    }

    try {
      await signup({ email, password, uname });
      navigate("/login");
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (typeof detail === "string" && detail.trim()) {
          setError(detail);
          return;
        }
      }

      setError("Signup failed. Please try again.");
    }
  }

  return (
    <div className="flex items-center justify-center h-screen w-full px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create an account</CardTitle>
          <CardDescription>
            Enter your information below to create your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <FieldGroup>
              {error && (
                <div className="text-destructive text-sm font-medium text-center p-2 bg-destructive/10 rounded-md border border-destructive/20">
                  {error}
                </div>
              )}

              <Field data-invalid={!!fieldErrors.uname}>
                <FieldLabel htmlFor="uname">Name</FieldLabel>
                <Input
                  id="uname"
                  type="text"
                  placeholder="Dexter"
                  value={uname}
                  onChange={(e) => handleNameChange(e.target.value)}
                  aria-invalid={!!fieldErrors.uname}
                  aria-describedby={
                    fieldErrors.uname ? "uname-error" : undefined
                  }
                />
                {fieldErrors.uname && (
                  <FieldError id="uname-error">{fieldErrors.uname}</FieldError>
                )}
              </Field>

              <Field data-invalid={!!fieldErrors.email}>
                <FieldLabel htmlFor="email">Email</FieldLabel>
                <Input
                  id="email"
                  type="email"
                  placeholder="dexter@example.com"
                  value={email}
                  onChange={(e) => handleEmailChange(e.target.value)}
                  aria-invalid={!!fieldErrors.email}
                  aria-describedby={
                    fieldErrors.email ? "email-error" : undefined
                  }
                />
                {fieldErrors.email && (
                  <FieldError id="email-error">{fieldErrors.email}</FieldError>
                )}
              </Field>

              <FieldGroup className="grid grid-cols-2">
                <Field data-invalid={!!fieldErrors.password}>
                  <FieldLabel htmlFor="password">Password</FieldLabel>
                  <PasswordInput
                    id="password"
                    value={password}
                    onChange={(e) => handlePasswordChange(e.target.value)}
                    aria-invalid={!!fieldErrors.password}
                    aria-describedby={
                      fieldErrors.password ? "password-error" : undefined
                    }
                  />
                  {fieldErrors.password && (
                    <FieldError id="password-error">
                      {fieldErrors.password}
                    </FieldError>
                  )}
                </Field>

                <Field data-invalid={!!fieldErrors.confirmPass}>
                  <FieldLabel htmlFor="confirm-password">
                    Confirm Password
                  </FieldLabel>
                  <PasswordInput
                    id="confirm-password"
                    value={confirmPass}
                    onChange={(e) =>
                      handleConfirmPasswordChange(e.target.value)
                    }
                    aria-invalid={!!fieldErrors.confirmPass}
                    aria-describedby={
                      fieldErrors.confirmPass
                        ? "confirm-password-error"
                        : undefined
                    }
                  />
                  {fieldErrors.confirmPass && (
                    <FieldError id="confirm-password-error">
                      {fieldErrors.confirmPass}
                    </FieldError>
                  )}
                </Field>
              </FieldGroup>

              <ValidationChecklist rules={passwordValidationRules} />

              <FieldGroup>
                <Field>
                  <Button type="submit" className="w-full">
                    Create Account
                  </Button>

                  <FieldDescription className="px-6 text-center">
                    Already have an account? <Link to="/login">Sign in</Link>
                  </FieldDescription>
                </Field>
              </FieldGroup>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
