import React, { useState } from 'react';
import ChatWindow from "./components/chat/ChatWindow";
import Login from "./components/auth/Login";
import './App.css'; // This makes the styles available to all children

function App() {
  const [user, setUser] = useState(null);

  const handleLogin = (userData) => setUser(userData);
  const handleLogout = () => setUser(null);

  return (
    <div className="app-container">
      {!user ? (
        /* CHANGE: 'onLogin' to 'onLoginSuccess' to match your Login.jsx */
        <Login onLoginSuccess={handleLogin} />
      ) : (
        <ChatWindow user={user} onLogout={handleLogout} />
      )}
    </div>
  );
}

export default App;