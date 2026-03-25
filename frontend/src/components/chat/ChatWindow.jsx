import React, { useState, useEffect, useRef } from 'react';
import EmployeeCard from './EmployeeCard';

const ChatWindow = ({ user, onLogout }) => {
  const [messages, setMessages] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
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
          if (data.logs) setAuditLogs(data.logs);
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
      setMessages(prev => [...prev, { role: 'assistant', content: "🚨 Terminal link severed. Check backend status." }]);
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
                      /* NO BUBBLE WRAPPER AT ALL */
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
          /* --- ENHANCED AUDIT LOGS VIEW --- */
          <div className="audit-logs-container" style={{ padding: '40px', color: '#2d3436', overflowY: 'auto' }}>
            <h2 style={{ marginBottom: '8px', fontSize: '24px' }}>Security Audit Trail</h2>
            <p style={{ color: '#636e72', marginBottom: '30px' }}>User ID: <strong>{user.user_id}</strong> | Terminal Access: Authorized</p>

            <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '12px', boxShadow: '0 4px 15px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
              <thead>
                <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #eee' }}>
                  <th style={{ padding: '16px', textAlign: 'left', width: '35%' }}>Exchange (Q&A)</th>
                  <th style={{ padding: '16px', textAlign: 'left' }}>Origin</th>
                  <th style={{ padding: '16px', textAlign: 'left' }}>Execution Path</th>
                  <th style={{ padding: '16px', textAlign: 'left' }}>Security Status</th>
                  <th style={{ padding: '16px', textAlign: 'left' }}>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.length > 0 ? auditLogs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid #f1f1f1' }}>
                    {/* 1. Q&A */}
                    <td style={{ padding: '16px' }}>
                      <div style={{ fontWeight: '600', color: '#2d3436' }}>Q: {log.question}</div>
                      <div style={{ fontSize: '12px', color: '#636e72', fontStyle: 'italic', marginTop: '4px' }}>
                        A: {log.answer?.substring(0, 80)}...
                      </div>
                    </td>

                    {/* 2. Origin */}
                    <td style={{ padding: '16px' }}>
                      <span style={{
                        fontSize: '11px',
                        fontWeight: 'bold',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        background: log.source_used === 'sql' ? '#e1f5fe' : '#f3e5f5',
                        color: log.source_used === 'sql' ? '#0288d1' : '#7b1fa2'
                      }}>
                        {log.source_used?.toUpperCase() || 'UNKNOWN'}
                      </span>
                    </td>

                    {/* 3. Execution Path */}
                    <td style={{ padding: '16px' }}>
                      <code style={{ fontSize: '11px', color: '#d63031', background: '#fff5f5', padding: '2px 4px', borderRadius: '4px', fontFamily: 'monospace' }}>
                        {log.node_path}
                      </code>
                    </td>

                    {/* 4. Security Status Badge */}
                    <td style={{ padding: '16px' }}>
                      <span style={{
                        fontSize: '10px',
                        fontWeight: '800',
                        letterSpacing: '0.5px',
                        padding: '2px 6px',
                        borderRadius: '12px',
                        border: log.source_used === 'sql' ? '1px solid #0288d1' : '1px solid #7b1fa2',
                        color: log.source_used === 'sql' ? '#0288d1' : '#7b1fa2',
                        textTransform: 'uppercase'
                      }}>
                        {log.source_used === 'sql' ? '🔒 DB Record' : '📄 Doc Search'}
                      </span>
                    </td>

                    {/* 5. Real Timestamp */}
                    <td style={{ padding: '16px', fontSize: '12px', color: '#b2bec3', whiteSpace: 'nowrap' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan="5" style={{ padding: '40px', textAlign: 'center', color: '#b2bec3' }}>
                      No audit records found in terminal history.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
};

export default ChatWindow;