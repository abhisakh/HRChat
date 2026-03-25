import React, { useState } from 'react';
import Login from './components/auth/Login';
import ChatWindow from './components/chat/ChatWindow';

/**
 * App.js - The Root Component
 * Manages the "Global State" (is the user logged in?)
 */
function App() {
  // 1. Define State: 'user' starts as null.
  // After login, it will look like { user_id: "user_123", role: "employee" }
  const [user, setUser] = useState(null);

  // 2. Logout function to clear the state
  const handleLogout = () => {
    setUser(null);
    console.log("User logged out, state cleared.");
  };

  // 3. Conditional Rendering: This is the "Switch"
  return (
    <div className="app-container">
      {!user ? (
        // If no user, show Login. Pass 'setUser' as a prop so Login can update it.
        <Login onLoginSuccess={(data) => setUser(data)} />
      ) : (
        // If user exists, show Chat. Pass 'user' data and 'handleLogout' down.
        <ChatWindow user={user} onLogout={handleLogout} />
      )}
    </div>
  );
}

export default App;