import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

// Self-hosted via @fontsource so the demo renders identically on a conference
// wifi that cannot reach Google Fonts. Only the weights we actually use.
import '@fontsource/fraunces/400.css'
import '@fontsource/fraunces/600.css'
import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'

import App from './App.jsx'
import { AuthProvider } from './auth.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* Opting into the v7 behaviours now keeps the demo console clean — an
        officer or a judge looking over a shoulder should see no warnings. */}
    <BrowserRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      {/* Inside the router, not outside it: the provider signs a person out
          when any request comes back 401, and the screens that react to that
          are routes. */}
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
