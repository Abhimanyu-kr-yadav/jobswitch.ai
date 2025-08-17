import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { 
  Download, 
  Eye, 
  FileText, 
  Mail, 
  Phone, 
  MapPin, 
  Globe,
  Linkedin,
  Calendar
} from 'lucide-react';

const ResumePreview = ({ resume, onDownload }) => {
  const [previewFormat, setPreviewFormat] = useState('modern');

  if (!resume || !resume.content) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Resume to Preview</h3>
          <p className="text-gray-600">Select a resume to see the preview</p>
        </CardContent>
      </Card>
    );
  }

  const { content } = resume;

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    if (dateStr.toLowerCase() === 'present') return 'Present';
    return dateStr;
  };

  const formatSkills = (skills) => {
    if (Array.isArray(skills)) {
      return skills.join(', ');
    }
    return skills || '';
  };

  return (
    <div className="space-y-6">
      {/* Preview Controls */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-semibold text-gray-900">Resume Preview</h2>
          <div className="flex items-center gap-2">
            <Badge variant="outline">Version {resume.version}</Badge>
            {resume.ats_score && (
              <Badge variant={resume.ats_score >= 0.8 ? "success" : "warning"}>
                ATS Score: {Math.round(resume.ats_score * 100)}%
              </Badge>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <select
            value={previewFormat}
            onChange={(e) => setPreviewFormat(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="modern">Modern Template</option>
            <option value="classic">Classic Template</option>
            <option value="minimal">Minimal Template</option>
          </select>
          
          <Button variant="outline" onClick={() => window.print()}>
            <Eye className="w-4 h-4 mr-2" />
            Print Preview
          </Button>
          
          <Button onClick={onDownload}>
            <Download className="w-4 h-4 mr-2" />
            Download PDF
          </Button>
        </div>
      </div>

      {/* Resume Preview */}
      <Card className="max-w-4xl mx-auto">
        <CardContent className="p-8">
          <div className="resume-preview bg-white" style={{ minHeight: '11in', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
            
            {/* Header Section */}
            <div className="border-b-2 border-gray-200 pb-6 mb-6">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {content.personal_info?.name || 'Your Name'}
              </h1>
              
              <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                {content.personal_info?.email && (
                  <div className="flex items-center gap-1">
                    <Mail className="w-4 h-4" />
                    <span>{content.personal_info.email}</span>
                  </div>
                )}
                
                {content.personal_info?.phone && (
                  <div className="flex items-center gap-1">
                    <Phone className="w-4 h-4" />
                    <span>{content.personal_info.phone}</span>
                  </div>
                )}
                
                {content.personal_info?.location && (
                  <div className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    <span>{content.personal_info.location}</span>
                  </div>
                )}
                
                {content.personal_info?.linkedin && (
                  <div className="flex items-center gap-1">
                    <Linkedin className="w-4 h-4" />
                    <span>{content.personal_info.linkedin}</span>
                  </div>
                )}
                
                {content.personal_info?.website && (
                  <div className="flex items-center gap-1">
                    <Globe className="w-4 h-4" />
                    <span>{content.personal_info.website}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Professional Summary */}
            {content.professional_summary && (
              <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 mb-3 border-b border-gray-300 pb-1">
                  Professional Summary
                </h2>
                <p className="text-gray-700 leading-relaxed">
                  {content.professional_summary}
                </p>
              </div>
            )}

            {/* Experience Section */}
            {content.experience && content.experience.length > 0 && (
              <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 mb-3 border-b border-gray-300 pb-1">
                  Professional Experience
                </h2>
                <div className="space-y-4">
                  {content.experience.map((exp, index) => (
                    <div key={index} className="border-l-2 border-blue-200 pl-4">
                      <div className="flex justify-between items-start mb-1">
                        <div>
                          <h3 className="font-semibold text-gray-900">{exp.title}</h3>
                          <p className="text-gray-700">{exp.company}</p>
                        </div>
                        <div className="text-right text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            <span>{formatDate(exp.start_date)} - {formatDate(exp.end_date)}</span>
                          </div>
                          {exp.location && (
                            <div className="flex items-center gap-1 mt-1">
                              <MapPin className="w-3 h-3" />
                              <span>{exp.location}</span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {exp.description && (
                        <div className="mt-2">
                          <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-line">
                            {exp.description}
                          </p>
                        </div>
                      )}
                      
                      {exp.achievements && exp.achievements.length > 0 && (
                        <ul className="mt-2 space-y-1">
                          {exp.achievements.map((achievement, achIndex) => (
                            <li key={achIndex} className="text-sm text-gray-700 flex items-start">
                              <span className="text-blue-600 mr-2">•</span>
                              <span>{achievement}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Education Section */}
            {content.education && content.education.length > 0 && (
              <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 mb-3 border-b border-gray-300 pb-1">
                  Education
                </h2>
                <div className="space-y-3">
                  {content.education.map((edu, index) => (
                    <div key={index} className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {edu.degree} {edu.field && `in ${edu.field}`}
                        </h3>
                        <p className="text-gray-700">{edu.institution}</p>
                        {edu.gpa && (
                          <p className="text-sm text-gray-600">GPA: {edu.gpa}</p>
                        )}
                      </div>
                      {edu.graduation_date && (
                        <div className="text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            <span>{formatDate(edu.graduation_date)}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Skills Section */}
            {content.skills && content.skills.length > 0 && (
              <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 mb-3 border-b border-gray-300 pb-1">
                  Skills
                </h2>
                <div className="space-y-3">
                  {content.skills.map((skillGroup, index) => (
                    <div key={index}>
                      {skillGroup.category && (
                        <h3 className="font-semibold text-gray-900 mb-1">
                          {skillGroup.category}
                        </h3>
                      )}
                      <p className="text-gray-700 text-sm">
                        {formatSkills(skillGroup.skills)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Certifications Section */}
            {content.certifications && content.certifications.length > 0 && (
              <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 mb-3 border-b border-gray-300 pb-1">
                  Certifications
                </h2>
                <div className="space-y-2">
                  {content.certifications.map((cert, index) => (
                    <div key={index} className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold text-gray-900">{cert.name}</h3>
                        <p className="text-gray-700 text-sm">{cert.issuer}</p>
                      </div>
                      <div className="text-sm text-gray-600">
                        {cert.date && (
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            <span>{formatDate(cert.date)}</span>
                            {cert.expiry && <span> - {formatDate(cert.expiry)}</span>}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Projects Section */}
            {content.projects && content.projects.length > 0 && (
              <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 mb-3 border-b border-gray-300 pb-1">
                  Projects
                </h2>
                <div className="space-y-3">
                  {content.projects.map((project, index) => (
                    <div key={index}>
                      <div className="flex justify-between items-start mb-1">
                        <h3 className="font-semibold text-gray-900">{project.name}</h3>
                        {project.url && (
                          <a 
                            href={project.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 text-sm hover:underline"
                          >
                            View Project
                          </a>
                        )}
                      </div>
                      
                      {project.description && (
                        <p className="text-gray-700 text-sm mb-1">
                          {project.description}
                        </p>
                      )}
                      
                      {project.technologies && project.technologies.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {project.technologies.map((tech, techIndex) => (
                            <Badge key={techIndex} variant="outline" className="text-xs">
                              {tech}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Preview Info */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              <p>Last updated: {new Date(resume.updated_at).toLocaleDateString()}</p>
              <p>Template: {previewFormat.charAt(0).toUpperCase() + previewFormat.slice(1)}</p>
            </div>
            <div className="text-right">
              <p>Resume ID: {resume.resume_id}</p>
              <p>Version: {resume.version}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ResumePreview;