//frontend/src/components/chat/ChatWindow.jsx
import React, { useState, useEffect, useRef } from 'react';
import EmployeeCard from './EmployeeCard';
// Import new component
import RegistrationModal from '../ui/RegistrationModel';

const ChatWindow = ({ user, onLogout }) => {
  const [messages, setMessages] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');

  // NEW STATE: Toggle for the Registration Modal
  const [isRegModalOpen, setIsRegModalOpen] = useState(false);

  const scrollRef = useRef(null);

  // 1. FETCH CHAT HISTORY (Persistent Memory)
  useEffect(() => {
    const loadChatHistory = async () => {
      try {
        const response = await fetch(`http://localhost:8000/chat/history/${user.user_id}`);
        const data = await response.json();
        if (data.history) setMessages(data.history);
      } catch (error) {
        console.error("Failed to load history:", error);
      }
    };
    loadChatHistory();
  }, [user.user_id]);

  // 2. FETCH AUDIT LOGS (Security Trail)
  useEffect(() => {
    if (activeTab === 'audit') {
      const loadAuditLogs = async () => {
        try {
          const response = await fetch(`http://localhost:8000/audit/logs/${user.user_id}`);
          const data = await response.json();
          console.log("Mainframe Audit Data:", data); // <--- Add this!
          setAuditLogs(data.logs || data);
        } catch (error) {
          console.error("Failed to load audit logs:", error);
        }
      };
      loadAuditLogs();
    }
  }, [activeTab, user.user_id]);

  // 3. AUTO-SCROLL
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    const userMsg = { role: 'user', content: input };
    const chatHistory = [...messages];

    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: currentInput,
          history: chatHistory,
          user_id: user.user_id,
          role: user.role
        }),
      });
      const data = await response.json();
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        source: data.source
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: "🚨 Terminal link severed." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="app-layout">
      {/* --- SIDEBAR --- */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">☂️</div>
          <h1>Umbrella HR</h1>
        </div>

        <div className="user-profile">
          <div className="user-avatar">
            {(user.first_name || user.user_id).charAt(0).toUpperCase()}
          </div>
          <div className="user-info">
            <span className="user-id" style={{ fontWeight: '600', color: 'white' }}>
              {user.first_name || user.user_id}
            </span>
            <span className={`role-badge ${user.role}`}>
              {(user.role || 'employee').toUpperCase()}
            </span>
          </div>
        </div>

        <nav className="sidebar-nav" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`} onClick={() => setActiveTab('chat')}>
            💬 Chat Assistant
          </button>
          <button className={`nav-item ${activeTab === 'audit' ? 'active' : ''}`} onClick={() => setActiveTab('audit')}>
            📜 Audit Logs
          </button>

          {/* NEW: Conditional Button for Admins/HR only */}
          {(user.role === 'admin' || user.role === 'hr') && (
            <button className="nav-item special-action" onClick={() => setIsRegModalOpen(true)}>
              ➕ Register Personnel
            </button>
          )}
        </nav>

        <button onClick={onLogout} className="logout-btn">Sign Out</button>
      </aside>

{/* --- MAIN CONTENT AREA --- */}
      <main className="chat-area">
        {activeTab === 'chat' ? (
          <>
            <div className="messages-list">
              {messages.length === 0 && (
                <div className="welcome-screen">
                  <div className="logo" style={{ fontSize: '48px', marginBottom: '20px' }}>☂️</div>
                  <h2>Security Cleared.</h2>
                  <p>Welcome back, <strong>{user.first_name || user.user_id}</strong>.</p>
                </div>
              )}
              {messages.map((msg, i) => {
                const isEmployeeCard = msg.role === 'assistant' &&
                  (typeof msg.content === 'object' || (typeof msg.content === 'string' && msg.content.includes('"user_id"')));

                return (
                  <div key={i} className={`message-wrapper ${msg.role}`}>
                    {isEmployeeCard ? (
                      <EmployeeCard data={msg.content} />
                    ) : (
                      <div className="message-bubble">
                        {msg.content}
                        {msg.source && <div className="source-tag">Source: {msg.source.toUpperCase()}</div>}
                      </div>
                    )}
                  </div>
                );
              })}
              {isTyping && (
                <div className="message-wrapper assistant">
                  <div className="message-bubble typing">Searching encrypted database...</div>
                </div>
              )}
              <div ref={scrollRef} />
            </div>

            <div className="input-section">
              <form className="input-box" onSubmit={handleSendMessage}>
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={isTyping ? "Accessing files..." : "Query personnel records..."}
                  disabled={isTyping}
                />
                <button type="submit" className="send-btn" disabled={isTyping || !input.trim()}>➔</button>
              </form>
              <p className="disclaimer">CLASSIFIED INFORMATION • Umbrella Corp © 2026</p>
            </div>
          </>
        ) : (
          /* --- FIXED: AUDIT LOGS TABLE IMPLEMENTATION --- */
          <div className="audit-logs-container">
            <div className="welcome-screen" style={{ textAlign: 'left', margin: '0 0 30px 0', maxWidth: '100%' }}>
              <h2>Security Audit Trail</h2>
              <p>Monitoring access logs for terminal user: <strong>{user.user_id}</strong></p>
            </div>

            {auditLogs.length === 0 ? (
              <div className="message-bubble assistant">No security logs found for this session.</div>
            ) : (
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Query</th>
                    <th>Source</th>
                    <th>Execution Path</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log, index) => (
                    <tr key={index}>
                      <td style={{ fontSize: '13px', color: '#636e72', whiteSpace: 'nowrap' }}>
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td style={{ fontWeight: '500' }}>{log.question}</td>
                      <td>
                        <span className={`badge-base ${log.source_used === 'sql' ? 'badge-sql' : 'badge-doc'}`}>
                          {log.source_used.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        <code className="node-trace">{log.node_path}</code>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </main>

      {/* NEW: Overlay Modal for Registration */}
      {isRegModalOpen && (
        <RegistrationModal
          adminId={user.user_id}
          onClose={() => setIsRegModalOpen(false)}
        />
      )}
    </div>
  );
};

export default ChatWindow;