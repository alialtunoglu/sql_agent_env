export interface ChartDataPoint {
  name: string;
  value: number;
  [key: string]: any;
}

export interface ChatResponse {
  answer: string;
  session_id: string;
  chart_data?: ChartDataPoint[] | null;
  chart_type?: string | null;
  sql_query?: string | null;
  requires_approval?: boolean;
  error?: string | null;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  chartData?: ChartDataPoint[] | null;
  sqlQuery?: string | null;
  requiresApproval?: boolean;
}
