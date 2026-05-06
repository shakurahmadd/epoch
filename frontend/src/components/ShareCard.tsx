import { useRef } from 'react'
import { Box, Typography, Button, Divider } from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'
import html2canvas from 'html2canvas'
import type { ClimateMetric } from '../types/climate'

interface ShareCardProps {
  stationName: string
  birthYear: number
  metrics: ClimateMetric[]
  narrative: string
}

function calcTempChange(metrics: ClimateMetric[], birthYear: number): number | null {
  const birthMetric = metrics.find(m => m.year === birthYear && m.avg_max_temp !== null)
  const sorted = [...metrics].filter(m => m.avg_max_temp !== null).sort((a, b) => b.year - a.year)
  const recentMetric = sorted[0]
  if (!birthMetric || !recentMetric) return null
  return recentMetric.avg_max_temp! - birthMetric.avg_max_temp!
}

function firstSentence(text: string): string {
  const match = text.match(/[^.!?]*[.!?]/)
  return match ? match[0].trim() : text.slice(0, 120)
}

export default function ShareCard({ stationName, birthYear, metrics, narrative }: ShareCardProps) {
  const cardRef = useRef<HTMLDivElement>(null)
  const tempChange = calcTempChange(metrics, birthYear)
  const sign = tempChange !== null && tempChange > 0 ? '+' : ''

  async function handleDownload() {
    if (!cardRef.current) return
    await document.fonts.ready
    const canvas = await html2canvas(cardRef.current, { scale: 2, useCORS: true })
    const link = document.createElement('a')
    link.download = `epoch-${stationName.replace(/\s+/g, '-').toLowerCase()}-${birthYear}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
  }

  return (
    <Box sx={{ mt: 2 }}>
      <Box
        ref={cardRef}
        sx={{
          background: 'linear-gradient(135deg, #0f1724 0%, #1a2d4a 100%)',
          border: '1px solid rgba(255,255,255,0.12)',
          borderRadius: 3,
          p: 4,
          color: '#fff',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* subtle background accent */}
        <Box
          sx={{
            position: 'absolute',
            top: -60,
            right: -60,
            width: 200,
            height: 200,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(255,100,50,0.15) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />

        <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.5)', letterSpacing: 3, fontSize: '0.65rem' }}>
          EPOCH · CLIMATE CHANGE, MADE PERSONAL
        </Typography>

        <Typography variant="h6" sx={{ mt: 0.5, fontWeight: 600, color: 'rgba(255,255,255,0.85)' }}>
          {stationName} · born {birthYear}
        </Typography>

        <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)', my: 2 }} />

        {/* hero number */}
        {tempChange !== null ? (
          <Box sx={{ my: 2 }}>
            <Typography
              sx={{
                fontSize: '4rem',
                fontWeight: 800,
                lineHeight: 1,
                color: tempChange > 0 ? '#ff6432' : '#4fc3f7',
                letterSpacing: '-2px',
              }}
            >
              {sign}{tempChange.toFixed(1)}°C
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.55)', mt: 0.5 }}>
              average daily max temperature change since {birthYear}
            </Typography>
          </Box>
        ) : (
          <Typography sx={{ color: 'rgba(255,255,255,0.4)', my: 2 }}>
            Temperature data unavailable for {birthYear}
          </Typography>
        )}

        <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)', my: 2 }} />

        <Typography
          variant="body1"
          sx={{
            color: 'rgba(255,255,255,0.75)',
            fontStyle: 'italic',
            lineHeight: 1.6,
            fontSize: '0.95rem',
          }}
        >
          "{firstSentence(narrative)}"
        </Typography>

        <Typography
          variant="caption"
          sx={{ display: 'block', mt: 3, color: 'rgba(255,255,255,0.3)', fontSize: '0.65rem' }}
        >
          epochclimate.app · data: Met Office MIDAS Open
        </Typography>
      </Box>

      <Button
        variant="outlined"
        startIcon={<DownloadIcon />}
        onClick={handleDownload}
        sx={{ mt: 1.5 }}
        size="small"
      >
        Download as image
      </Button>
    </Box>
  )
}
