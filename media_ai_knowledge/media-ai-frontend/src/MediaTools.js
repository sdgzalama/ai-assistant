// MediaTools.js
import React, { useState } from 'react';

export const MediaTools = ({ onToolSelect }) => {
  const tools = [
    {
      id: 'law-checker',
      name: 'Media Law Checker',
      description: 'Verify if your content complies with Tanzanian media laws',
      icon: '⚖️'
    },
    {
      id: 'ethics-guide',
      name: 'Ethics Guide', 
      description: 'Check journalism ethics for your story',
      icon: '📝'
    },
    {
      id: 'audience-insights',
      name: 'Audience Insights',
      description: 'Get insights about Tanzanian media audience',
      icon: '👥'
    },
    {
      id: 'content-strategy',
      name: 'Content Strategy',
      description: 'Plan your content strategy',
      icon: '📊'
    }
  ];

  return (
    <div style={{
      padding: '20px',
      background: '#f8f9fa',
      borderRadius: '12px',
      marginBottom: '20px'
    }}>
      <h3 style={{ marginTop: 0, color: '#1a73e8' }}>Media Tools</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
        {tools.map(tool => (
          <div
            key={tool.id}
            onClick={() => onToolSelect(tool)}
            style={{
              padding: '15px',
              background: 'white',
              borderRadius: '8px',
              border: '1px solid #eaeaea',
              cursor: 'pointer',
              transition: 'all 0.2s',
              textAlign: 'center'
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = 'none';
            }}
          >
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>{tool.icon}</div>
            <div style={{ fontWeight: '600', fontSize: '14px', marginBottom: '4px' }}>{tool.name}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>{tool.description}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Law Checker Component
export const LawChecker = ({ onClose, onSendMessage }) => {
  const [content, setContent] = useState('');
  const [lawType, setLawType] = useState('media_services_act_2016');

  const laws = [
    { value: 'media_services_act_2016', label: 'Media Services Act, 2016' },
    { value: 'access_to_information_act_2016', label: 'Access to Information Act, 2016' },
    { value: 'cyber_crimes_act_2015', label: 'Cybercrimes Act, 2015' }
  ];

  const checkCompliance = () => {
    if (content.trim()) {
      const message = `Check compliance with ${laws.find(l => l.value === lawType)?.label}:\n\n${content}`;
      onSendMessage(message, 'laws');
      onClose();
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        background: 'white',
        padding: '24px',
        borderRadius: '12px',
        width: '90%',
        maxWidth: '500px',
        maxHeight: '80vh',
        overflow: 'auto'
      }}>
        <h3 style={{ marginTop: 0 }}>Media Law Compliance Check</h3>
        
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
            Select Law:
          </label>
          <select
            value={lawType}
            onChange={(e) => setLawType(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #ddd',
              borderRadius: '6px'
            }}
          >
            {laws.map(law => (
              <option key={law.value} value={law.value}>{law.label}</option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
            Your Content:
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste your content here to check compliance..."
            style={{
              width: '100%',
              height: '150px',
              padding: '12px',
              border: '1px solid #ddd',
              borderRadius: '6px',
              resize: 'vertical',
              fontFamily: 'inherit'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{
              padding: '8px 16px',
              border: '1px solid #ddd',
              background: 'white',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            onClick={checkCompliance}
            disabled={!content.trim()}
            style={{
              padding: '8px 16px',
              border: 'none',
              background: '#1a73e8',
              color: 'white',
              borderRadius: '6px',
              cursor: 'pointer',
              opacity: !content.trim() ? 0.6 : 1
            }}
          >
            Check Compliance
          </button>
        </div>
      </div>
    </div>
  );
};