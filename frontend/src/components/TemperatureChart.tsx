import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer, Legend,
} from 'recharts'
import { Box, Typography, Paper } from '@mui/material'
import type { ClimateMetric } from '../types/climate'

interface Props {
  metrics: ClimateMetric[]   // array of per-year records
  birthYear: number
  stationName: string
}

export default function TemperatureChart({ metrics, birthYear, stationName }: Props) {
  // Filter out rows with no temperature data, then sort by year.
  // .filter() and .sort() are standard JavaScript array methods — like Python's
  // list comprehension and sorted().
  const data = metrics
    .filter((m) => m.avg_max_temp !== null)
    .sort((a, b) => a.year - b.year)

  if (data.length === 0) {
    return <Typography color="text.secondary">No temperature data available.</Typography>
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Temperature trend — {stationName}
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Average daily maximum temperature (°C)
      </Typography>
      <Box sx={{ width: '100%', height: 320 }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="year" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} unit="°C" />
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(1)}°C`, 'Avg max temp']}
            />
            <Legend />
            {/* ReferenceLine draws the vertical birth year marker */}
            <ReferenceLine
              x={birthYear}
              stroke="#f59e0b"
              strokeDasharray="4 4"
              label={{ value: 'Born', fill: '#f59e0b', fontSize: 12 }}
            />
            <Line
              type="monotone"
              dataKey="avg_max_temp"
              name="Avg max temp"
              stroke="#4fc3f7"
              dot={false}
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  )
}
