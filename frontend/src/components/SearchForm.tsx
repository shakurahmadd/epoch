import { useState } from 'react'
import { Box, Button, TextField, Typography } from '@mui/material'
import type { SearchValues } from '../types/climate'

// Props is the interface for what this component receives from its parent.
// onSearch is a function — (values: SearchValues) => void means it takes
// SearchValues and returns nothing (void = no return value).
interface Props {
  onSearch: (values: SearchValues) => void
  loading: boolean
}

// Destructuring props: { onSearch, loading } pulls the two values out by name.
// This is equivalent to: function SearchForm(props) { const onSearch = props.onSearch ... }
export default function SearchForm({ onSearch, loading }: Props) {
  // Local state for the two input fields. These only live inside this component —
  // the parent (ClimateTimeline) doesn't need to know about them until submit.
  const [postcode, setPostcode] = useState<string>('')
  const [birthYear, setBirthYear] = useState<string>('')

  // React.FormEvent is the TypeScript type for a form submit event.
  // e.preventDefault() stops the browser from refreshing the page on submit.
  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!postcode || !birthYear) return
    // Call the parent's onSearch with the typed SearchValues shape.
    // parseInt converts the birthYear string to a number.
    onSearch({ postcode: postcode.trim().toUpperCase(), birthYear: parseInt(birthYear, 10) })
  }

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}
    >
      <Typography variant="h2" fontWeight={700} textAlign="center">
        Epoch
      </Typography>
      <Typography variant="h6" color="text.secondary" textAlign="center">
        Climate change, made personal
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
        <TextField
          label="UK Postcode"
          placeholder="e.g. LS1 1BA"
          value={postcode}
          onChange={(e) => setPostcode(e.target.value)}
          required
          sx={{ width: 200 }}
        />
        <TextField
          label="Birth Year"
          placeholder="e.g. 1990"
          type="number"
          value={birthYear}
          onChange={(e) => setBirthYear(e.target.value)}
          inputProps={{ min: 1950, max: 2010 }}
          required
          sx={{ width: 160 }}
        />
        <Button
          type="submit"
          variant="contained"
          size="large"
          disabled={loading}
          sx={{ height: 56 }}
        >
          {loading ? 'Loading…' : 'Show my climate'}
        </Button>
      </Box>
    </Box>
  )
}
