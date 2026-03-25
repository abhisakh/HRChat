import React, { useState } from 'react';
import { loginUser } from '../../lib/api';

function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); // Clear old errors

    // DEBUG: Look at your browser console (F12) to see if these are empty
    console.log("React sending to API:", { username, password });

    try {
      const data = await loginUser(username, password);
      console.log("Login Success:", data);
      onLoginSuccess(data);
    } catch (err) {
      console.error("Login Error:", err);
      setError("Unauthorized: Check your credentials.");
    }
  };

  return (
    <div className="login-card">
      <h2>Umbrella Corp HR Login</h2>
      {error && <p className="error-message" style={{ color: 'red' }}>{error}</p>}

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)} // Correct
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)} // <--- CHANGE THIS (was setUsername)
        />
        <button type="submit">Enter Portal</button>
      </form>
    </div>
  );
}

export default Login;