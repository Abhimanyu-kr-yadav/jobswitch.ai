import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Textarea } from '../ui/Textarea';
import { Alert, AlertDescription } from '../ui/Alert';
import { Badge } from '../ui/Badge';
import { skillsAnalysisAPI } from '../../services/skillsAnalysisAPI';

const ResumeSkillExtractor = ({ onSkillsExtracted }) => {
  const [resumeText, setResumeText] = useState('');
  const [extractedSkills, setExtractedSkills] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [updateProfile, setUpdateProfile] = useState(true);

  const handleExtractSkills = async () => {
    if (!resumeText.trim()) {
      setError('Please paste your resume text');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await skillsAnalysisAPI.extractSkillsFromResume({
        resume_text: resumeText,
        update_profile: updateProfile
      });

      if (response.success) {
        setExtractedSkills(response.data);
        if (onSkillsExtracted && response.data.extracted_skills) {
          onSkillsExtracted(response.data.extracted_skills);
        }
      } else {
        setError(response.error || 'Failed to extract skills');
      }
    } catch (err) {
      setError('Error extracting skills: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClearResults = () => {
    setExtractedSkills(null);
    setError(null);
  };

  const getCategoryColor = (category) => {
    switch (category?.toLowerCase()) {
      case 'technical':
        return 'bg-purple-100 text-purple-800';
      case 'soft':
        return 'bg-green-100 text-green-800';
      case 'domain':
        return 'bg-blue-100 text-blue-800';
      case 'certifications':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getProficiencyColor = (proficiency) => {
    switch (proficiency?.toLowerCase()) {
      case 'expert':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'advanced':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'beginner':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const groupSkillsByCategory = (skills) => {
    const grouped = {};
    skills.forEach(skill => {
      const category = skill.category || 'other';
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(skill);
    });
    return grouped;
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <Card>
        <CardHeader>
          <CardTitle>Extract Skills from Resume</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Resume Text
            </label>
            <Textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              placeholder="Paste your resume text here. Include your work experience, skills, education, and certifications..."
              rows={12}
              className="w-full"
            />
            <p className="text-xs text-gray-500 mt-1">
              Tip: Copy and paste your entire resume for best results. The AI will extract technical skills, soft skills, and certifications.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="updateProfile"
              checked={updateProfile}
              onChange={(e) => setUpdateProfile(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="updateProfile" className="text-sm text-gray-700">
              Update my profile with extracted skills
            </label>
          </div>

          {error && (
            <Alert className="border-red-200 bg-red-50">
              <AlertDescription className="text-red-800">
                {error}
              </AlertDescription>
            </Alert>
          )}

          <div className="flex gap-2">
            <Button
              onClick={handleExtractSkills}
              disabled={loading || !resumeText.trim()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {loading ? 'Extracting Skills...' : 'Extract Skills'}
            </Button>
            
            {extractedSkills && (
              <Button
                onClick={handleClearResults}
                variant="outline"
              >
                Clear Results
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Results Section */}
      {extractedSkills && (
        <>
          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Extraction Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {extractedSkills.total_skills_extracted || 0}
                  </div>
                  <div className="text-sm text-gray-600">Skills Extracted</div>
                </div>
                
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {extractedSkills.certifications?.length || 0}
                  </div>
                  <div className="text-sm text-gray-600">Certifications</div>
                </div>
                
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {Object.keys(groupSkillsByCategory(extractedSkills.extracted_skills || [])).length}
                  </div>
                  <div className="text-sm text-gray-600">Categories</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Extracted Skills by Category */}
          {extractedSkills.extracted_skills && extractedSkills.extracted_skills.length > 0 && (
            <div className="space-y-4">
              {Object.entries(groupSkillsByCategory(extractedSkills.extracted_skills)).map(([category, skills]) => (
                <Card key={category}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Badge className={getCategoryColor(category)}>
                        {category.charAt(0).toUpperCase() + category.slice(1)}
                      </Badge>
                      <span className="text-sm text-gray-600">
                        ({skills.length} skills)
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {skills.map((skill, index) => (
                        <div key={index} className="border rounded-lg p-3 bg-gray-50">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-semibold text-gray-900">{skill.name}</h4>
                            <Badge className={getProficiencyColor(skill.proficiency)}>
                              {skill.proficiency}
                            </Badge>
                          </div>
                          
                          <div className="text-xs text-gray-600 space-y-1">
                            {skill.subcategory && (
                              <p>Type: {skill.subcategory}</p>
                            )}
                            {skill.years_experience && (
                              <p>Experience: {skill.years_experience} years</p>
                            )}
                            <p>Source: {skill.source}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Extracted Certifications */}
          {extractedSkills.certifications && extractedSkills.certifications.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Certifications</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {extractedSkills.certifications.map((cert, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-orange-50">
                      <h4 className="font-semibold text-gray-900 mb-2">{cert.name}</h4>
                      <div className="text-sm text-gray-600 space-y-1">
                        {cert.issuer && <p>Issuer: {cert.issuer}</p>}
                        {cert.year && <p>Year: {cert.year}</p>}
                        <p>Status: {cert.status}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Extraction Metadata */}
          {extractedSkills.metadata && (
            <Card>
              <CardHeader>
                <CardTitle>Extraction Details</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-gray-600 space-y-1">
                  <p>Extraction Method: {extractedSkills.metadata.extraction_method}</p>
                  <p>Resume Length: {extractedSkills.metadata.resume_length} characters</p>
                  <p>Processing Time: {extractedSkills.metadata.processing_time}</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Next Steps */}
          <Card>
            <CardHeader>
              <CardTitle>Next Steps</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 border rounded-lg bg-blue-50">
                  <div className="text-blue-600">✓</div>
                  <div>
                    <h4 className="font-semibold text-blue-900">Skills Extracted</h4>
                    <p className="text-sm text-gray-700">
                      {extractedSkills.total_skills_extracted} skills have been identified from your resume.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 p-3 border rounded-lg">
                  <div className="text-gray-400">→</div>
                  <div>
                    <h4 className="font-semibold">Analyze Skill Gaps</h4>
                    <p className="text-sm text-gray-600">
                      Compare your skills against specific job requirements to identify gaps.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 p-3 border rounded-lg">
                  <div className="text-gray-400">→</div>
                  <div>
                    <h4 className="font-semibold">Get Learning Recommendations</h4>
                    <p className="text-sm text-gray-600">
                      Receive personalized learning paths to develop missing skills.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Sample Resume Text */}
      {!resumeText && (
        <Card>
          <CardHeader>
            <CardTitle>Sample Resume Text</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-3">
              Not sure what to paste? Here's an example of what resume text should look like:
            </p>
            <div className="bg-gray-100 p-4 rounded-lg text-sm">
              <p className="font-semibold">John Doe</p>
              <p>Senior Software Engineer</p>
              <br />
              <p><strong>Experience:</strong></p>
              <p>• 5+ years developing web applications using React, Node.js, and Python</p>
              <p>• Proficient in AWS cloud services including EC2, S3, and Lambda</p>
              <p>• Experience with Docker containerization and Kubernetes orchestration</p>
              <p>• Strong background in database design with PostgreSQL and MongoDB</p>
              <br />
              <p><strong>Certifications:</strong></p>
              <p>• AWS Certified Solutions Architect (2023)</p>
              <p>• Certified Kubernetes Administrator (2022)</p>
            </div>
            <Button
              onClick={() => setResumeText(`John Doe
Senior Software Engineer

Experience:
• 5+ years developing web applications using React, Node.js, and Python
• Proficient in AWS cloud services including EC2, S3, and Lambda
• Experience with Docker containerization and Kubernetes orchestration
• Strong background in database design with PostgreSQL and MongoDB
• Led team of 4 developers in agile development environment
• Excellent communication and problem-solving skills

Certifications:
• AWS Certified Solutions Architect (2023)
• Certified Kubernetes Administrator (2022)

Education:
• Bachelor's degree in Computer Science
• Master's degree in Software Engineering`)}
              variant="outline"
              size="sm"
              className="mt-2"
            >
              Use Sample Text
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ResumeSkillExtractor;