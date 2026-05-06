import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { Box, Typography, Paper } from '@mui/material'
import type { ForecastPoint } from '../types/climate'

interface Props {
  forecast: ForecastPoint[]
  stationName: string
}

export default function ForecastChart({ forecast, stationName }: Props) {
  if (forecast.length === 0) {
    return <Typography color="text.secondary">No forecast data available.</Typography>
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Temperature forecast to 2038 — {stationName}
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Quantile forecast: 10th, 50th, 90th percentile (°C)
      </Typography>
      <Box sx={{ width: '100%', height: 320 }}>
        <ResponsiveContainer>
          <LineChart data={forecast} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="year" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} unit="°C" />
            <Tooltip formatter={(value: number) => [`${value.toFixed(2)}°C`]} />
            <Legend />
            <Line
              type="monotone"
              dataKey="q10"
              name="10th percentile"
              stroke="#64b5f6"
              dot={false}
              strokeWidth={1.5}
              strokeDasharray="4 4"
            />
            <Line
              type="monotone"
              dataKey="q50"
              name="50th percentile"
              stroke="#4fc3f7"
              dot={false}
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="q90"
              name="90th percentile"
              stroke="#ef5350"
              dot={false}
              strokeWidth={1.5}
              strokeDasharray="4 4"
            />
          </LineChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  )
}
