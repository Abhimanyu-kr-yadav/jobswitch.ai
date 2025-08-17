import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Alert, AlertDescription } from '../ui/Alert';
import { 
  Wand2, 
  Target, 
  TrendingUp, 
  CheckCircle,
  ArrowRight,
  Lightbulb,
  FileText,
  Zap
} from 'lucide-react';

const ResumeOptimizer = ({ resume, onOptimize, loading }) => {
  const [selectedJob, setSelectedJob] = useState(null);
  const [optimizationType, setOptimizationType] = useState('ats');
  const [savedJobs, setSavedJobs] = useState([]);
  const [optimizationHistory, setOptimizationHistory] = useState([]);

  useEffect(() => {
    // Load saved jobs and optimization history
    loadSavedJobs();
    loadOptimizationHistory();
  }, [resume]);

  const loadSavedJobs = async () => {
    // This would fetch saved jobs from the API
    // For now, using mock data
    setSavedJobs([
      { job_id: '1', title: 'Senior Software Engineer', company: 'TechCorp' },
      { job_id: '2', title: 'Full Stack Developer', company: 'StartupXYZ' },
      { job_id: '3', title: 'Frontend Developer', company: 'WebCo' }
    ]);
  };

  const loadOptimizationHistory = async () => {
    // This would fetch optimization history from the API
    // For now, using mock data
    if (resume?.optimizations) {
      setOptimizationHistory(resume.optimizations);
    }
  };

  const handleOptimize = async () => {
    await onOptimize(selectedJob);
  };

  const optimizationTypes = [
    {
      id: 'ats',
      name: 'ATS Optimization',
      description: 'Optimize for Applicant Tracking Systems',
      icon: <Target className="w-5 h-5" />,
      features: [
        'Keyword optimization',
        'Format standardization',
        'Section organization',
        'ATS-friendly formatting'
      ]
    },
    {
      id: 'job_specific',
      name: 'Job-Specific Optimization',
      description: 'Tailor resume for specific job posting',
      icon: <Zap className="w-5 h-5" />,
      features: [
        'Job requirement matching',
        'Skill highlighting',
        'Experience prioritization',
        'Custom keyword integration'
      ]
    },
    {
      id: 'keyword',
      name: 'Keyword Enhancement',
      description: 'Boost keyword density and relevance',
      icon: <TrendingUp className="w-5 h-5" />,
      features: [
        'Industry keyword analysis',
        'Skill keyword optimization',
        'Action verb enhancement',
        'Technical term integration'
      ]
    }
  ];

  return (
    <div className="space-y-6">
      {/* Optimization Type Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wand2 className="w-5 h-5" />
            Choose Optimization Type
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {optimizationTypes.map((type) => (
              <div
                key={type.id}
                className={`border rounded-lg p-4 cursor-pointer transition-all ${
                  optimizationType === type.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setOptimizationType(type.id)}
              >
                <div className="flex items-center gap-2 mb-2">
                  {type.icon}
                  <h3 className="font-medium text-gray-900">{type.name}</h3>
                </div>
                <p className="text-sm text-gray-600 mb-3">{type.description}</p>
                <ul className="space-y-1">
                  {type.features.map((feature, index) => (
                    <li key={index} className="flex items-center gap-2 text-xs text-gray-500">
                      <CheckCircle className="w-3 h-3 text-green-500" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Job Selection for Job-Specific Optimization */}
      {optimizationType === 'job_specific' && (
        <Card>
          <CardHeader>
            <CardTitle>Select Target Job</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Choose a job posting to optimize for
                </label>
                <select
                  value={selectedJob || ''}
                  onChange={(e) => setSelectedJob(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a job posting...</option>
                  {savedJobs.map((job) => (
                    <option key={job.job_id} value={job.job_id}>
                      {job.title} at {job.company}
                    </option>
                  ))}
                </select>
              </div>
              
              {!selectedJob && (
                <Alert>
                  <Lightbulb className="w-4 h-4" />
                  <AlertDescription>
                    Select a specific job posting to get targeted optimization recommendations.
                    The AI will analyze the job requirements and tailor your resume accordingly.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Optimization Action */}
      <Card>
        <CardHeader>
          <CardTitle>Start Optimization</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <h3 className="font-medium text-gray-900">Current Resume</h3>
                <p className="text-sm text-gray-600">{resume?.title}</p>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="outline">Version {resume?.version}</Badge>
                  {resume?.ats_score && (
                    <Badge variant={resume.ats_score >= 0.8 ? "success" : "warning"}>
                      ATS Score: {Math.round(resume.ats_score * 100)}%
                    </Badge>
                  )}
                </div>
              </div>
              <ArrowRight className="w-6 h-6 text-gray-400" />
              <div>
                <h3 className="font-medium text-gray-900">Optimized Resume</h3>
                <p className="text-sm text-gray-600">AI-enhanced version</p>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="outline">Version {(resume?.version || 0) + 1}</Badge>
                  <Badge variant="success">Improved ATS Score</Badge>
                </div>
              </div>
            </div>

            <Button
              onClick={handleOptimize}
              disabled={loading || (optimizationType === 'job_specific' && !selectedJob)}
              className="w-full"
              size="lg"
            >
              <Wand2 className="w-4 h-4 mr-2" />
              {loading ? 'Optimizing Resume...' : 'Optimize Resume'}
            </Button>

            <div className="text-center text-sm text-gray-600">
              <p>
                The AI will analyze your resume and create an optimized version with:
              </p>
              <ul className="mt-2 space-y-1">
                <li>• Enhanced keyword density</li>
                <li>• Improved ATS compatibility</li>
                <li>• Better content organization</li>
                <li>• Targeted skill highlighting</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Optimization History */}
      {optimizationHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Optimization History
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {optimizationHistory.map((optimization, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <h4 className="font-medium text-gray-900">
                        {optimization.optimization_type.replace('_', ' ').toUpperCase()} Optimization
                      </h4>
                      <p className="text-sm text-gray-600">
                        {new Date(optimization.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    {optimization.score_improvement && (
                      <Badge variant="success">
                        +{Math.round(optimization.score_improvement * 100)}% improvement
                      </Badge>
                    )}
                  </div>
                  
                  {optimization.job_id && (
                    <div className="mb-2">
                      <Badge variant="outline">
                        Optimized for specific job
                      </Badge>
                    </div>
                  )}
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      // Navigate to optimized resume
                      window.location.href = `/resume/${optimization.optimized_resume_id}`;
                    }}
                  >
                    View Optimized Resume
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tips and Best Practices */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5" />
            Optimization Tips
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">ATS Best Practices</h4>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Use standard section headings</li>
                <li>• Include relevant keywords naturally</li>
                <li>• Avoid complex formatting</li>
                <li>• Use common file formats (PDF, DOCX)</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Content Optimization</h4>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Quantify achievements with numbers</li>
                <li>• Use strong action verbs</li>
                <li>• Match job description language</li>
                <li>• Highlight relevant skills prominently</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ResumeOptimizer;