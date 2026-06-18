import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import './index.css'

import { AuthProvider } from './context/AuthContext'
import { RutaProtegida } from './components/auth/RutaProtegida'

import NuevaActa from './views/NuevaActa.jsx'
import Dashboard from './views/Dashboard.jsx'
import Historial from './views/Historial.jsx'
import NuevoDescuento from './views/NuevoDescuento'
import Login from './views/Login.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <HashRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            path="/dashboard"
            element={
              <RutaProtegida>
                <Dashboard />
              </RutaProtegida>
            }
          />

          <Route
            path="/nuevo-descuento"
            element={
              <RutaProtegida>
                <NuevoDescuento />
              </RutaProtegida>
            }
          />


          <Route
            path="/nueva-acta"
            element={
              <RutaProtegida>
                <NuevaActa />
              </RutaProtegida>
            }
          />

          <Route
            path="/historial"
            element={
              <RutaProtegida>
                <Historial />
              </RutaProtegida>
            }
          />

          {/* Redirección por defecto */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
        <Toaster position="top-center" richColors />
      </HashRouter>
    </AuthProvider>
  </StrictMode>,
)
