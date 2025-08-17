import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select';
import { Badge } from '../ui/Badge';
import { Textarea } from '../ui/Textarea';
import { 
  Play, 
  Square, 
  Mic, 
  MicOff, 
  Video, 
  VideoOff, 
  Clock, 
  ArrowRight,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { interviewAPI } from '../../services/interviewAPI';

const MockInterview = () => {
  // Setup state
  const [setupData, setSetupData] = useState({
    job_role: '',
    company: '',
    question_count: 5,
    categories: ['behavioral', 'technical']
  });

  // Interview session state
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [response, setResponse] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingMode, setRecordingMode] = useState('audio'); // 'audio' or 'video'
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [sessionComplete, setSessionComplete] = useState(false);

  // UI state
  const [currentStep, setCurrentStep] = useState('setup'); // 'setup', 'interview', 'complete'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Recording refs
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const videoRef = useRef(null);
  const timerRef = useRef(null);

  const categories = [
    { value: 'behavioral', label: 'Behavioral' },
    { value: 'technical', label: 'Technical' },
    { value: 'company', label: 'Company-specific' },
    { value: 'general', label: 'General' }
  ];

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      stopRecording();
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const handleSetupChange = (field, value) => {
    setSetupData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCategoryToggle = (category) => {
    setSetupData(prev => ({
      ...prev,
      categories: prev.categories.includes(category)
        ? prev.categories.filter(c => c !== category)
        : [...prev.categories, category]
    }));
  };

  const startInterview = async () => {
    if (!setupData.job_role.trim()) {
      setError('Job role is required');
      return;
    }

    if (setupData.categories.length === 0) {
      setError('Please select at least one question category');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await interviewAPI.startMockInterview({
        job_role: setupData.job_role,
        company: setupData.company,
        question_count: setupData.question_count,
        categories: setupData.categories
      });

      if (response.success) {
        setSessionId(response.data.session_id);
        setCurrentQuestion(response.data.current_question);
        setProgress({
          current: 1,
          total: response.data.total_questions
        });
        setCurrentStep('interview');
        startTimer();
      } else {
        setError('Failed to start interview');
      }
    } catch (err) {
      setError('Failed to start interview. Please try again.');
      console.error('Error starting interview:', err);
    } finally {
      setLoading(false);
    }
  };

  const startTimer = () => {
    setTimeElapsed(0);
    timerRef.current = setInterval(() => {
      setTimeElapsed(prev => prev + 1);
    }, 1000);
  };

  const stopTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const startRecording = async () => {
    try {
      const constraints = recordingMode === 'video' 
        ? { video: true, audio: true }
        : { audio: true };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (recordingMode === 'video' && videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      const chunks = [];
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { 
          type: recordingMode === 'video' ? 'video/webm' : 'audio/webm' 
        });
        // Here you could upload the blob to your server
        console.log('Recording completed:', blob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Failed to start recording. Please check your camera/microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  const submitResponse = async () => {
    if (!response.trim() && !isRecording) {
      setError('Please provide a response or record your answer before continuing');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      stopTimer();
      
      let audioUrl = null;
      let videoUrl = null;
      let processedResponse = response;
      
      // Handle recording upload if there was a recording
      if (isRecording) {
        stopRecording();
        
        // In a real implementation, you would upload the recorded blob here
        // For now, we'll simulate this
        if (recordingMode === 'video') {
          videoUrl = `/recordings/${sessionId}_${Date.now()}.webm`;
        } else {
          audioUrl = `/recordings/${sessionId}_${Date.now()}.webm`;
        }
        
        // Enhanced speech-to-text processing if audio is available
        if (audioUrl) {
          try {
            const speechResult = await interviewAPI.processSpeechToText(audioUrl);
            if (speechResult.success && speechResult.data.transcript) {
              // If we have a transcript and no text response, use the transcript
              if (!processedResponse.trim() && speechResult.data.transcript.transcript) {
                processedResponse = speechResult.data.transcript.transcript;
              }
              
              // Add speech analysis data to submission
              if (speechResult.data.analysis) {
                submitData.speech_analysis = speechResult.data.analysis;
              }
            }
          } catch (speechError) {
            console.warn('Speech-to-text processing failed:', speechError);
            // Continue with submission even if speech processing fails
          }
        }
      }

      const submitData = {
        session_id: sessionId,
        response: processedResponse,
        response_time: timeElapsed
      };
      
      if (audioUrl) submitData.audio_url = audioUrl;
      if (videoUrl) submitData.video_url = videoUrl;

      const submitResponse = await interviewAPI.submitResponse(submitData);

      if (submitResponse.success) {
        if (submitResponse.data.session_complete) {
          setSessionComplete(true);
          setCurrentStep('complete');
        } else {
          setCurrentQuestion(submitResponse.data.next_question);
          setProgress(submitResponse.data.progress);
          setResponse('');
          startTimer();
        }
      } else {
        setError('Failed to submit response');
      }
    } catch (err) {
      setError('Failed to submit response. Please try again.');
      console.error('Error submitting response:', err);
    } finally {
      setLoading(false);
    }
  };

  const endInterview = async () => {
    if (sessionId) {
      try {
        await interviewAPI.endSession({ session_id: sessionId });
      } catch (err) {
        console.error('Error ending session:', err);
      }
    }
    
    stopTimer();
    stopRecording();
    setCurrentStep('complete');
  };

  const resetInterview = () => {
    setSessionId(null);
    setCurrentQuestion(null);
    setProgress({ current: 0, total: 0 });
    setResponse('');
    setTimeElapsed(0);
    setSessionComplete(false);
    setCurrentStep('setup');
    setError(null);
    stopTimer();
    stopRecording();
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (currentStep === 'setup') {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            Mock Interview Setup
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="job_role">Job Role *</Label>
              <Input
                id="job_role"
                placeholder="e.g., Software Engineer, Product Manager"
                value={setupData.job_role}
                onChange={(e) => handleSetupChange('job_role', e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="company">Company (Optional)</Label>
              <Input
                id="company"
                placeholder="e.g., Google, Microsoft"
                value={setupData.company}
                onChange={(e) => handleSetupChange('company', e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="question_count">Number of Questions</Label>
            <Select
              value={setupData.question_count.toString()}
              onValueChange={(value) => handleSetupChange('question_count', parseInt(value))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[3, 5, 7, 10].map(count => (
                  <SelectItem key={count} value={count.toString()}>
                    {count} questions
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Question Categories</Label>
            <div className="flex flex-wrap gap-2">
              {categories.map(category => (
                <Button
                  key={category.value}
                  variant={setupData.categories.includes(category.value) ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleCategoryToggle(category.value)}
                >
                  {category.label}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label>Recording Mode</Label>
            <div className="flex gap-2">
              <Button
                variant={recordingMode === 'audio' ? "default" : "outline"}
                size="sm"
                onClick={() => setRecordingMode('audio')}
              >
                <Mic className="h-4 w-4 mr-2" />
                Audio Only
              </Button>
              <Button
                variant={recordingMode === 'video' ? "default" : "outline"}
                size="sm"
                onClick={() => setRecordingMode('video')}
              >
                <Video className="h-4 w-4 mr-2" />
                Video + Audio
              </Button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          <Button
            onClick={startInterview}
            disabled={loading}
            className="w-full"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Starting Interview...
              </>
            ) : (
              'Start Mock Interview'
            )}
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (currentStep === 'interview') {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Play className="h-5 w-5" />
                Mock Interview in Progress
              </CardTitle>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Clock className="h-4 w-4" />
                  {formatTime(timeElapsed)}
                </div>
                <Badge variant="outline">
                  Question {progress.current} of {progress.total}
                </Badge>
              </div>
            </div>
          </CardHeader>
        </Card>

        {recordingMode === 'video' && (
          <Card>
            <CardContent className="p-4">
              <div className="relative">
                <video
                  ref={videoRef}
                  autoPlay
                  muted
                  className="w-full max-w-md mx-auto rounded-lg bg-gray-900"
                />
                {isRecording && (
                  <div className="absolute top-2 right-2 flex items-center gap-2 bg-red-600 text-white px-2 py-1 rounded text-sm">
                    <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                    Recording
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardContent className="p-6">
            {currentQuestion && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 mb-4">
                  <Badge className="bg-blue-100 text-blue-800">
                    {currentQuestion.category}
                  </Badge>
                  <Badge className="bg-gray-100 text-gray-800">
                    {currentQuestion.difficulty}
                  </Badge>
                  <div className="flex items-center gap-1 text-sm text-gray-500">
                    <Clock className="h-3 w-3" />
                    {Math.floor(currentQuestion.time_limit / 60)}m suggested
                  </div>
                </div>

                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  {currentQuestion.question}
                </h3>

                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Button
                      variant={isRecording ? "destructive" : "default"}
                      size="sm"
                      onClick={isRecording ? stopRecording : startRecording}
                    >
                      {isRecording ? (
                        <>
                          {recordingMode === 'video' ? <VideoOff className="h-4 w-4 mr-2" /> : <MicOff className="h-4 w-4 mr-2" />}
                          Stop Recording
                        </>
                      ) : (
                        <>
                          {recordingMode === 'video' ? <Video className="h-4 w-4 mr-2" /> : <Mic className="h-4 w-4 mr-2" />}
                          Start Recording
                        </>
                      )}
                    </Button>
                    
                    {isRecording && (
                      <div className="flex items-center gap-2 text-sm text-red-600">
                        <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse"></div>
                        Recording in progress...
                      </div>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="response">Your Response</Label>
                    <Textarea
                      id="response"
                      placeholder="Type your response here or use the recording feature above..."
                      value={response}
                      onChange={(e) => setResponse(e.target.value)}
                      rows={6}
                    />
                  </div>

                  {error && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-4">
                      <p className="text-red-800">{error}</p>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <Button
                      onClick={submitResponse}
                      disabled={loading}
                      className="flex-1"
                    >
                      {loading ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Submitting...
                        </>
                      ) : (
                        <>
                          Next Question
                          <ArrowRight className="h-4 w-4 ml-2" />
                        </>
                      )}
                    </Button>
                    
                    <Button
                      variant="outline"
                      onClick={endInterview}
                    >
                      End Interview
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (currentStep === 'complete') {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Interview Complete!
          </h2>
          <p className="text-gray-600 mb-6">
            {sessionComplete 
              ? `You've completed all ${progress.total} questions. Great job!`
              : 'Interview session ended. You can review your performance and get feedback.'
            }
          </p>
          
          <div className="flex gap-2 justify-center">
            <Button onClick={resetInterview}>
              Start New Interview
            </Button>
            <Button variant="outline">
              View Feedback
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return null;
};

export default MockInterview;