import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { getAuthHeader } from '../../utils/tokenUtils';

interface AIDebugLog {
  id: number;
  timestamp: string;
  operation_type: string;
  user_id?: number;
  agent_id?: number;
  contest_id?: number;
  model_id?: string;
  strategy_input?: string;
  llm_prompt?: string;
  llm_response?: string;
  parsed_output?: string;
  execution_time_ms?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  cost_usd?: number;
}

interface APIResponse {
  enabled: boolean;
  count: number;
  logs: AIDebugLog[];
}

const AdminAIDebugLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AIDebugLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEnabled, setIsEnabled] = useState(false);
  const [filter, setFilter] = useState<string>('');
  const [expandedLogs, setExpandedLogs] = useState<Set<number>>(new Set());

  const fetchLogs = async () => {
    try {
      // Temporarily call backend directly to test
      const url = `http://localhost:8000/admin/ai-debug-logs/api${filter ? `?operation_type=${filter}` : ''}`;
      console.log('🔍 Fetching from:', url);
      
      const authHeader = getAuthHeader();
      const headers: Record<string, string> = {};
      if (authHeader) {
        headers['Authorization'] = authHeader;
      }
      
      const response = await fetch(url, {
        credentials: 'include', // Include cookies for authentication
        headers
      });
      
      console.log('📡 Response status:', response.status);
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Error response:', errorText);
        throw new Error(`Failed to fetch logs: ${response.status} ${errorText}`);
      }
      
      const data: APIResponse = await response.json();
      console.log('✅ Received data:', data);
      setLogs(data.logs);
      setIsEnabled(data.enabled);
    } catch (error) {
      console.error('Error fetching AI debug logs:', error);
      toast.error('Failed to load AI debug logs');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchLogs, 30000);
    return () => clearInterval(interval);
  }, [filter]);

  const toggleLogExpansion = (logId: number) => {
    const newExpanded = new Set(expandedLogs);
    if (newExpanded.has(logId)) {
      newExpanded.delete(logId);
    } else {
      newExpanded.add(logId);
    }
    setExpandedLogs(newExpanded);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatContent = (content: string | undefined, maxLength: number = 200) => {
    if (!content) return 'No content logged';
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto py-8 px-4">
        <div className="text-center">Loading AI debug logs...</div>
      </div>
    );
  }

  if (!isEnabled) {
    return (
      <div className="max-w-7xl mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-8">AI Debug Logs</h1>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-2 text-yellow-800">Debug Logging Disabled</h2>
          <p className="text-yellow-700">
            Debug logging is only available in development mode (DEBUG=True).
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">AI Debug Logs</h1>
        <button
          onClick={fetchLogs}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          🔄 Refresh
        </button>
      </div>

      <div className="mb-6 text-center text-sm text-gray-600">
        🔄 Auto-refreshing every 30 seconds | Showing last 50 operations
      </div>

      {/* Filters */}
      <div className="mb-6 flex gap-4">
        <button
          onClick={() => setFilter('')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            filter === '' 
              ? 'bg-green-600 text-white' 
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          All Operations
        </button>
        <button
          onClick={() => setFilter('writer')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            filter === 'writer' 
              ? 'bg-green-600 text-white' 
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          Writer Only
        </button>
        <button
          onClick={() => setFilter('judge')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            filter === 'judge' 
              ? 'bg-green-600 text-white' 
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          Judge Only
        </button>
      </div>

      {/* Logs */}
      {logs.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <h3 className="text-xl font-semibold mb-2">No AI operations logged yet</h3>
          <p className="text-gray-600">AI operations will appear here when they are executed in development mode.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {logs.map((log) => (
            <div
              key={log.id}
              className={`border rounded-lg overflow-hidden ${
                log.operation_type === 'writer' 
                  ? 'border-l-4 border-l-green-500' 
                  : 'border-l-4 border-l-blue-500'
              }`}
            >
              {/* Header */}
              <div
                className="bg-gray-50 p-4 cursor-pointer hover:bg-gray-100 transition-colors"
                onClick={() => toggleLogExpansion(log.id)}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold">
                      {formatTimestamp(log.timestamp)} | {log.operation_type.toUpperCase()}
                    </div>
                    <div className="text-sm text-gray-600">
                      User: {log.user_id || 'N/A'} | Agent: {log.agent_id || 'N/A'}
                      {log.contest_id && ` | Contest: ${log.contest_id}`}
                    </div>
                  </div>
                  <div className="text-right text-sm">
                    <div className="text-gray-600">⏱️ {log.execution_time_ms}ms</div>
                    <div className="text-gray-600">
                      📝 {(log.prompt_tokens || 0) + (log.completion_tokens || 0)} tokens
                    </div>
                    <div className="text-gray-600">💰 ${(log.cost_usd || 0).toFixed(4)}</div>
                    <div className="text-gray-600">🤖 {log.model_id || 'Unknown'}</div>
                  </div>
                </div>
              </div>

              {/* Expanded Content */}
              {expandedLogs.has(log.id) && (
                <div className="p-4 space-y-4">
                  {/* Strategy Input */}
                  <div>
                    <h4 className="font-semibold mb-2">📥 Strategy Input</h4>
                    <div className="bg-gray-100 p-3 rounded font-mono text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
                      {log.strategy_input || 'No input logged'}
                    </div>
                  </div>

                  {/* LLM Prompt */}
                  <div>
                    <h4 className="font-semibold mb-2">🚀 LLM Prompt</h4>
                    <div className="bg-gray-100 p-3 rounded font-mono text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
                      {log.llm_prompt || 'No prompt logged'}
                    </div>
                  </div>

                  {/* LLM Response */}
                  <div>
                    <h4 className="font-semibold mb-2">🤖 LLM Response</h4>
                    <div className="bg-gray-100 p-3 rounded font-mono text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
                      {log.llm_response || 'No response logged'}
                    </div>
                  </div>

                  {/* Parsed Output */}
                  <div>
                    <h4 className="font-semibold mb-2">📤 Parsed Output</h4>
                    <div className="bg-gray-100 p-3 rounded font-mono text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
                      {log.parsed_output || 'No output logged'}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminAIDebugLogsPage; 