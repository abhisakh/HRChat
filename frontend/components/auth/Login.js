import React, { useState } from 'react';
import { loginUser } from '../../lib/api';

function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevents the page from refreshing
    try {
      const data = await loginUser(username, password);
      // If successful, send the data back up to App.js
      onLoginSuccess(data);
    } catch (err) {
      setError("Unauthorized: Check your credentials.");
    }
  };

  return (
    <div className="login-card">
      <h2>Umbrella Corp HR Login</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Username"
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit">Enter Portal</button>
      </form>
    </div>
  );
}

export default Login;