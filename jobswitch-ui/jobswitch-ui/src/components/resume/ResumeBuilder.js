import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { Alert, AlertDescription } from '../ui/Alert';
import { Upload, Download, Eye, Save, Wand2, BarChart3, GitBranch, Target } from 'lucide-react';
import ResumeEditor from './ResumeEditor';
import ResumePreview from './ResumePreview';
import ATSAnalysis from './ATSAnalysis';
import ResumeOptimizer from './ResumeOptimizer';
import ResumeVersionManager from './ResumeVersionManager';
import AcceptanceProbabilityCalculator from './AcceptanceProbabilityCalculator';
import { resumeAPI } from '../../services/resumeAPI';

const ResumeBuilder = () => {
  const [resumes, setResumes] = useState([]);
  const [currentResume, setCurrentResume] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('editor');
  const [atsAnalysis, setAtsAnalysis] = useState(null);
  const [showVersionManager, setShowVersionManager] = useState(false);
  const [showAcceptanceCalculator, setShowAcceptanceCalculator] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState(null);

  useEffect(() => {
    loadUserResumes();
  }, []);

  const loadUserResumes = async () => {
    try {
      setLoading(true);
      const response = await resumeAPI.getUserResumes();
      if (response.success) {
        setResumes(response.data);
        if (response.data.length > 0) {
          const primaryResume = response.data.find(r => r.is_primary) || response.data[0];
          setCurrentResume(primaryResume);
        }
      }
    } catch (err) {
      setError('Failed to load resumes');
      console.error('Error loading resumes:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleResumeUpload = async (file) => {
    try {
      setLoading(true);
      setError(null);
      
      const formData = new FormData();
      formData.append('resume_file', file);
      
      const response = await resumeAPI.parseResume(null, file);
      if (response.success) {
        await loadUserResumes();
        setCurrentResume(response.data);
      }
    } catch (err) {
      setError('Failed to upload and parse resume');
      console.error('Error uploading resume:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleResumeOptimize = async (jobId = null) => {
    if (!currentResume) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await resumeAPI.optimizeResume(currentResume.resume_id, jobId);
      if (response.success) {
        await loadUserResumes();
        // Switch to the optimized resume
        const optimizedResumeId = response.data.optimized_resume_id;
        const optimizedResume = resumes.find(r => r.resume_id === optimizedResumeId);
        if (optimizedResume) {
          setCurrentResume(optimizedResume);
        }
      }
    } catch (err) {
      setError('Failed to optimize resume');
      console.error('Error optimizing resume:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleATSAnalysis = async () => {
    if (!currentResume) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await resumeAPI.analyzeATS(currentResume.resume_id);
      if (response.success) {
        setAtsAnalysis(response.data);
        setActiveTab('analysis');
      }
    } catch (err) {
      setError('Failed to analyze ATS compatibility');
      console.error('Error analyzing ATS:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleResumeUpdate = async (updatedContent) => {
    if (!currentResume) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // Create new version with updated content
      const response = await resumeAPI.generateResume(null, null, updatedContent);
      if (response.success) {
        await loadUserResumes();
        setCurrentResume(response.data);
      }
    } catch (err) {
      setError('Failed to update resume');
      console.error('Error updating resume:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      handleResumeUpload(file);
    }
  };

  if (loading && !currentResume) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading resumes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Resume Builder</h1>
            <p className="text-gray-600">Create and optimize your resume with AI assistance</p>
          </div>
          
          <div className="flex gap-2">
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileUpload}
              className="hidden"
              id="resume-upload"
            />
            <label htmlFor="resume-upload">
              <Button variant="outline" className="cursor-pointer">
                <Upload className="w-4 h-4 mr-2" />
                Upload Resume
              </Button>
            </label>
            
            {currentResume && (
              <>
                <Button 
                  onClick={handleATSAnalysis}
                  disabled={loading}
                  variant="outline"
                >
                  <BarChart3 className="w-4 h-4 mr-2" />
                  ATS Analysis
                </Button>
                
                <Button 
                  onClick={() => setShowVersionManager(true)}
                  disabled={loading}
                  variant="outline"
                >
                  <GitBranch className="w-4 h-4 mr-2" />
                  Versions
                </Button>
                
                <Button 
                  onClick={() => setShowAcceptanceCalculator(true)}
                  disabled={loading}
                  variant="outline"
                >
                  <Target className="w-4 h-4 mr-2" />
                  Acceptance Rate
                </Button>
                
                <Button 
                  onClick={() => handleResumeOptimize()}
                  disabled={loading}
                >
                  <Wand2 className="w-4 h-4 mr-2" />
                  Optimize Resume
                </Button>
              </>
            )}
          </div>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Resume Selection */}
        {resumes.length > 0 && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Resume
            </label>
            <select
              value={currentResume?.resume_id || ''}
              onChange={(e) => {
                const selected = resumes.find(r => r.resume_id === e.target.value);
                setCurrentResume(selected);
              }}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              {resumes.map((resume) => (
                <option key={resume.resume_id} value={resume.resume_id}>
                  {resume.title} {resume.is_primary && '(Primary)'} - v{resume.version}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {currentResume ? (
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="editor">Editor</TabsTrigger>
            <TabsTrigger value="preview">Preview</TabsTrigger>
            <TabsTrigger value="analysis">ATS Analysis</TabsTrigger>
            <TabsTrigger value="optimizer">Optimizer</TabsTrigger>
            <TabsTrigger value="versions">Versions</TabsTrigger>
            <TabsTrigger value="probability">Acceptance</TabsTrigger>
          </TabsList>

          <TabsContent value="editor" className="mt-6">
            <ResumeEditor
              resume={currentResume}
              onUpdate={handleResumeUpdate}
              loading={loading}
            />
          </TabsContent>

          <TabsContent value="preview" className="mt-6">
            <ResumePreview
              resume={currentResume}
              onDownload={() => {/* Implement download */}}
            />
          </TabsContent>

          <TabsContent value="analysis" className="mt-6">
            <ATSAnalysis
              resume={currentResume}
              analysis={atsAnalysis}
              onAnalyze={handleATSAnalysis}
              loading={loading}
            />
          </TabsContent>

          <TabsContent value="optimizer" className="mt-6">
            <ResumeOptimizer
              resume={currentResume}
              onOptimize={handleResumeOptimize}
              loading={loading}
            />
          </TabsContent>

          <TabsContent value="versions" className="mt-6">
            <ResumeVersionManager
              resumeId={currentResume?.resume_id}
              onVersionSelect={(version) => {
                setCurrentResume(version);
                setActiveTab('editor');
              }}
              onClose={() => setActiveTab('editor')}
            />
          </TabsContent>

          <TabsContent value="probability" className="mt-6">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Job for Probability Analysis
              </label>
              <input
                type="text"
                placeholder="Enter Job ID or select from saved jobs"
                value={selectedJobId || ''}
                onChange={(e) => setSelectedJobId(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            {selectedJobId && currentResume ? (
              <AcceptanceProbabilityCalculator
                resumeId={currentResume.resume_id}
                jobId={selectedJobId}
                onClose={() => setActiveTab('editor')}
              />
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <Target className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Job</h3>
                  <p className="text-gray-600">
                    Enter a job ID to calculate acceptance probability for your resume
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      ) : (
        <Card>
          <CardContent className="text-center py-12">
            <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Resume Found</h3>
            <p className="text-gray-600 mb-4">
              Upload your existing resume or create a new one to get started
            </p>
            <div className="flex justify-center gap-4">
              <label htmlFor="resume-upload-empty">
                <Button className="cursor-pointer">
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Resume
                </Button>
              </label>
              <Button variant="outline" onClick={() => {/* Implement create new */}}>
                Create New Resume
              </Button>
            </div>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileUpload}
              className="hidden"
              id="resume-upload-empty"
            />
          </CardContent>
        </Card>
      )}

      {/* Version Manager Modal */}
      {showVersionManager && currentResume && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto m-4">
            <ResumeVersionManager
              resumeId={currentResume.resume_id}
              onVersionSelect={(version) => {
                setCurrentResume(version);
                setShowVersionManager(false);
              }}
              onClose={() => setShowVersionManager(false)}
            />
          </div>
        </div>
      )}

      {/* Acceptance Probability Calculator Modal */}
      {showAcceptanceCalculator && currentResume && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto m-4">
            <div className="p-4">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Enter Job ID for Analysis
                </label>
                <input
                  type="text"
                  placeholder="Job ID"
                  value={selectedJobId || ''}
                  onChange={(e) => setSelectedJobId(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              {selectedJobId ? (
                <AcceptanceProbabilityCalculator
                  resumeId={currentResume.resume_id}
                  jobId={selectedJobId}
                  onClose={() => setShowAcceptanceCalculator(false)}
                />
              ) : (
                <div className="text-center py-8">
                  <Target className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">Enter a job ID to calculate acceptance probability</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResumeBuilder;