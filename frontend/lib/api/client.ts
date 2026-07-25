const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface ApiErrorBody {
  detail?: string;
  message?: string;
}

function isApiErrorBody(value: unknown): value is ApiErrorBody {
  return typeof value === "object" && value !== null;
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    ...init,
  });

  const isJson = response.headers
    .get("content-type")
    ?.includes("application/json");

  let data: unknown = null;
  if (response.status !== 204 && response.status !== 205) {
    const text = await response.text();
    if (text && isJson) {
      data = JSON.parse(text);
    }
  }

  if (!response.ok) {
    const errorMessage = isApiErrorBody(data)
      ? data.detail ?? data.message
      : undefined;
    throw new ApiError(errorMessage ?? "Request failed", response.status);
  }

  return data as T;
}