import React from 'react';

const EmployeeCard = ({ data }) => {
  // Safe parsing in case the LLM returns a string instead of an object
  const profile = typeof data === 'string' ? JSON.parse(data) : data;

  return (
    <div className="employee-card">
      <div className="card-header">
        <div className="avatar-circle">
          {profile.first_name?.[0]}{profile.last_name?.[0]}
        </div>
        <div className="header-text">
          <h3>{profile.first_name} {profile.last_name}</h3>
          <span className="position-label">{profile.position}</span>
        </div>
      </div>

      <div className="card-body">
        <div className="info-row"><strong>📍 Location:</strong> {profile.location}</div>
        <div className="info-row"><strong>🏢 Dept:</strong> {profile.department}</div>
        <div className="info-row"><strong>📧 Email:</strong> {profile.email}</div>

        {profile.skills && (
          <div className="skills-container">
            {profile.skills.split(',').map(skill => (
              <span key={skill} className="skill-tag">{skill.trim()}</span>
            ))}
          </div>
        )}

        {profile.salary && (
          <div className="salary-info">
            💰 Annual Salary: ${profile.salary.toLocaleString()}
          </div>
        )}
      </div>
      <div className="card-footer">
        Umbrella Corp Certified • ID: {profile.user_id}
      </div>
    </div>
  );
};

export default EmployeeCard;