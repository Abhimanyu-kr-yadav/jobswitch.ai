import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';

const TestResults = ({ results }) => {
  if (!results) return null;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'accepted':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'wrong_answer':
      case 'compilation_error':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'partial_correct':
        return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      default:
        return <Clock className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'accepted':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'wrong_answer':
      case 'compilation_error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'partial_correct':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const formatStatus = (status) => {
    return status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Test Results</CardTitle>
          <div className="flex items-center space-x-2">
            {getStatusIcon(results.overall_status)}
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(results.overall_status)}`}>
              {formatStatus(results.overall_status)}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall Summary */}
        <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {results.passed_tests}
            </div>
            <div className="text-sm text-gray-600">Passed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {results.total_tests - results.passed_tests}
            </div>
            <div className="text-sm text-gray-600">Failed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {results.execution_time}ms
            </div>
            <div className="text-sm text-gray-600">Runtime</div>
          </div>
        </div>

        {/* Error Message */}
        {results.error_message && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <XCircle className="w-5 h-5 text-red-600" />
              <span className="font-medium text-red-800">Execution Error</span>
            </div>
            <pre className="text-sm text-red-700 whitespace-pre-wrap font-mono">
              {results.error_message}
            </pre>
          </div>
        )}

        {/* Individual Test Results */}
        {results.test_results && results.test_results.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Test Case Results</h4>
            {results.test_results.map((testResult, index) => (
              <div
                key={index}
                className={`p-4 border rounded-lg ${
                  testResult.passed 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {testResult.passed ? (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-600" />
                    )}
                    <span className="font-medium">
                      Test Case {testResult.test_case_index + 1}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    {testResult.execution_time}ms
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium">Input:</span>
                    <pre className="mt-1 p-2 bg-white border rounded font-mono text-xs">
                      {JSON.stringify(testResult.input, null, 2)}
                    </pre>
                  </div>

                  <div>
                    <span className="font-medium">Expected:</span>
                    <pre className="mt-1 p-2 bg-white border rounded font-mono text-xs">
                      {JSON.stringify(testResult.expected_output, null, 2)}
                    </pre>
                  </div>

                  {testResult.actual_output !== undefined && (
                    <div>
                      <span className="font-medium">Your Output:</span>
                      <pre className={`mt-1 p-2 border rounded font-mono text-xs ${
                        testResult.passed ? 'bg-white' : 'bg-red-50'
                      }`}>
                        {JSON.stringify(testResult.actual_output, null, 2)}
                      </pre>
                    </div>
                  )}

                  {testResult.error_message && (
                    <div>
                      <span className="font-medium text-red-600">Error:</span>
                      <pre className="mt-1 p-2 bg-red-50 border border-red-200 rounded font-mono text-xs text-red-700">
                        {testResult.error_message}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* AI Feedback */}
        {results.ai_feedback && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">AI</span>
              </div>
              <span className="font-medium text-blue-800">AI Feedback</span>
            </div>
            <div className="text-sm text-blue-700 whitespace-pre-wrap">
              {results.ai_feedback}
            </div>
          </div>
        )}

        {/* Performance Metrics */}
        {results.execution_time > 0 && (
          <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <div className="text-sm text-gray-600">Execution Time</div>
              <div className="text-lg font-semibold">
                {results.execution_time}ms
              </div>
              <div className="text-xs text-gray-500">
                {results.execution_time < 1000 ? 'Excellent' : 
                 results.execution_time < 3000 ? 'Good' : 'Could be optimized'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Memory Usage</div>
              <div className="text-lg font-semibold">
                {results.memory_used > 0 ? `${Math.round(results.memory_used / 1024)}KB` : 'N/A'}
              </div>
              <div className="text-xs text-gray-500">
                {results.memory_used > 0 && results.memory_used < 10240 ? 'Efficient' : 'Standard'}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TestResults;