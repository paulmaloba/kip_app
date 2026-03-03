// ── Auth ──────────────────────────────────────────────────────────────────────
export interface KIPUser {
  id:       number
  name:     string
  email:    string
  location: string | null
}

export interface AuthState {
  user:          KIPUser | null
  accessToken:   string | null
  refreshToken:  string | null
  isAuthenticated: boolean
}

// ── Response types ────────────────────────────────────────────────────────────
export type ResponseType =
  | 'business_idea'
  | 'economic_analysis'
  | 'crisis'
  | 'regulatory'
  | 'general'

export type LogType =
  | 'revenue' | 'expense' | 'challenge'
  | 'milestone' | 'customer' | 'supplier' | 'staff' | 'general'

// ── Chat ──────────────────────────────────────────────────────────────────────
export interface ChatMessage {
  id:            string
  role:          'user' | 'assistant'
  content:       string
  response_type?: ResponseType
  structured?:   any
  timestamp:     Date
}

// ── Business ──────────────────────────────────────────────────────────────────
export interface BusinessProfile {
  id:              number
  name:            string
  sector:          string
  stage:           'idea' | 'planning' | 'launched' | 'growing' | 'struggling'
  location:        string
  start_capital:   number | null
  monthly_revenue: number | null
  employees:       number
}

export interface BusinessLog {
  id:              number
  log_type:        LogType
  title:           string
  description:     string | null
  amount_zmw:      number | null
  kip_analysis:    string | null
  kip_suggestions: any[]
  created_at:      string
}

// ── Forecast ──────────────────────────────────────────────────────────────────
export interface ForecastData {
  indicator:     string
  current:       number
  forecast_3m:   number
  forecast_6m:   number
  forecast_12m:  number
  chart_data:    { date: string; historical: number | null; forecast: number | null }[]
  model_source:  string
}

export interface DashboardMetrics {
  food_inflation:    number
  nonfood_inflation: number
  usd_zmw:           number
  copper_usd_ton:    number
}

export interface CPIIndicator {
  name:         string
  current:      number
  yoy_pct:      number
  forecast_12m: number
  trend:        'up' | 'down' | 'flat'
  color:        string
  seasonal_tip: string
}

// ── Structured response payloads ──────────────────────────────────────────────
export interface BusinessIdeaData {
  title:                string
  tagline:              string
  best_for_location:    string[]
  startup_capital_min:  number
  startup_capital_max:  number
  monthly_revenue_min:  number
  monthly_revenue_max:  number
  breakeven_months:     number
  why_zambia:           string
  first_steps:          { step: number; action: string; cost: string; timeframe: string }[]
  main_risk:            string
  funding_options:      string[]
  kip_verdict:          string
}

export interface CrisisData {
  severity:           'high' | 'medium' | 'low'
  situation_assessment: string
  do_now:             { action: string; why?: string }[]
  do_this_week:       { action: string; why?: string }[]
  avoid_this_mistake: string
  who_can_help:       string[]
  honest_outlook:     string
}

export interface RegulatoryData {
  business_type:   string
  total_time:      string
  total_cost_min:  number
  total_cost_max:  number
  pro_tip:         string
  checklist: {
    step:       number
    institution: string
    action:     string
    cost_zmw:   number
    timeframe:  string
    where:      string
    documents:  string[]
    status:     'mandatory' | 'optional'
  }[]
}

export interface EconomicData {
  headline:              string
  summary:               string
  data_points:           { label: string; value: string; trend: 'up' | 'down' | 'flat' }[]
  business_implications: string[]
  forecast_note:         string
  sources:               string[]
}
