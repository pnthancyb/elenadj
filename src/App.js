
import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import Header from './components/Header';
import AuthSection from './components/AuthSection';
import MoodTab from './components/MoodTab';
import CustomTab from './components/CustomTab';
import Features from './components/Features';
import Footer from './components/Footer';
import TabNavigation from './components/TabNavigation';
import { checkAuthStatus } from './services/api';

function App() {
  const [activeTab, setActiveTab] = useState('mood');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await checkAuthStatus();
        setIsAuthenticated(response.authenticated);
      } catch (error) {
        console.error('Failed to check auth status:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="animate-pulse-subtle">
          <div className="text-4xl font-bold text-white mb-4">🎵 Elena - Your DJ</div>
          <div className="text-gray-400">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1f2937',
            color: '#ffffff',
            border: '1px solid #374151',
          },
        }}
      />
      
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        <Header />
        
        <AuthSection 
          isAuthenticated={isAuthenticated}
          setIsAuthenticated={setIsAuthenticated}
        />
        
        <TabNavigation 
          activeTab={activeTab}
          setActiveTab={setActiveTab}
        />
        
        <div className="animate-fade-in">
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
