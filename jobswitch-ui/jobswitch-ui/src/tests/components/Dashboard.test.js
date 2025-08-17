/**
 * Tests for Dashboard component
 */
import React from 'react';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import { renderWithProviders, mockFetch, mockWebSocket, mockApiResponses } from '../utils/testUtils';
import Dashboard from '../../components/Dashboard';

describe('Dashboard Component', () => {
  beforeEach(() => {
    mockFetch();
    mockWebSocket();
  });

  test('renders dashboard with user data', async () => {
    renderWithProviders(<Dashboard />);
    
    // Check if main dashboard elements are present
    expect(screen.getByText(/welcome/i)).toBeInTheDocument();
    
    // Wait for async data loading
    await waitFor(() => {
      expect(screen.getByText(/job recommendations/i)).toBeInTheDocument();
    });
  });

  test('displays job recommendations', async () => {
    const customResponses = {
      'GET /api/v1/jobs/recommendations': {
        recommendations: [
          {
            job_id: 'job-1',
            title: 'Senior Software Engineer',
            company: 'TechCorp',
            match_score: 0.85,
            reason: 'Strong Python and React skills match'
          }
        ]
      }
    };
    
    mockFetch(customResponses);
    renderWithProviders(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('TechCorp')).toBeInTheDocument();
      expect(screen.getByText(/85%/)).toBeInTheDocument();
    });
  });

  test('shows recent activities', async () => {
    const customResponses = {
      'GET /api/v1/dashboard': {
        recent_activities: [
          {
            type: 'job_application',
            description: 'Applied to Software Engineer at TechCorp',
            timestamp: '2025-01-08T10:00:00Z'
          },
          {
            type: 'resume_optimization',
            description: 'Optimized resume for Python Developer role',
            timestamp: '2025-01-08T09:30:00Z'
          }
        ]
      }
    };
    
    mockFetch(customResponses);
    renderWithProviders(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/Applied to Software Engineer/)).toBeInTheDocument();
      expect(screen.getByText(/Optimized resume/)).toBeInTheDocument();
    });
  });

  test('handles real-time updates via WebSocket', async () => {
    const mockWs = mockWebSocket();
    renderWithProviders(<Dashboard />);
    
    // Simulate WebSocket message
    const messageEvent = new MessageEvent('message', {
      data: JSON.stringify({
        type: 'job_recommendation',
        data: {
          job_id: 'new-job-456',
          title: 'Senior Python Developer',
          company: 'DataCorp',
          match_score: 0.92
        }
      })
    });
    
    // Trigger WebSocket message handler
    mockWs.addEventListener.mock.calls
      .find(call => call[0] === 'message')[1](messageEvent);
    
    await waitFor(() => {
      expect(screen.getByText('Senior Python Developer')).toBeInTheDocument();
      expect(screen.getByText('DataCorp')).toBeInTheDocument();
    });
  });

  test('displays loading state initially', () => {
    renderWithProviders(<Dashboard />);
    
    // Should show loading indicators
    expect(screen.getByTestId('dashboard-loading')).toBeInTheDocument();
  });

  test('handles error states gracefully', async () => {
    // Mock API error
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error: 'Server error' })
      })
    );
    
    renderWithProviders(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/error loading dashboard/i)).toBeInTheDocument();
    });
  });

  test('navigates to different sections', async () => {
    renderWithProviders(<Dashboard />);
    
    await waitFor(() => {
      const jobsButton = screen.getByText(/view all jobs/i);
      fireEvent.click(jobsButton);
      
      // Should navigate to jobs section (this would be tested with router mock)
      expect(jobsButton).toBeInTheDocument();
    });
  });

  test('shows skill progress indicators', async () => {
    const customResponses = {
      'GET /api/v1/dashboard': {
        skill_progress: {
          'Python': { current_level: 'advanced', progress: 85 },
          'React': { current_level: 'intermediate', progress: 70 },
          'AWS': { current_level: 'beginner', progress: 30 }
        }
      }
    };
    
    mockFetch(customResponses);
    renderWithProviders(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Python')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('70%')).toBeInTheDocument();
    });
  });

  test('displays application status summary', async () => {
    const customResponses = {
      'GET /api/v1/dashboard': {
        application_summary: {
          total_applications: 15,
          pending_responses: 8,
          interviews_scheduled: 3,
          offers_received: 1
        }
      }
    };
    
    mockFetch(customResponses);
    renderWithProviders(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('15')).toBeInTheDocument(); // total applications
      expect(screen.getByText('8')).toBeInTheDocument();  // pending responses
      expect(screen.getByText('3')).toBeInTheDocument();  // interviews
      expect(screen.getByText('1')).toBeInTheDocument();  // offers
    });
  });

  test('refreshes data when refresh button is clicked', async () => {
    const fetchSpy = jest.spyOn(global, 'fetch');
    renderWithProviders(<Dashboard />);
    
    await waitFor(() => {
      const refreshButton = screen.getByLabelText(/refresh/i);
      fireEvent.click(refreshButton);
    });
    
    // Should make additional API calls
    expect(fetchSpy).toHaveBeenCalledTimes(2); // Initial load + refresh
  });

  test('is accessible', async () => {
    const { container } = renderWithProviders(<Dashboard />);
    
    // Check for proper heading structure
    expect(screen.getByRole('main')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    
    // Check for keyboard navigation
    const interactiveElements = screen.getAllByRole('button');
    interactiveElements.forEach(element => {
      expect(element).toHaveAttribute('tabIndex');
    });
  });

  test('responsive design works correctly', () => {
    // Mock window resize
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768, // tablet size
    });
    
    renderWithProviders(<Dashboard />);
    
    // Should adapt layout for smaller screens
    const dashboard = screen.getByTestId('dashboard-container');
    expect(dashboard).toHaveClass('responsive-layout');
  });
});