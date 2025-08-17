/**
 * Test utilities for JobSwitch.ai frontend tests
 */
import React from 'react';
import { render } from '@testing-library/react';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock user data
export const mockUser = {
  user_id: 'test-user-123',
  email: 'test@example.com',
  full_name: 'Test User',
  skills: [
    { name: 'Python', category: 'programming', proficiency: 'advanced' },
    { name: 'React', category: 'frontend', proficiency: 'intermediate' }
  ],
  experience: [
    {
      title: 'Software Engineer',
      company: 'TechCorp',
      duration: '2020-2023',
      description: 'Developed web applications'
    }
  ],
  preferences: {
    job_types: ['full-time'],
    locations: ['remote', 'san-francisco'],
    salary_range: { min: 80000, max: 120000 }
  }
};

// Mock job data
export const mockJob = {
  job_id: 'job-123',
  title: 'Senior Software Engineer',
  company: 'TechCorp',
  location: 'San Francisco, CA',
  description: 'We are looking for a senior software engineer...',
  requirements: ['5+ years Python', '3+ years React', 'AWS experience'],
  salary_range: { min: 100000, max: 150000 },
  match_score: 0.85,
  source: 'linkedin'
};

// Mock resume data
export const mockResume = {
  resume_id: 'resume-123',
  user_id: 'test-user-123',
  version: 1,
  content: {
    personal_info: {
      name: 'Test User',
      email: 'test@example.com',
      phone: '+1-555-0123'
    },
    summary: 'Experienced software engineer with 5+ years in web development',
    experience: [
      {
        title: 'Software Engineer',
        company: 'TechCorp',
        duration: '2020-2023',
        achievements: [
          'Developed 10+ web applications',
          'Improved system performance by 30%'
        ]
      }
    ],
    skills: ['Python', 'React', 'AWS', 'PostgreSQL'],
    education: [
      {
        degree: 'Bachelor of Computer Science',
        institution: 'Tech University',
        year: 2020
      }
    ]
  },
  ats_score: 85,
  target_job_id: 'job-123'
};

// Mock interview session data
export const mockInterviewSession = {
  session_id: 'interview-123',
  user_id: 'test-user-123',
  job_role: 'Senior Software Engineer',
  questions: [
    {
      question_id: 'q1',
      question: 'Tell me about yourself',
      type: 'behavioral',
      difficulty: 'easy'
    },
    {
      question_id: 'q2',
      question: 'Describe a challenging project',
      type: 'behavioral',
      difficulty: 'medium'
    }
  ],
  responses: [
    {
      question_id: 'q1',
      response: 'I am a software engineer with 5 years of experience...',
      duration_seconds: 120
    }
  ],
  feedback: {
    overall_score: 8,
    strengths: ['Clear communication', 'Good examples'],
    improvements: ['More specific metrics', 'Better structure']
  }
};

// Mock API responses
export const mockApiResponses = {
  login: {
    access_token: 'mock-token',
    user: mockUser
  },
  jobs: {
    jobs: [mockJob],
    total: 1,
    page: 1,
    per_page: 10
  },
  recommendations: {
    recommendations: [
      {
        ...mockJob,
        reason: 'Strong skill match with Python and React'
      }
    ]
  },
  skillsAnalysis: {
    matching_skills: [
      { name: 'Python', match_strength: 'strong' }
    ],
    critical_gaps: [
      { skill: 'Kubernetes', priority: 'high' }
    ],
    overall_readiness: { percentage: 75 }
  },
  resumeOptimization: {
    optimized_resume: mockResume.content,
    ats_score: 85,
    improvements: ['Added relevant keywords', 'Improved formatting']
  },
  interviewPreparation: {
    questions: mockInterviewSession.questions,
    session_id: 'interview-123'
  }
};

// Custom render function with providers
export const renderWithProviders = (ui, options = {}) => {
  const {
    initialAuthState = {
      user: mockUser,
      token: 'mock-token',
      isAuthenticated: true,
      isLoading: false
    },
    ...renderOptions
  } = options;

  const Wrapper = ({ children }) => {
    return (
      <AuthProvider initialState={initialAuthState}>
        {children}
      </AuthProvider>
    );
  };

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Mock fetch responses
export const mockFetch = (responses = {}) => {
  global.fetch = jest.fn((url, options) => {
    const method = options?.method || 'GET';
    const key = `${method} ${url}`;
    
    if (responses[key]) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(responses[key])
      });
    }
    
    // Default responses
    if (url.includes('/auth/login')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockApiResponses.login)
      });
    }
    
    if (url.includes('/jobs/discover') || url.includes('/jobs/search')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockApiResponses.jobs)
      });
    }
    
    if (url.includes('/jobs/recommendations')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockApiResponses.recommendations)
      });
    }
    
    if (url.includes('/skills/analyze')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockApiResponses.skillsAnalysis)
      });
    }
    
    if (url.includes('/resume/optimize')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockApiResponses.resumeOptimization)
      });
    }
    
    if (url.includes('/interview/prepare')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockApiResponses.interviewPreparation)
      });
    }
    
    // Default fallback
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({})
    });
  });
};

// Wait for async operations
export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0));

// Mock WebSocket for real-time features
export const mockWebSocket = () => {
  const mockWs = {
    send: jest.fn(),
    close: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    readyState: WebSocket.OPEN
  };
  
  global.WebSocket = jest.fn(() => mockWs);
  return mockWs;
};

// Create mock event
export const createMockEvent = (type, properties = {}) => {
  const event = new Event(type, { bubbles: true, cancelable: true });
  Object.assign(event, properties);
  return event;
};

// Mock file for file upload tests
export const createMockFile = (name = 'test.pdf', type = 'application/pdf', size = 1024) => {
  const file = new File(['test content'], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
};

// Mock drag and drop events
export const createMockDragEvent = (type, files = []) => {
  const event = createMockEvent(type);
  event.dataTransfer = {
    files,
    items: files.map(file => ({ kind: 'file', type: file.type, getAsFile: () => file })),
    types: ['Files']
  };
  return event;
};

// Performance testing utilities
export const measureRenderTime = async (renderFn) => {
  const start = performance.now();
  const result = await renderFn();
  const end = performance.now();
  return {
    result,
    renderTime: end - start
  };
};

// Accessibility testing utilities
export const checkAccessibility = async (container) => {
  const { axe } = await import('@axe-core/react');
  const results = await axe(container);
  return results;
};

// Mock intersection observer for lazy loading tests
export const mockIntersectionObserver = () => {
  const mockIntersectionObserver = jest.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
  });
  
  global.IntersectionObserver = mockIntersectionObserver;
  return mockIntersectionObserver;
};

// Mock resize observer for responsive tests
export const mockResizeObserver = () => {
  const mockResizeObserver = jest.fn();
  mockResizeObserver.mockReturnValue({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
  });
  
  global.ResizeObserver = mockResizeObserver;
  return mockResizeObserver;
};

export default {
  mockUser,
  mockJob,
  mockResume,
  mockInterviewSession,
  mockApiResponses,
  renderWithProviders,
  mockFetch,
  waitForAsync,
  mockWebSocket,
  createMockEvent,
  createMockFile,
  createMockDragEvent,
  measureRenderTime,
  checkAccessibility,
  mockIntersectionObserver,
  mockResizeObserver
};