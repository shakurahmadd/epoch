export interface ClimateMetric {
  year: number
  avg_max_temp: number | null
  avg_min_temp: number | null
  avg_prcp: number | null
  hot_days: number | null
  frost_days: number | null
  heavy_rain_days: number | null
}

export interface TimelineResponse {
  location: string
  birth_year: number
  station_name: string
  region: string
  metrics: ClimateMetric[]
  trend_temp: number | null
  total_years: number
}

export interface NarrativeResponse {
  narrative: string
  region: string
  birth_year: number
}

export interface SearchValues {
  postcode: string
  birthYear: number
}


export interface ForecastPoint {
  year: number
  q10: number
  q50: number
  q90: number 
  
}

export interface ForecastResponse {
  station_name : string
  forecast : ForecastPoint[]
}

export interface AnomalyPeriod {
  start_date: string
  end_date: string
  severity: number
}