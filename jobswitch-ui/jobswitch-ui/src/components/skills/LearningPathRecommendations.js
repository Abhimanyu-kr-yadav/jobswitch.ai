import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Input } from '../ui/Input';
import { Alert, AlertDescription } from '../ui/Alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { skillsAnalysisAPI } from '../../services/skillsAnalysisAPI';

const LearningPathRecommendations = ({ userSkills, skillsAnalysis }) => {
  const [learningPaths, setLearningPaths] = useState(null);
  const [targetSkills, setTargetSkills] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);


  const handleGeneratePaths = async () => {
    if (!targetSkills.trim() && !targetRole.trim()) {
      setError('Please specify either target skills or a target role');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const requestData = {
        target_skills: targetSkills ? targetSkills.split(',').map(s => s.trim()) : null,
        target_role: targetRole || null
      };

      const response = await skillsAnalysisAPI.recommendLearningPaths(requestData);

      if (response.success) {
        setLearningPaths(response.data);
      } else {
        setError(response.error || 'Failed to generate learning paths');
      }
    } catch (err) {
      setError('Error generating learning paths: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case 'beginner':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'advanced':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getResourceTypeIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'course':
        return '🎓';
      case 'book':
        return '📚';
      case 'video':
        return '🎥';
      case 'tutorial':
        return '📝';
      case 'practice':
        return '💻';
      default:
        return '📄';
    }
  };

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle>Generate Learning Paths</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Target Skills (comma-separated)
            </label>
            <Input
              value={targetSkills}
              onChange={(e) => setTargetSkills(e.target.value)}
              placeholder="e.g., React, Node.js, Docker, Kubernetes"
            />
          </div>

          <div className="text-center text-gray-500">OR</div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Target Role
            </label>
            <Input
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder="e.g., Full Stack Developer, Data Scientist"
            />
          </div>

          {error && (
            <Alert className="border-red-200 bg-red-50">
              <AlertDescription className="text-red-800">
                {error}
              </AlertDescription>
            </Alert>
          )}

          <Button
            onClick={handleGeneratePaths}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            {loading ? 'Generating Paths...' : 'Generate Learning Paths'}
          </Button>
        </CardContent>
      </Card>

      {/* Learning Paths Results */}
      {learningPaths && (
        <>
          {/* Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Learning Path Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {learningPaths.learning_paths?.length || 0}
                  </div>
                  <div className="text-sm text-gray-600">Learning Paths</div>
                </div>
                
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {learningPaths.overall_timeline || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Estimated Timeline</div>
                </div>
                
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    ${learningPaths.budget_estimate?.total_estimated || 0}
                  </div>
                  <div className="text-sm text-gray-600">Estimated Budget</div>
                </div>
              </div>

              {learningPaths.priority_order && (
                <div className="mt-4">
                  <h4 className="font-semibold mb-2">Recommended Priority Order:</h4>
                  <div className="flex flex-wrap gap-2">
                    {learningPaths.priority_order.map((skill, index) => (
                      <Badge key={index} className="bg-blue-100 text-blue-800">
                        {index + 1}. {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Budget Breakdown */}
          {learningPaths.budget_estimate && (
            <Card>
              <CardHeader>
                <CardTitle>Budget Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>Free Resources</span>
                    <span className="font-semibold text-green-600">
                      {learningPaths.budget_estimate.free_resources}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Paid Courses</span>
                    <span className="font-semibold">
                      ${learningPaths.budget_estimate.paid_courses}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Certifications</span>
                    <span className="font-semibold">
                      ${learningPaths.budget_estimate.certifications}
                    </span>
                  </div>
                  <hr />
                  <div className="flex justify-between items-center font-bold">
                    <span>Total Estimated</span>
                    <span>${learningPaths.budget_estimate.total_estimated}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Learning Paths */}
          <div className="space-y-6">
            {learningPaths.learning_paths?.map((path, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{path.skill}</span>
                    <div className="flex gap-2">
                      <Badge className={getDifficultyColor(path.target_level)}>
                        {path.target_level}
                      </Badge>
                      <Badge className="bg-gray-100 text-gray-800">
                        {path.estimated_duration}
                      </Badge>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="overview" className="w-full">
                    <TabsList className="grid w-full grid-cols-4">
                      <TabsTrigger value="overview">Overview</TabsTrigger>
                      <TabsTrigger value="steps">Learning Steps</TabsTrigger>
                      <TabsTrigger value="projects">Projects</TabsTrigger>
                      <TabsTrigger value="certifications">Certifications</TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-semibold mb-2">Current Level</h4>
                          <Badge className={getDifficultyColor(path.current_level)}>
                            {path.current_level}
                          </Badge>
                        </div>
                        <div>
                          <h4 className="font-semibold mb-2">Target Level</h4>
                          <Badge className={getDifficultyColor(path.target_level)}>
                            {path.target_level}
                          </Badge>
                        </div>
                      </div>

                      {path.prerequisites && path.prerequisites.length > 0 && (
                        <div>
                          <h4 className="font-semibold mb-2">Prerequisites</h4>
                          <div className="flex flex-wrap gap-2">
                            {path.prerequisites.map((prereq, idx) => (
                              <Badge key={idx} className="bg-orange-100 text-orange-800">
                                {prereq}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="steps" className="space-y-4">
                      {path.learning_steps?.map((step, stepIndex) => (
                        <div key={stepIndex} className="border rounded-lg p-4">
                          <div className="flex items-center gap-3 mb-3">
                            <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold">
                              {step.step}
                            </div>
                            <div>
                              <h4 className="font-semibold">{step.title}</h4>
                              <p className="text-sm text-gray-600">{step.duration}</p>
                            </div>
                          </div>

                          {step.resources && step.resources.length > 0 && (
                            <div>
                              <h5 className="font-medium mb-2">Resources:</h5>
                              <div className="space-y-2">
                                {step.resources.map((resource, resIndex) => (
                                  <div key={resIndex} className="flex items-center gap-2 text-sm">
                                    <span>{getResourceTypeIcon(resource.type)}</span>
                                    <span className="font-medium">{resource.name}</span>
                                    {resource.provider && (
                                      <span className="text-gray-600">by {resource.provider}</span>
                                    )}
                                    {resource.author && (
                                      <span className="text-gray-600">by {resource.author}</span>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </TabsContent>

                    <TabsContent value="projects" className="space-y-4">
                      {path.projects?.map((project, projIndex) => (
                        <div key={projIndex} className="border rounded-lg p-4">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-semibold">{project.name}</h4>
                            <div className="flex gap-2">
                              <Badge className={getDifficultyColor(project.difficulty)}>
                                {project.difficulty}
                              </Badge>
                              <Badge className="bg-gray-100 text-gray-800">
                                {project.estimated_time}
                              </Badge>
                            </div>
                          </div>
                          {project.description && (
                            <p className="text-sm text-gray-600">{project.description}</p>
                          )}
                        </div>
                      ))}
                    </TabsContent>

                    <TabsContent value="certifications" className="space-y-4">
                      {path.certifications?.map((cert, certIndex) => (
                        <div key={certIndex} className="border rounded-lg p-4">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-semibold">{cert.name}</h4>
                            <Badge className={getDifficultyColor(cert.difficulty)}>
                              {cert.difficulty}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600">Provider: {cert.provider}</p>
                          {cert.cost && (
                            <p className="text-sm text-gray-600">Cost: ${cert.cost}</p>
                          )}
                        </div>
                      ))}
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* Quick Start Recommendations */}
      {skillsAnalysis?.improvement_areas && (
        <Card>
          <CardHeader>
            <CardTitle>Quick Start Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">
              Based on your current skills analysis, here are some immediate areas to focus on:
            </p>
            <div className="space-y-3">
              {skillsAnalysis.improvement_areas.slice(0, 3).map((area, index) => (
                <div key={index} className="border rounded-lg p-3 bg-blue-50">
                  <h4 className="font-semibold text-blue-900">{area.category}</h4>
                  <p className="text-sm text-gray-700">{area.reason}</p>
                  <Button
                    size="sm"
                    className="mt-2"
                    onClick={() => {
                      setTargetSkills(area.category);
                      setTargetRole('');
                    }}
                  >
                    Generate Path for {area.category}
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default LearningPathRecommendations;