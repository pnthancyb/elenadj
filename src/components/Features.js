import React from 'react';
import { Brain, Target, Globe, Shield, Zap, Palette } from 'lucide-react';

const Features = () => {
  const features = [
    {
      icon: Brain,
      title: 'Advanced AI Analysis',
      description: 'Powered by LLaMA 3 70B for sophisticated mood understanding and music curation',
    },
    {
      icon: Target,
      title: 'Quality Filtering',
      description: 'Smart popularity thresholds and artist verification ensure high-quality tracks',
    },
    {
      icon: Globe,
      title: 'Multi-Language Support',
      description: 'Optimized search algorithms for 11+ languages with regional market targeting',
    },
    {
      icon: Shield,
      title: 'Secure Integration',
      description: 'OAuth 2.0 authentication with Spotify for safe and private playlist creation',
    },
    {
      icon: Zap,
      title: 'Instant Creation',
      description: 'Generate and populate playlists directly in your Spotify account within seconds',
    },
    {
      icon: Palette,
      title: 'Smart Descriptions',
      description: 'AI-generated contextual playlist names and descriptions that capture your vibe',
    },
  ];

  return (
    <div className="mt-16">
      <div className="card">
        <h2 className="text-3xl font-bold text-center mb-12">🌟 Elena DJ Features</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="text-center p-6 rounded-xl bg-gray-800 border border-gray-700 hover:border-gray-600 transition-all duration-300 hover:transform hover:scale-105"
              >
                <Icon className="w-12 h-12 text-white mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-3 text-white">{feature.title}</h3>
                <p className="text-gray-300 text-sm leading-relaxed">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Features;
