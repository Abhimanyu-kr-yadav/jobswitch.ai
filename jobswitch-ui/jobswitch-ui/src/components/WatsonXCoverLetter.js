import React from "react";
import "../styles/WatsonXCoverLetter.css";

function WatsonXCoverLetter({ coverLetter, onChange }) {
  return (
    <div className="cover-letter-container">
      <h2>Generated Cover Letter</h2>
      <textarea
        value={coverLetter}
        onChange={onChange}
        rows={10}
        cols={50}
        className="cover-letter-textarea"
      />
      <div className="cover-letter-actions">
        <button onClick={() => alert("Cover letter saved!")}>Save</button>
        <button onClick={() => alert("Further prompts coming soon!")}>
          More Options
        </button>
      </div>
    </div>
  );
}

export default WatsonXCoverLetter;
