import React from 'react';
import { Heart, Bot } from 'lucide-react';

const TabNavigation = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'mood', label: 'Mood Discovery', icon: Heart },
    { id: 'custom', label: 'Custom AI Playlists', icon: Bot }
  ];

  return (
    <div className="flex space-x-1 bg-gray-900 p-1 rounded-lg mb-8">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center px-6 py-4 rounded-md font-semibold transition-all duration-200 ${
              activeTab === tab.id
                ? 'bg-white text-black shadow-lg'
                : 'text-gray-300 hover:text-white hover:bg-gray-800'
            }`}
          >
            <Icon className="w-5 h-5 mr-2" />
            {tab.label}
          </button>
        );
      })}
    </div>
  );
};

export default TabNavigation;
