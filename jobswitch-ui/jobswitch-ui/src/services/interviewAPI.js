import api from './api';

export const interviewAPI = {
  /**
   * Generate interview questions based on job role, company, and skills
   */
  generateQuestions: async (data) => {
    try {
      const response = await api.post('/agents/interview-preparation/generate-questions', data);
      return response.data;
    } catch (error) {
      console.error('Error generating questions:', error);
      throw error;
    }
  },

  /**
   * Start a new mock interview session
   */
  startMockInterview: async (data) => {
    try {
      const response = await api.post('/agents/interview-preparation/start-mock-interview', data);
      return response.data;
    } catch (error) {
      console.error('Error starting mock interview:', error);
      throw error;
    }
  },

  /**
   * Submit response to interview question
   */
  submitResponse: async (data) => {
    try {
      const response = await api.post('/agents/interview-preparation/submit-response', data);
      return response.data;
    } catch (error) {
      console.error('Error submitting response:', error);
      throw error;
    }
  },

  /**
   * End an active interview session
   */
  endSession: async (data) => {
    try {
      const response = await api.post('/agents/interview-preparation/end-session', data);
      return response.data;
    } catch (error) {
      console.error('Error ending session:', error);
      throw error;
    }
  },

  /**
   * Get feedback for completed interview session
   */
  getFeedback: async (data) => {
    try {
      const response = await api.post('/agents/interview-preparation/get-feedback', data);
      return response.data;
    } catch (error) {
      console.error('Error getting feedback:', error);
      throw error;
    }
  },

  /**
   * Get interview preparation recommendations for the user
   */
  getRecommendations: async () => {
    try {
      const response = await api.get('/agents/interview-preparation/recommendations');
      return response.data;
    } catch (error) {
      console.error('Error getting recommendations:', error);
      throw error;
    }
  },

  /**
   * Upload audio or video recording for interview response
   */
  uploadRecording: async (sessionId, file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);

      const response = await api.post('/agents/interview-preparation/upload-recording', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading recording:', error);
      throw error;
    }
  },

  /**
   * Process audio file to extract text using speech-to-text with enhanced analysis
   */
  processSpeechToText: async (audioUrl) => {
    try {
      const response = await api.post('/agents/interview-preparation/process-speech-to-text', {
        audio_url: audioUrl
      });
      return response.data;
    } catch (error) {
      console.error('Error processing speech-to-text:', error);
      throw error;
    }
  },

  /**
   * Analyze speech patterns from multiple audio responses
   */
  analyzeSpeechPatterns: async (audioUrls) => {
    try {
      const response = await api.post('/agents/interview-preparation/analyze-speech-patterns', {
        audio_urls: audioUrls
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing speech patterns:', error);
      throw error;
    }
  }
};