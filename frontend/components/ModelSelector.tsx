'use client';
// frontend/components/ModelSelector.tsx

import { useEffect, useState } from 'react';
import { getLLMConfig, updateLLMConfig, LLMConfigResponse } from '../lib/api';

export default function ModelSelector() {
  const [config, setConfig] = useState<LLMConfigResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    getLLMConfig()
      .then(setConfig)
      .catch((e) => console.error("Failed to load models", e))
      .finally(() => setLoading(false));
  }, []);

  const handleProviderChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (!config || !config.available_models) return;
    const newProvider = e.target.value;
    // Default to the first available model for the new provider
    const newModel = config.available_models[newProvider]?.[0] || '';
    
    setUpdating(true);
    try {
      const updated = await updateLLMConfig(newProvider, newModel);
      setConfig(updated);
    } catch (err: any) {
      alert(err.message || 'Failed to change provider');
      setConfig({ ...config }); 
    } finally {
      setUpdating(false);
    }
  };

  const handleModelChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (!config) return;
    const newModel = e.target.value;
    
    setUpdating(true);
    try {
      const updated = await updateLLMConfig(config.provider, newModel);
      setConfig(updated);
    } catch (err: any) {
      alert(err.message || 'Failed to change model');
      setConfig({ ...config });
    } finally {
      setUpdating(false);
    }
  };

  if (loading || !config || !config.available_models) return null;

  return (
    <div className="model-selector-container">
      <div className="model-selector-label">LLM Provider</div>
      <select 
        className="model-selector-select"
        value={config.provider}
        onChange={handleProviderChange}
        disabled={updating}
      >
        {config.available_providers.map((p) => (
          <option key={p} value={p}>
            {p.charAt(0).toUpperCase() + p.slice(1)}
          </option>
        ))}
      </select>

      <div className="model-selector-label" style={{ marginTop: '8px' }}>Model</div>
      <select 
        className="model-selector-select"
        value={config.model}
        onChange={handleModelChange}
        disabled={updating}
      >
        {config.available_models[config.provider]?.map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </select>
    </div>
  );
}
