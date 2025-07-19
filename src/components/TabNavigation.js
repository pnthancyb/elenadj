
import React from 'react';
import { Brain, Bot } from 'lucide-react';

const TabNavigation = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'mood', label: 'Mood Discovery', icon: Brain, description: 'Emotion-driven playlists' },
    { id: 'custom', label: 'Custom AI Playlists', icon: Bot, description: 'AI-powered custom playlists' }
  ];

  return (
    <div className="flex space-x-2 p-1 bg-gray-900 rounded-xl border border-gray-800">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        
        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center space-x-3 py-4 px-6 rounded-lg font-semibold transition-all duration-200 ${
              isActive
                ? 'bg-white text-black shadow-lg transform scale-105'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            <Icon className="w-5 h-5" />
            <div className="text-left">
              <div className="font-semibold">{tab.label}</div>
              <div className={`text-xs ${isActive ? 'text-gray-600' : 'text-gray-500'}`}>
                {tab.description}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
};

export default TabNavigation;
