import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Select } from '../ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import CodeEditor from './CodeEditor';
import TestResults from './TestResults';
import { technicalInterviewAPI } from '../../services/technicalInterviewAPI';

const CodingChallenge = ({ challenge, sessionId, onComplete }) => {
  const [selectedLanguage, setSelectedLanguage] = useState('python');
  const [code, setCode] = useState('');
  const [testResults, setTestResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hints, setHints] = useState([]);
  const [currentHintLevel, setCurrentHintLevel] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(challenge?.time_limit || 1800);

  const supportedLanguages = [
    { value: 'python', label: 'Python' },
    { value: 'javascript', label: 'JavaScript' },
    { value: 'java', label: 'Java' }
  ];

  useEffect(() => {
    if (challenge) {
      // Set initial code from starter code
      const starterCode = challenge.starter_code?.[selectedLanguage] || '';
      setCode(starterCode);
      
      // Reset state for new challenge
      setTestResults(null);
      setHints([]);
      setCurrentHintLevel(0);
      setTimeRemaining(challenge.time_limit || 1800);
    }
  }, [challenge, selectedLanguage]);

  useEffect(() => {
    // Timer countdown
    if (timeRemaining > 0) {
      const timer = setTimeout(() => {
        setTimeRemaining(prev => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [timeRemaining]);

  const handleLanguageChange = (language) => {
    setSelectedLanguage(language);
    const starterCode = challenge.starter_code?.[language] || '';
    setCode(starterCode);
    setTestResults(null);
  };

  const handleRunTests = async () => {
    setLoading(true);
    try {
      const response = await technicalInterviewAPI.executeCode({
        challenge_id: challenge.id,
        language: selectedLanguage,
        code: code
      });

      if (response.success) {
        setTestResults(response.data.execution_result);
      } else {
        setTestResults({
          success: false,
          error_message: response.error || 'Execution failed'
        });
      }
    } catch (error) {
      console.error('Test execution error:', error);
      setTestResults({
        success: false,
        error_message: 'Failed to execute code'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitSolution = async () => {
    setLoading(true);
    try {
      const response = await technicalInterviewAPI.submitCode({
        session_id: sessionId,
        challenge_id: challenge.id,
        language: selectedLanguage,
        code: code
      });

      if (response.success) {
        onComplete(response.data);
      } else {
        setTestResults({
          success: false,
          error_message: response.error || 'Submission failed'
        });
      }
    } catch (error) {
      console.error('Submission error:', error);
      setTestResults({
        success: false,
        error_message: 'Failed to submit solution'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleGetHint = async () => {
    try {
      const response = await technicalInterviewAPI.getHint(sessionId, currentHintLevel + 1);
      if (response.success) {
        setHints(prev => [...prev, response.data.hint]);
        setCurrentHintLevel(response.data.hint_level);
      }
    } catch (error) {
      console.error('Failed to get hint:', error);
    }
  };

  const handleSkipChallenge = async () => {
    try {
      const response = await technicalInterviewAPI.skipChallenge(sessionId);
      if (response.success) {
        onComplete(response.data);
      }
    } catch (error) {
      console.error('Failed to skip challenge:', error);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'easy': return 'text-green-600 bg-green-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'hard': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  if (!challenge) {
    return <div>Loading challenge...</div>;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Problem Description */}
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-xl">{challenge.title}</CardTitle>
                <div className="flex items-center space-x-2 mt-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(challenge.difficulty)}`}>
                    {challenge.difficulty.charAt(0).toUpperCase() + challenge.difficulty.slice(1)}
                  </span>
                  <span className="text-sm text-gray-500">
                    {challenge.category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-lg font-mono ${timeRemaining < 300 ? 'text-red-600' : 'text-gray-700'}`}>
                  {formatTime(timeRemaining)}
                </div>
                <div className="text-xs text-gray-500">Time Remaining</div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none">
              <div className="whitespace-pre-wrap">{challenge.description}</div>
            </div>

            {challenge.tags && challenge.tags.length > 0 && (
              <div className="mt-4">
                <div className="text-sm font-medium mb-2">Tags:</div>
                <div className="flex flex-wrap gap-1">
                  {challenge.tags.map(tag => (
                    <span key={tag} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {challenge.companies && challenge.companies.length > 0 && (
              <div className="mt-4">
                <div className="text-sm font-medium mb-2">Asked by:</div>
                <div className="flex flex-wrap gap-1">
                  {challenge.companies.slice(0, 5).map(company => (
                    <span key={company} className="px-2 py-1 bg-gray-50 text-gray-700 text-xs rounded">
                      {company}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Test Cases */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Test Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {challenge.test_cases?.slice(0, 3).map((testCase, index) => (
                <div key={index} className="p-3 bg-gray-50 rounded-md">
                  <div className="text-sm font-medium mb-1">Example {index + 1}:</div>
                  <div className="text-sm">
                    <div><strong>Input:</strong> {JSON.stringify(testCase.input)}</div>
                    <div><strong>Output:</strong> {JSON.stringify(testCase.expected_output)}</div>
                    {testCase.explanation && (
                      <div className="mt-1 text-gray-600">
                        <strong>Explanation:</strong> {testCase.explanation}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Hints */}
        {hints.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Hints</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {hints.map((hint, index) => (
                  <div key={index} className="p-3 bg-blue-50 border-l-4 border-blue-400">
                    <div className="text-sm font-medium">Hint {index + 1}:</div>
                    <div className="text-sm text-blue-800">{hint}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Code Editor and Results */}
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-lg">Solution</CardTitle>
              <div className="flex items-center space-x-2">
                <Select
                  value={selectedLanguage}
                  onValueChange={handleLanguageChange}
                >
                  {supportedLanguages.map(lang => (
                    <option key={lang.value} value={lang.value}>
                      {lang.label}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <CodeEditor
              language={selectedLanguage}
              value={code}
              onChange={setCode}
              height="400px"
            />

            <div className="flex justify-between items-center mt-4">
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  onClick={handleRunTests}
                  disabled={loading}
                >
                  {loading ? 'Running...' : 'Run Tests'}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleGetHint}
                  disabled={currentHintLevel >= (challenge.hints?.length || 0)}
                >
                  Get Hint
                </Button>
                <Button
                  variant="outline"
                  onClick={handleSkipChallenge}
                >
                  Skip Challenge
                </Button>
              </div>
              <Button
                onClick={handleSubmitSolution}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700"
              >
                {loading ? 'Submitting...' : 'Submit Solution'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Test Results */}
        {testResults && (
          <TestResults results={testResults} />
        )}
      </div>
    </div>
  );
};

export default CodingChallenge;