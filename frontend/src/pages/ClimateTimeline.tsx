import { useState } from 'react'
import { Container, Box, Alert, CircularProgress, Typography, Divider} from '@mui/material'
import type { TimelineResponse, NarrativeResponse, SearchValues, ForecastResponse } from '../types/climate'
import { fetchTimeline, fetchNarrative, fetchForecast } from '../api/client'
import SearchForm from '../components/SearchForm'
import TemperatureChart from '../components/TemperatureChart'
import RainfallChart from '../components/RainfallChart'
import NarrativeCard from '../components/NarrativeCard'
import ShareCard from '../components/ShareCard'

export default function ClimateTimeline() {
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [searchValues, setSearchValues] = useState<SearchValues | null>(null)
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null)
  const [narrative, setNarrative] = useState<NarrativeResponse | null>(null)
  const [forecast, setForecast] = useState<ForecastResponse | null>(null)

  async function handleSearch(values: SearchValues) {
    setLoading(true)
    setError(null)
    setTimeline(null)
    setNarrative(null)
    setSearchValues(values)
    setForecast(null)

    try {
      const timelineData = await fetchTimeline(values.postcode, values.birthYear)
      setTimeline(timelineData)

      const narrativeData = await fetchNarrative(values.birthYear, timelineData.region, values.postcode)
      setNarrative(narrativeData)

      const forecastData = await fetchForecast(values.postcode)
      setForecast(forecastData)
    } catch (err) {
      setError('Could not load climate data. Check the postcode and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <SearchForm onSearch={handleSearch} loading={loading} />

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 6 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 4 }}>
          {error}
        </Alert>
      )}

      {timeline && searchValues && (
        <Box sx={{ mt: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <Box>
            <Typography variant="h5" fontWeight={600}>
              {timeline.location} · born {searchValues.birthYear}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {timeline.total_years} years of data · {timeline.station_name}
              {timeline.trend_temp !== null && (
                <> · {timeline.trend_temp > 0 ? '+' : ''}{timeline.trend_temp.toFixed(2)}°C per decade</>
              )}
            </Typography>
          </Box>

          <TemperatureChart
            metrics={timeline.metrics}
            forecast={forecast?.forecast ?? []}
            birthYear={searchValues.birthYear}
            stationName={timeline.station_name}
          />

          <RainfallChart
            metrics={timeline.metrics}
            birthYear={searchValues.birthYear}
            stationName={timeline.station_name}
          />
          
          {narrative && (
            <>
              <Divider />
              <NarrativeCard
                narrative={narrative.narrative}
                region={narrative.region}
                birthYear={narrative.birth_year}
              />
              <ShareCard
                stationName={timeline.station_name}
                birthYear={searchValues.birthYear}
                metrics={timeline.metrics}
                narrative={narrative.narrative}
              />
            </>
          )}
        </Box>
      )}
    </Container>
  )
}
