import { Paper, Typography, Box } from '@mui/material'
import FormatQuoteIcon from '@mui/icons-material/FormatQuote'

interface Props {
  narrative: string
  region: string
  birthYear: number
}

export default function NarrativeCard({ narrative, region, birthYear }: Props) {
  return (
    <Paper
      sx={{
        p: 4,
        borderLeft: '4px solid',
        borderColor: 'primary.main',
        background: 'linear-gradient(135deg, #111827 0%, #0f172a 100%)',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
        <FormatQuoteIcon sx={{ color: 'primary.main', fontSize: 40, mt: -0.5 }} />
        <Box>
          <Typography variant="body1" lineHeight={1.8} sx={{ fontStyle: 'italic' }}>
            {narrative}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            {region} · Since {birthYear}
          </Typography>
        </Box>
      </Box>
    </Paper>
  )
}
