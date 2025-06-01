import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { WebsocketProvider } from './WebsocketProvider.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <WebsocketProvider>
      <App />
    </WebsocketProvider>
  </StrictMode>,
)
