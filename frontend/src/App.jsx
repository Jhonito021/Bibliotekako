// src/App.jsx
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/auth/Login'; // Nous allons créer ce fichier juste après

// Composant pour protéger les routes (ex: empêcher l'accès au dashboard sans être connecté)
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) return <div>Chargement...</div>; // En attente de la vérif du token
  if (!user) return <Navigate to="/login" replace />; // Pas connecté -> redirection
  
  return children; // Connecté -> on affiche la page
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Route publique */}
          <Route path="/login" element={<Login />} />
          
          {/* Route protégée (exemple pour le futur Dashboard) */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <div>
                  <h1>Bienvenue sur votre Dashboard !</h1>
                </div>
              </ProtectedRoute>
            } 
          />
          
          {/* Redirection par défaut */}
          <Route path="/" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;