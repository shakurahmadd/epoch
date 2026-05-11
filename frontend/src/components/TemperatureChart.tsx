import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ReferenceArea, ResponsiveContainer, Legend,
} from 'recharts'
import { Box, Typography, Paper } from '@mui/material'
import type { ClimateMetric, ForecastPoint, AnomalyPeriod } from '../types/climate'

interface Props {
  metrics: ClimateMetric[]
  forecast: ForecastPoint[]
  birthYear: number
  stationName: string
  anomalies: AnomalyPeriod[]
}

interface ChartRow {
  year: number
  avg_max_temp: number | null
  q10: number | null
  q50: number | null
  q90: number | null
  anomaly: { severity: number; start_date: string; end_date: string } | null
}

export default function TemperatureChart({ metrics, forecast, birthYear, stationName, anomalies }: Props) {
  const historical: ChartRow[] = metrics
    .filter((m) => m.avg_max_temp !== null)
    .sort((a, b) => a.year - b.year)
    .map((m) => {
      const anomaly = anomalies.find((a) => {
        const start = new Date(a.start_date).getFullYear()
        const end = new Date(a.end_date).getFullYear()
        return m.year >= start && m.year <= end
      }) ?? null
      return {
        year: m.year,
        avg_max_temp: m.avg_max_temp,
        q10: null,
        q50: null,
        q90: null,
        anomaly: anomaly ? { severity: anomaly.severity, start_date: anomaly.start_date, end_date: anomaly.end_date } : null,
      }
    })

  const forecastRows: ChartRow[] = forecast.map((f) => ({
    year: f.year,
    avg_max_temp: null,
    q10: f.q10,
    q50: f.q50,
    q90: f.q90,
    anomaly: null,
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
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null
                const row = payload[0].payload as ChartRow
                return (
                  <Box sx={{ bgcolor: '#1e293b', p: 1.5, borderRadius: 1, fontSize: 12 }}>
                    <Typography variant="body2" fontWeight={600}>{row.year}</Typography>
                    {payload.map((p) =>
                      p.value != null ? (
                        <Typography key={p.dataKey as string} variant="body2" sx={{ color: p.color }}>
                          {p.name}: {(p.value as number).toFixed(2)}°C
                        </Typography>
                      ) : null
                    )}
                    {row.anomaly && (
                      <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid #334155' }}>
                        <Typography variant="body2" sx={{ color: '#94a3b8' }}>
                          ⚠ Anomalous period
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#94a3b8' }}>
                          {row.anomaly.start_date} → {row.anomaly.end_date}
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#94a3b8' }}>
                          Severity: {row.anomaly.severity}× threshold
                        </Typography>
                      </Box>
                    )}
                  </Box>
                )
              }}
            />
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
            {anomalies.map((a, i) => (
              <ReferenceArea
                key={i}
                x1={new Date(a.start_date).getFullYear()}
                x2={new Date(a.end_date).getFullYear()}
                fill="#94a3b8"
                fillOpacity={0.12}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  )
}
