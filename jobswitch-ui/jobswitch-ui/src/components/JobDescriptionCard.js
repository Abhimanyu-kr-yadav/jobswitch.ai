import React, { useState } from "react";
import ChatBox from "./ChatBox";
import "../styles/JobDescriptionCard.css";

function JobDescriptionCard() {
  const [isChatBoxOpen, setChatBoxOpen] = useState(false);

  const handleOpenChatBox = () => {
    setChatBoxOpen(true);
  };

  const handleCloseChatBox = () => {
    setChatBoxOpen(false);
  };

  return (
    <div className="job-description-card max-w-md mx-auto bg-white rounded-xl shadow-md p-6 mt-8">
      <h2 className="text-2xl font-bold text-blue-600 mb-2">Job Description</h2>
      <p className="text-gray-700 mb-4">
        Paste your job description below to generate a custom cover letter.
      </p>
      <button
        onClick={handleOpenChatBox}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
      >
        Open Chat Box
      </button>
      {isChatBoxOpen && <ChatBox onClose={handleCloseChatBox} />}
    </div>
  );
}

export default JobDescriptionCard;
