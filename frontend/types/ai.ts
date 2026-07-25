export type SentimentLabel = "positive" | "neutral" | "negative" | "frustrated";

export interface AIInsight {
  id: string;
  ticket_id: string;
  summary: string | null;
  sentiment: SentimentLabel | null;
  sentiment_score: number | null;
  predicted_priority: "low" | "medium" | "high" | "urgent" | null;
  suggested_tags: string[];
  internal_ai_notes: string | null;
  model_used: string | null;
  generated_at: string | null;
  updated_at: string;
}

export interface ReplySuggestionRequest {
  instructions?: string;
}

export interface ReplySuggestionResponse {
  reply: string;
}