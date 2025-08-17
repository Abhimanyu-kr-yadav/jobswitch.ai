import api from './api';

export const resumeAPI = {
  // Parse resume from content or file
  parseResume: async (resumeContent = null, resumeFile = null) => {
    const formData = new FormData();
    
    if (resumeContent) {
      formData.append('resume_content', resumeContent);
    }
    
    if (resumeFile) {
      formData.append('resume_file', resumeFile);
    }
    
    const response = await api.post('/agents/resume-optimization/parse', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  // Optimize resume
  optimizeResume: async (resumeId, jobId = null, optimizationType = 'ats') => {
    const params = new URLSearchParams({
      resume_id: resumeId,
      optimization_type: optimizationType,
    });
    
    if (jobId) {
      params.append('job_id', jobId);
    }
    
    const response = await api.post(`/agents/resume-optimization/optimize?${params}`);
    return response.data;
  },

  // Analyze ATS compatibility
  analyzeATS: async (resumeId, jobId = null) => {
    const params = new URLSearchParams({
      resume_id: resumeId,
    });
    
    if (jobId) {
      params.append('job_id', jobId);
    }
    
    const response = await api.post(`/agents/resume-optimization/analyze-ats?${params}`);
    return response.data;
  },

  // Generate new resume
  generateResume: async (jobId = null, templateId = null, customContent = null) => {
    const params = new URLSearchParams();
    
    if (jobId) {
      params.append('job_id', jobId);
    }
    
    if (templateId) {
      params.append('template_id', templateId);
    }
    
    const requestData = customContent ? { content: customContent } : {};
    
    const response = await api.post(`/agents/resume-optimization/generate?${params}`, requestData);
    return response.data;
  },

  // Get resume recommendations
  getResumeRecommendations: async () => {
    const response = await api.get('/agents/resume-optimization/recommendations');
    return response.data;
  },

  // Score resume
  scoreResume: async (resumeId, jobId = null) => {
    const params = new URLSearchParams({
      resume_id: resumeId,
    });
    
    if (jobId) {
      params.append('job_id', jobId);
    }
    
    const response = await api.post(`/agents/resume-optimization/score?${params}`);
    return response.data;
  },

  // Get all user resumes
  getUserResumes: async () => {
    const response = await api.get('/agents/resume-optimization/resumes');
    return response.data;
  },

  // Get specific resume
  getResume: async (resumeId) => {
    const response = await api.get(`/agents/resume-optimization/resumes/${resumeId}`);
    return response.data;
  },

  // Delete resume
  deleteResume: async (resumeId) => {
    const response = await api.delete(`/agents/resume-optimization/resumes/${resumeId}`);
    return response.data;
  },

  // Set primary resume
  setPrimaryResume: async (resumeId) => {
    const response = await api.put(`/agents/resume-optimization/resumes/${resumeId}/primary`);
    return response.data;
  },

  // Update resume content
  updateResume: async (resumeId, content) => {
    const response = await api.put(`/agents/resume-optimization/resumes/${resumeId}`, {
      content: content
    });
    return response.data;
  },

  // Download resume as PDF
  downloadResume: async (resumeId, format = 'pdf') => {
    const response = await api.get(`/agents/resume-optimization/resumes/${resumeId}/download`, {
      params: { format },
      responseType: 'blob'
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `resume.${format}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    
    return { success: true };
  },

  // Get resume templates
  getResumeTemplates: async () => {
    const response = await api.get('/agents/resume-optimization/templates');
    return response.data;
  },

  // Get resume analysis history
  getResumeAnalyses: async (resumeId) => {
    const response = await api.get(`/agents/resume-optimization/resumes/${resumeId}/analyses`);
    return response.data;
  },

  // Get optimization history
  getOptimizationHistory: async (resumeId) => {
    const response = await api.get(`/agents/resume-optimization/resumes/${resumeId}/optimizations`);
    return response.data;
  },

  // Compare resumes
  compareResumes: async (resumeId1, resumeId2) => {
    const response = await api.post('/agents/resume-optimization/compare', {
      resume_id_1: resumeId1,
      resume_id_2: resumeId2
    });
    return response.data;
  },

  // Get ATS keywords suggestions
  getATSKeywords: async (industry = null, jobTitle = null) => {
    const params = new URLSearchParams();
    
    if (industry) {
      params.append('industry', industry);
    }
    
    if (jobTitle) {
      params.append('job_title', jobTitle);
    }
    
    const response = await api.get(`/agents/resume-optimization/ats-keywords?${params}`);
    return response.data;
  },

  // Bulk optimize resumes
  bulkOptimizeResumes: async (resumeIds, optimizationType = 'ats') => {
    const response = await api.post('/agents/resume-optimization/bulk-optimize', {
      resume_ids: resumeIds,
      optimization_type: optimizationType
    });
    return response.data;
  },

  // Get resume statistics
  getResumeStats: async (resumeId) => {
    const response = await api.get(`/agents/resume-optimization/resumes/${resumeId}/stats`);
    return response.data;
  },

  // Export resume data
  exportResumeData: async (resumeId, format = 'json') => {
    const response = await api.get(`/agents/resume-optimization/resumes/${resumeId}/export`, {
      params: { format },
      responseType: format === 'json' ? 'json' : 'blob'
    });
    
    if (format === 'json') {
      return response.data;
    } else {
      // Handle file download for other formats
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `resume-data.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return { success: true };
    }
  },

  // Resume Versioning and Management APIs

  // Get all versions of a resume
  getResumeVersions: async (resumeId) => {
    const response = await api.get(`/agents/resume-optimization/resumes/${resumeId}/versions`);
    return response.data;
  },

  // Compare two resume versions
  compareResumeVersions: async (resumeId1, resumeId2) => {
    const response = await api.post('/agents/resume-optimization/resumes/compare', {
      resume_id_1: resumeId1,
      resume_id_2: resumeId2
    });
    return response.data;
  },

  // Calculate acceptance probability for resume-job match
  calculateAcceptanceProbability: async (resumeId, jobId) => {
    const response = await api.post(`/agents/resume-optimization/resumes/${resumeId}/acceptance-probability`, {
      job_id: jobId
    });
    return response.data;
  },

  // Create a new version of an existing resume
  createResumeVersion: async (resumeId, content, title = null) => {
    const response = await api.post(`/agents/resume-optimization/resumes/${resumeId}/create-version`, {
      content: content,
      title: title
    });
    return response.data;
  },

  // Get version history with changes
  getVersionHistory: async (resumeId) => {
    const response = await api.get(`/agents/resume-optimization/resumes/${resumeId}/history`);
    return response.data;
  },

  // Restore a previous version
  restoreResumeVersion: async (resumeId, versionId) => {
    const response = await api.post(`/agents/resume-optimization/resumes/${resumeId}/restore`, {
      version_id: versionId
    });
    return response.data;
  },

  // Get version comparison summary
  getVersionComparison: async (resumeId) => {
    const response = await api.get(`/agents/resume-optimization/resumes/${resumeId}/version-comparison`);
    return response.data;
  },

  // Batch operations for version management
  batchVersionOperations: async (operations) => {
    const response = await api.post('/agents/resume-optimization/resumes/batch-operations', {
      operations: operations
    });
    return response.data;
  }
};

export default resumeAPI;