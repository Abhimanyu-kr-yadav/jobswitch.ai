import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';
import { 
  GripVertical, 
  Plus, 
  Trash2, 
  Save, 
  Edit3,
  User,
  Briefcase,
  GraduationCap,
  Award,
  Code,
  FileText,
  ArrowUp,
  ArrowDown
} from 'lucide-react';

const ResumeEditor = ({ resume, onUpdate, loading }) => {
  const [resumeContent, setResumeContent] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (resume && resume.content) {
      setResumeContent(resume.content);
      setHasChanges(false);
    }
  }, [resume]);

  const handleContentChange = (section, field, value, index = null) => {
    if (!resumeContent) return;

    const updatedContent = { ...resumeContent };
    
    if (index !== null) {
      // Handle array items
      if (!updatedContent[section]) updatedContent[section] = [];
      if (!updatedContent[section][index]) updatedContent[section][index] = {};
      updatedContent[section][index][field] = value;
    } else if (typeof updatedContent[section] === 'object' && !Array.isArray(updatedContent[section])) {
      // Handle object fields
      updatedContent[section][field] = value;
    } else {
      // Handle direct field updates
      updatedContent[section] = value;
    }

    setResumeContent(updatedContent);
    setHasChanges(true);
  };

  const handleAddItem = (section, template = {}) => {
    if (!resumeContent) return;

    const updatedContent = { ...resumeContent };
    if (!updatedContent[section]) updatedContent[section] = [];
    updatedContent[section].push(template);
    
    setResumeContent(updatedContent);
    setHasChanges(true);
  };

  const handleRemoveItem = (section, index) => {
    if (!resumeContent) return;

    const updatedContent = { ...resumeContent };
    if (updatedContent[section] && updatedContent[section].length > index) {
      updatedContent[section].splice(index, 1);
      setResumeContent(updatedContent);
      setHasChanges(true);
    }
  };

  const handleMoveItem = (section, index, direction) => {
    if (!resumeContent || !resumeContent[section]) return;

    const items = [...resumeContent[section]];
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (newIndex < 0 || newIndex >= items.length) return;

    // Swap items
    [items[index], items[newIndex]] = [items[newIndex], items[index]];

    const updatedContent = { ...resumeContent };
    updatedContent[section] = items;
    setResumeContent(updatedContent);
    setHasChanges(true);
  };

  const handleSave = () => {
    if (resumeContent && hasChanges) {
      onUpdate(resumeContent);
      setHasChanges(false);
    }
  };

  if (!resumeContent) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Edit3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Loading resume editor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Save Button */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Edit Resume</h2>
        <Button 
          onClick={handleSave} 
          disabled={!hasChanges || loading}
          className="flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {loading ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>

      <div>
        {/* Personal Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              Personal Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name
                </label>
                <Input
                  value={resumeContent.personal_info?.name || ''}
                  onChange={(e) => handleContentChange('personal_info', 'name', e.target.value)}
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <Input
                  type="email"
                  value={resumeContent.personal_info?.email || ''}
                  onChange={(e) => handleContentChange('personal_info', 'email', e.target.value)}
                  placeholder="john@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone
                </label>
                <Input
                  value={resumeContent.personal_info?.phone || ''}
                  onChange={(e) => handleContentChange('personal_info', 'phone', e.target.value)}
                  placeholder="(555) 123-4567"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Location
                </label>
                <Input
                  value={resumeContent.personal_info?.location || ''}
                  onChange={(e) => handleContentChange('personal_info', 'location', e.target.value)}
                  placeholder="City, State"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  LinkedIn
                </label>
                <Input
                  value={resumeContent.personal_info?.linkedin || ''}
                  onChange={(e) => handleContentChange('personal_info', 'linkedin', e.target.value)}
                  placeholder="linkedin.com/in/johndoe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Website
                </label>
                <Input
                  value={resumeContent.personal_info?.website || ''}
                  onChange={(e) => handleContentChange('personal_info', 'website', e.target.value)}
                  placeholder="johndoe.com"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Professional Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Professional Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              value={resumeContent.professional_summary || ''}
              onChange={(e) => handleContentChange('professional_summary', null, e.target.value)}
              placeholder="Write a compelling professional summary..."
              rows={4}
            />
          </CardContent>
        </Card>

        {/* Experience Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Briefcase className="w-5 h-5" />
              Work Experience
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(resumeContent.experience || []).map((exp, index) => (
                <div key={index} className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex items-start gap-2">
                    <div className="flex flex-col gap-1 mt-2">
                      <button
                        onClick={() => handleMoveItem('experience', index, 'up')}
                        disabled={index === 0}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                      >
                        <ArrowUp className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => handleMoveItem('experience', index, 'down')}
                        disabled={index === (resumeContent.experience || []).length - 1}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                      >
                        <ArrowDown className="w-3 h-3" />
                      </button>
                    </div>
                            <div className="flex-1 space-y-3">
                              <div className="grid grid-cols-2 gap-4">
                                <Input
                                  value={exp.title || ''}
                                  onChange={(e) => handleContentChange('experience', 'title', e.target.value, index)}
                                  placeholder="Job Title"
                                />
                                <Input
                                  value={exp.company || ''}
                                  onChange={(e) => handleContentChange('experience', 'company', e.target.value, index)}
                                  placeholder="Company Name"
                                />
                                <Input
                                  value={exp.location || ''}
                                  onChange={(e) => handleContentChange('experience', 'location', e.target.value, index)}
                                  placeholder="Location"
                                />
                                <div className="flex gap-2">
                                  <Input
                                    value={exp.start_date || ''}
                                    onChange={(e) => handleContentChange('experience', 'start_date', e.target.value, index)}
                                    placeholder="MM/YYYY"
                                  />
                                  <Input
                                    value={exp.end_date || ''}
                                    onChange={(e) => handleContentChange('experience', 'end_date', e.target.value, index)}
                                    placeholder="MM/YYYY or Present"
                                  />
                                </div>
                              </div>
                              <Textarea
                                value={exp.description || ''}
                                onChange={(e) => handleContentChange('experience', 'description', e.target.value, index)}
                                placeholder="Describe your role and achievements..."
                                rows={3}
                              />
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRemoveItem('experience', index)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            <Button
              variant="outline"
              onClick={() => handleAddItem('experience', {
                title: '',
                company: '',
                location: '',
                start_date: '',
                end_date: '',
                description: ''
              })}
              className="mt-4 w-full"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Experience
            </Button>
          </CardContent>
        </Card>

        {/* Education Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GraduationCap className="w-5 h-5" />
              Education
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(resumeContent.education || []).map((edu, index) => (
                <div key={index} className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex items-start gap-2">
                    <div className="flex flex-col gap-1 mt-2">
                      <button
                        onClick={() => handleMoveItem('education', index, 'up')}
                        disabled={index === 0}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                      >
                        <ArrowUp className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => handleMoveItem('education', index, 'down')}
                        disabled={index === (resumeContent.education || []).length - 1}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                      >
                        <ArrowDown className="w-3 h-3" />
                      </button>
                    </div>
                            <div className="flex-1 space-y-3">
                              <div className="grid grid-cols-2 gap-4">
                                <Input
                                  value={edu.degree || ''}
                                  onChange={(e) => handleContentChange('education', 'degree', e.target.value, index)}
                                  placeholder="Degree"
                                />
                                <Input
                                  value={edu.field || ''}
                                  onChange={(e) => handleContentChange('education', 'field', e.target.value, index)}
                                  placeholder="Field of Study"
                                />
                                <Input
                                  value={edu.institution || ''}
                                  onChange={(e) => handleContentChange('education', 'institution', e.target.value, index)}
                                  placeholder="Institution"
                                />
                                <Input
                                  value={edu.graduation_date || ''}
                                  onChange={(e) => handleContentChange('education', 'graduation_date', e.target.value, index)}
                                  placeholder="MM/YYYY"
                                />
                              </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRemoveItem('education', index)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            <Button
              variant="outline"
              onClick={() => handleAddItem('education', {
                degree: '',
                field: '',
                institution: '',
                graduation_date: ''
              })}
              className="mt-4 w-full"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Education
            </Button>
          </CardContent>
        </Card>

        {/* Skills Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code className="w-5 h-5" />
              Skills
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(resumeContent.skills || []).map((skillGroup, index) => (
                <div key={index} className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex items-start gap-2">
                    <div className="flex flex-col gap-1 mt-2">
                      <button
                        onClick={() => handleMoveItem('skills', index, 'up')}
                        disabled={index === 0}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                      >
                        <ArrowUp className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => handleMoveItem('skills', index, 'down')}
                        disabled={index === (resumeContent.skills || []).length - 1}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                      >
                        <ArrowDown className="w-3 h-3" />
                      </button>
                    </div>
                            <div className="flex-1 space-y-3">
                              <Input
                                value={skillGroup.category || ''}
                                onChange={(e) => handleContentChange('skills', 'category', e.target.value, index)}
                                placeholder="Skill Category (e.g., Technical Skills)"
                              />
                              <Textarea
                                value={Array.isArray(skillGroup.skills) ? skillGroup.skills.join(', ') : skillGroup.skills || ''}
                                onChange={(e) => {
                                  const skillsArray = e.target.value.split(',').map(s => s.trim()).filter(s => s);
                                  handleContentChange('skills', 'skills', skillsArray, index);
                                }}
                                placeholder="Enter skills separated by commas"
                                rows={2}
                              />
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRemoveItem('skills', index)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            <Button
              variant="outline"
              onClick={() => handleAddItem('skills', {
                category: '',
                skills: []
              })}
              className="mt-4 w-full"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Skill Category
            </Button>
          </CardContent>
        </Card>

        {/* Certifications Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="w-5 h-5" />
              Certifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(resumeContent.certifications || []).map((cert, index) => (
                <div key={index} className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex items-start gap-2">
                    <div className="flex flex-col gap-1 mt-2">
                      <button
                        onClick={() => handleMoveItem('certifications', index, 'up')}
                        disabled={index === 0}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                      >
                        <ArrowUp className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => handleMoveItem('certifications', index, 'down')}
                        disabled={index === (resumeContent.certifications || []).length - 1}
                        className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                      >
                        <ArrowDown className="w-3 h-3" />
                      </button>
                    </div>
                            <div className="flex-1 space-y-3">
                              <div className="grid grid-cols-2 gap-4">
                                <Input
                                  value={cert.name || ''}
                                  onChange={(e) => handleContentChange('certifications', 'name', e.target.value, index)}
                                  placeholder="Certification Name"
                                />
                                <Input
                                  value={cert.issuer || ''}
                                  onChange={(e) => handleContentChange('certifications', 'issuer', e.target.value, index)}
                                  placeholder="Issuing Organization"
                                />
                                <Input
                                  value={cert.date || ''}
                                  onChange={(e) => handleContentChange('certifications', 'date', e.target.value, index)}
                                  placeholder="MM/YYYY"
                                />
                                <Input
                                  value={cert.expiry || ''}
                                  onChange={(e) => handleContentChange('certifications', 'expiry', e.target.value, index)}
                                  placeholder="Expiry (MM/YYYY or leave blank)"
                                />
                              </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRemoveItem('certifications', index)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            <Button
              variant="outline"
              onClick={() => handleAddItem('certifications', {
                name: '',
                issuer: '',
                date: '',
                expiry: ''
              })}
              className="mt-4 w-full"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Certification
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Save Button at Bottom */}
      <div className="flex justify-center">
        <Button 
          onClick={handleSave} 
          disabled={!hasChanges || loading}
          size="lg"
          className="px-8"
        >
          <Save className="w-4 h-4 mr-2" />
          {loading ? 'Saving...' : 'Save Resume'}
        </Button>
      </div>
    </div>
  );
};

export default ResumeEditor;