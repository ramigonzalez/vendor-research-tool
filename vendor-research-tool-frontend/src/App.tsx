import { ThemeProvider } from './contexts/ThemeContext'
import { ResearchPage } from './components/templates/ResearchPage'

function App() {
  return (
    <ThemeProvider>
      <ResearchPage />
    </ThemeProvider>
  )
}

export default App
