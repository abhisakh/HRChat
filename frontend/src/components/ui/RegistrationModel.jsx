import React, { useState } from 'react';
import { registerUser } from '../../lib/api';

const RegistrationModel = ({ adminId, onClose }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    role: 'employee',
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    position: '',
    department: '',
    skills: '',
    location: '',
    hire_date: new Date().toISOString().split('T')[0],
    supervisor: '',
    salary: '',
    available_pto: 15
  });

  const [status, setStatus] = useState({ type: '', msg: '' });

  // --- NEW: Hashing Helper ---
  const hashPassword = async (password) => {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  /*
  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus({ type: 'loading', msg: 'Syncing with Umbrella mainframe...' });

    try {
      // 🛡️ STEP 1: Hash the password on the client side
      const securePassword = await hashPassword(formData.password);

      // 🛡️ STEP 2: Send the payload with the hashed password
      const result = await registerUser({
        ...formData,
        password: securePassword,
        admin_id: adminId
      });

      if (result.status === 'success') {
        setStatus({ type: 'success', msg: `Personnel ID ${result.user_id} registered.` });
        setTimeout(() => onClose(), 2000);
      }
    } catch (err) {
      setStatus({ type: 'error', msg: err.message });
    }
  };
  */

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus({ type: 'loading', msg: 'Syncing with Umbrella mainframe...' });

    try {
      // ✅ REVERTED: Send the plain password; let the Backend hash it securely
      const result = await registerUser({
        ...formData,
        admin_id: adminId
      });

      if (result.status === 'success') {
        setStatus({ type: 'success', msg: `Personnel ID ${result.user_id} registered.` });
        setTimeout(() => onClose(), 2000);
      }
    } catch (err) {
      setStatus({ type: 'error', msg: err.message });
    }
  };

  return (
    <div className="modal-overlay">
      <div className="registration-modal">
        <div className="modal-header">
          <h2>Personnel Provisioning</h2>
          <button onClick={onClose} className="close-btn">&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="reg-form">
          <div className="form-section">
            <h3>🔐 Authentication</h3>
            <div className="input-group">
              <input name="username" placeholder="Username" required onChange={handleChange} />
              <input name="password" type="password" placeholder="Temporary Password" required onChange={handleChange} />
              <select name="role" value={formData.role} onChange={handleChange}>
                <option value="employee">Employee</option>
                <option value="hr">HR Officer</option>
                <option value="admin">Administrator</option>
              </select>
            </div>
          </div>

          <div className="form-section">
            <h3>👤 Profile Details</h3>
            <div className="input-grid">
              <input name="first_name" placeholder="First Name" required onChange={handleChange} />
              <input name="last_name" placeholder="Last Name" required onChange={handleChange} />
              <input name="email" type="email" placeholder="Email" required onChange={handleChange} />
              <input name="phone_number" placeholder="Phone" onChange={handleChange} />
            </div>
          </div>

          <div className="form-section">
            <h3>🏢 Employment</h3>
            <div className="input-grid">
              <input name="position" placeholder="Job Title" required onChange={handleChange} />
              <input name="department" placeholder="Department" required onChange={handleChange} />
              <input name="location" placeholder="Office Location" onChange={handleChange} />
              <input name="supervisor" placeholder="Supervisor" onChange={handleChange} />
              <input name="skills" placeholder="Skills" onChange={handleChange} />
              <input name="salary" type="number" placeholder="Annual Salary" required onChange={handleChange} />
              <div className="date-input">
                <label>Hire Date:</label>
                <input name="hire_date" type="date" value={formData.hire_date} onChange={handleChange} />
              </div>
              <input name="available_pto" type="number" placeholder="Initial PTO" onChange={handleChange} />
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" onClick={onClose} className="cancel-btn">Abort</button>
            <button type="submit" className="submit-btn">Finalize Entry</button>
          </div>

          {status.msg && <div className={`status-banner ${status.type}`}>{status.msg}</div>}
        </form>
      </div>
    </div>
  );
};

export default RegistrationModel;