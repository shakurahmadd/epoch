import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer, Legend,
} from 'recharts'
import { Box, Typography, Paper } from '@mui/material'
import type { ClimateMetric, ForecastPoint } from '../types/climate'

interface Props {
  metrics: ClimateMetric[]
  forecast: ForecastPoint[]
  birthYear: number
  stationName: string
}

interface ChartRow {
  year: number
  avg_max_temp: number | null
  q10: number | null
  q50: number | null
  q90: number | null
}

export default function TemperatureChart({ metrics, forecast, birthYear, stationName }: Props) {
  const historical: ChartRow[] = metrics
    .filter((m) => m.avg_max_temp !== null)
    .sort((a, b) => a.year - b.year)
    .map((m) => ({
      year: m.year,
      avg_max_temp: m.avg_max_temp,
      q10: null,
      q50: null,
      q90: null,
    }))

  const forecastRows: ChartRow[] = forecast.map((f) => ({
    year: f.year,
    avg_max_temp: null,
    q10: f.q10,
    q50: f.q50,
    q90: f.q90,
  }))

  const data = [...historical, ...forecastRows].sort((a, b) => a.year - b.year)

  if (data.length === 0) {
    return <Typography color="text.secondary">No temperature data available.</Typography>
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Temperature — {stationName}
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Historical avg max (°C) with forecast to 2038 (10th / 50th / 90th percentile)
      </Typography>
      <Box sx={{ width: '100%', height: 360 }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="year" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} unit="°C" />
            <Tooltip formatter={(value: number) => [`${value.toFixed(2)}°C`]} />
            <Legend />
            <ReferenceLine
              x={birthYear}
              stroke="#f59e0b"
              strokeDasharray="4 4"
              label={{ value: 'Born', fill: '#f59e0b', fontSize: 12 }}
            />
            <ReferenceLine
              x={2025}
              stroke="#94a3b8"
              strokeDasharray="4 4"
              label={{ value: 'Now', fill: '#94a3b8', fontSize: 12 }}
            />
            <Line
              type="monotone"
              dataKey="avg_max_temp"
              name="Historical"
              stroke="#4fc3f7"
              dot={false}
              strokeWidth={2}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="q50"
              name="Forecast (median)"
              stroke="#f97316"
              dot={false}
              strokeWidth={2}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="q10"
              name="Forecast (low)"
              stroke="#fb923c"
              dot={false}
              strokeWidth={1}
              strokeDasharray="3 3"
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="q90"
              name="Forecast (high)"
              stroke="#fb923c"
              dot={false}
              strokeWidth={1}
              strokeDasharray="3 3"
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  )
}
