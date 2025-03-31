import { useState, useEffect } from 'react';
import './AgeVerification.css';

const AgeVerification = ({ onVerified }) => {
  const [show, setShow] = useState(true);
  
  useEffect(() => {
    // Check if user has previously verified
    const verified = localStorage.getItem('ageVerified');
    const verifiedDate = localStorage.getItem('ageVerifiedDate');

    // Check if verification exists and is less than 7 days old
    const isValid = verified === 'true' && verifiedDate && 
                  (new Date().getTime() - parseInt(verifiedDate) < 7 * 24 * 60 * 60 * 1000);

    if (isValid === 'true') {
      setShow(false);
      onVerified();
    }
  }, [onVerified]);
  
  const handleVerify = () => {
    localStorage.setItem('ageVerified', 'true');
    localStorage.setItem('ageVerifiedDate', new Date().getTime().toString());
    setShow(false);
    onVerified();
  };
  
  const handleReject = () => {
    window.location.href = 'https://www.responsibility.org/';
  };
  
  if (!show) return null;
  
  return (
    <div className="age-verification-overlay">
      <div className="age-verification-modal">
        <h2>Age Verification</h2>
        <div className="logo">🍺</div>
        <p>Welcome to Chicago Beer Finder</p>
        <p>You must be 21 years or older to visit this site.</p>
        <div className="buttons">
          <button onClick={handleVerify} className="verify-button">
            Yes, I am 21 or older
          </button>
          <button onClick={handleReject} className="reject-button">
            No, I am under 21
          </button>
        </div>
        <p className="disclaimer">
          Please drink responsibly. Don't drink and drive.
        </p>
      </div>
    </div>
  );
};

export default AgeVerification;