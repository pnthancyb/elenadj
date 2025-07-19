import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import Header from './components/Header';
import AuthSection from './components/AuthSection';
import TabNavigation from './components/TabNavigation';
import MoodTab from './components/MoodTab';
import CustomTab from './components/CustomTab';
import Features from './components/Features';
import Footer from './components/Footer';
import { checkAuthStatus } from './services/api';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState('mood');

  useEffect(() => {
    checkAuthStatus().then(setIsAuthenticated).catch(() => setIsAuthenticated(false));
  }, []);

  return (
    <div className="min-h-screen bg-black text-white">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1f2937',
            color: '#ffffff',
            border: '1px solid #374151',
          },
        }}
      />

      <div className="max-w-4xl mx-auto px-4 py-8">
        <Header />

        <AuthSection 
          isAuthenticated={isAuthenticated} 
          onAuthSuccess={() => setIsAuthenticated(true)} 
        />

        <TabNavigation activeTab={activeTab} setActiveTab={setActiveTab} />

        <div className="mt-8">
          {activeTab === 'mood' && (
            <MoodTab isAuthenticated={isAuthenticated} />
          )}
          {activeTab === 'custom' && (
            <CustomTab isAuthenticated={isAuthenticated} />
          )}
        </div>

        <Features />
        <Footer />
      </div>
    </div>
  );
}

export default App;