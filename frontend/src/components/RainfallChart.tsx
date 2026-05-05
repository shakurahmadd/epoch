import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { Box, Typography, Paper } from '@mui/material'
import type { ClimateMetric } from '../types/climate'

interface Props {
  metrics: ClimateMetric[]
  birthYear: number
  stationName: string
}

export default function RainfallChart({ metrics, birthYear, stationName }: Props) {
  const data = metrics
    .filter((m) => m.avg_prcp !== null)
    .sort((a, b) => a.year - b.year)

  if (data.length < 5) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>Rainfall trend — {stationName}</Typography>
        <Typography color="text.secondary">
          Not enough rainfall data for this station ({data.length} year{data.length !== 1 ? 's' : ''} recorded).
        </Typography>
      </Paper>
    )
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Rainfall trend — {stationName}
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Average daily precipitation (mm)
      </Typography>
      <Box sx={{ width: '100%', height: 320 }}>
        <ResponsiveContainer>
          <BarChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="year" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} unit="mm" />
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(2)}mm`, 'Avg daily precip']}
            />
            <Legend />
            <ReferenceLine
              x={birthYear}
              stroke="#f59e0b"
              strokeDasharray="4 4"
              label={{ value: 'Born', fill: '#f59e0b', fontSize: 12 }}
            />
            <Bar
              dataKey="avg_prcp"
              name="Avg daily precip"
              fill="#38bdf8"
              opacity={0.8}
              radius={[2, 2, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  )
}
