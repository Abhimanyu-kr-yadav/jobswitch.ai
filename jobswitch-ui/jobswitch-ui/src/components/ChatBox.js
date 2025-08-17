import React, { useState } from "react";
import { generateCoverLetter } from "../utils/watsonxApi";

function ChatBox({ onClose }) {
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [coverLetter, setCoverLetter] = useState("");
  const [error, setError] = useState(""); // Add error state

  const handleInputChange = (event) => {
    setJobDescription(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(""); // Reset error
    try {
      const letter = await generateCoverLetter(jobDescription);
      setCoverLetter(letter);
    } catch (error) {
      setError("Failed to generate cover letter. Please try again.");
      console.error("Error generating cover letter:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
      <div className="bg-white rounded-xl shadow-lg p-6 w-full max-w-lg relative">
        <button
          className="absolute top-4 right-4 text-gray-500 hover:text-red-500 text-xl font-bold"
          onClick={onClose}
        >
          ×
        </button>
        <h2 className="text-xl font-semibold text-blue-600 mb-4">
          Paste Job Description
        </h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <textarea
            value={jobDescription}
            onChange={handleInputChange}
            placeholder="Paste job description here..."
            rows="5"
            required
            className="border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate Cover Letter"}
          </button>
          {error && <div className="text-red-600 text-sm mt-2">{error}</div>}
        </form>
        {coverLetter && (
          <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="text-lg font-bold text-gray-800 mb-2">
              Generated Cover Letter
            </h3>
            <textarea
              className="w-full border border-gray-300 rounded-lg p-2 text-gray-700"
              rows="8"
              value={coverLetter}
              onChange={(e) => setCoverLetter(e.target.value)}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatBox;
