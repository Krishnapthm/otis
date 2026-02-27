import { describe, expect, it } from "vitest";
import { resolveApiBaseUrl } from "./authApi";

describe("resolveApiBaseUrl", () => {
  it("uses provided env URL", () => {
    expect(resolveApiBaseUrl("https://api.example.com")).toBe(
      "https://api.example.com",
    );
  });

  it("falls back to root path when env URL is missing", () => {
    expect(resolveApiBaseUrl(undefined)).toBe("/");
    expect(resolveApiBaseUrl("")).toBe("/");
    expect(resolveApiBaseUrl("   ")).toBe("/");
  });
});
