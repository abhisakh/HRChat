import React, { useState } from 'react';
import { sendChatMessage } from '../../lib/api';

/**
 * ChatWindow.js
 * Manages the conversation state and communicates with the LangGraph agent.
 */
function ChatWindow({ user, onLogout }) {
  const [messages, setMessages] = useState([]); // Array of {role, content}
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false); // To show "AI is thinking..."

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // 1. Update UI with the User's message immediately
    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    setIsLoading(true);

    try {
      // 2. Call the Backend API (using the user_id from props)
      const data = await sendChatMessage(user.user_id, currentInput);

      // 3. Add the AI's response to the UI
      const aiMessage = { role: "assistant", content: data.answer };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Chat Error:", error);
      setMessages((prev) => [...prev, { role: "assistant", content: "Error: Could not reach the HR server." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h3>Umbrella Corp Assistant ({user.role})</h3>
        <button onClick={onLogout}>Logout</button>
      </header>

      <div className="messages-area">
        {messages.map((msg, index) => (
          <div key={index} className={`message-bubble ${msg.role}`}>
            <strong>{msg.role === "user" ? "You" : "AI"}:</strong> {msg.content}
          </div>
        ))}
        {isLoading && <div className="loading">AI is searching records...</div>}
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          placeholder="Ask about salary, policies, or status..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>Send</button>
      </form>
    </div>
  );
}

export default ChatWindow;