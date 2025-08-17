import axios from "axios";

// Connect to your FastAPI backend running locally
const BACKEND_API_URL = "http://localhost:5000/api/generate-cover-letter";

export const generateCoverLetter = async (jobDescription) => {
  try {
    const response = await axios.post(BACKEND_API_URL, {
      description: jobDescription,
    });
    return response.data.coverLetter; // Adjust if response structure is different
  } catch (error) {
    console.error("Error generating cover letter:", error);
    throw error;
  }
};
