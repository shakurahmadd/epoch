import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'
import ClimateTimeline from './pages/ClimateTimeline'

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#4fc3f7' },
    background: {
      default: '#0a0f1e',
      paper: '#111827',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", sans-serif',
  },
})

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ClimateTimeline />
    </ThemeProvider>
  )
}
