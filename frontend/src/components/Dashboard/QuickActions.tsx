import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface QuickActionsProps {
  hasTexts: boolean;
  hasContests: boolean;
  hasAgents: boolean;
  urgentActions?: any[];
}

const QuickActions: React.FC<QuickActionsProps> = ({ 
  hasTexts, 
  hasContests, 
  hasAgents, 
  urgentActions = [] 
}) => {
  const { user } = useAuth();

  // Determine what actions to suggest based on user's current state
  const getSuggestedActions = () => {
    const actions = [];

    // Priority 1: Urgent actions
    if (urgentActions.length > 0) {
      actions.push({
        title: "Complete Pending Evaluations",
        description: `You have ${urgentActions.length} contest${urgentActions.length === 1 ? '' : 's'} waiting for your judgment`,
        icon: "⚖️",
        color: "red",
        link: `/contests/${urgentActions[0].contest_id}`,
        priority: 1
      });
    }

    // Priority 2: If no texts, encourage writing
    if (!hasTexts) {
      actions.push({
        title: "Write Your First Text",
        description: "Start your literary journey by creating your first story, poem, or essay",
        icon: "✍️",
        color: "blue",
        link: "/dashboard?tab=texts",
        priority: 2
      });
    }

    // Priority 3: If no AI agents, suggest creating one
    if (!hasAgents) {
      actions.push({
        title: "Create an AI Writing Assistant",
        description: "Set up an AI agent to help with writing or judging",
        icon: "🤖",
        color: "purple",
        link: "/dashboard?tab=agents",
        priority: 3
      });
    }

    // Priority 4: If no contests, suggest joining one
    if (!hasContests) {
      actions.push({
        title: "Join Your First Contest",
        description: "Browse public contests and participate as an author or judge",
        icon: "🏆",
        color: "green",
        link: "/contests",
        priority: 4
      });
    }

    // Always suggest exploring if they have basic setup
    if (hasTexts && hasAgents) {
      actions.push({
        title: "Explore Public Contests",
        description: "Discover new literary competitions to join",
        icon: "🔍",
        color: "indigo",
        link: "/contests",
        priority: 5
      });
    }

    // Suggest AI writer if they have texts but haven't used AI
    if (hasTexts && hasAgents) {
      actions.push({
        title: "Try AI-Assisted Writing",
        description: "Use your AI agents to create new content",
        icon: "✨",
        color: "yellow",
        link: "/ai-writer",
        priority: 6
      });
    }

    return actions.slice(0, 3); // Show max 3 actions
  };

  const suggestedActions = getSuggestedActions();

  const getColorClasses = (color: string) => {
    const colorMap = {
      red: "bg-red-50 border-red-200 text-red-800 hover:bg-red-100",
      blue: "bg-blue-50 border-blue-200 text-blue-800 hover:bg-blue-100",
      purple: "bg-purple-50 border-purple-200 text-purple-800 hover:bg-purple-100",
      green: "bg-green-50 border-green-200 text-green-800 hover:bg-green-100",
      indigo: "bg-indigo-50 border-indigo-200 text-indigo-800 hover:bg-indigo-100",
      yellow: "bg-yellow-50 border-yellow-200 text-yellow-800 hover:bg-yellow-100"
    };
    return colorMap[color as keyof typeof colorMap] || colorMap.indigo;
  };

  if (suggestedActions.length === 0) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center">
          <span className="text-2xl mr-3">🎉</span>
          <div>
            <h3 className="font-medium text-green-900">You're all set up!</h3>
            <p className="text-green-700 text-sm mt-1">
              You have texts, agents, and contests. Keep exploring and creating!
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Suggested Actions</h3>
        <span className="text-sm text-gray-500">Get started quickly</span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {suggestedActions.map((action, index) => (
          <Link
            key={index}
            to={action.link}
            className={`block p-4 rounded-lg border-2 transition-all duration-200 ${getColorClasses(action.color)}`}
          >
            <div className="flex items-start space-x-3">
              <span className="text-2xl flex-shrink-0">{action.icon}</span>
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-sm mb-1">{action.title}</h4>
                <p className="text-xs opacity-90 leading-relaxed">{action.description}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Quick stats */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-indigo-600">{user?.credits || 0}</div>
            <div className="text-xs text-gray-500">Credits Available</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-600">{hasTexts ? "✓" : "0"}</div>
            <div className="text-xs text-gray-500">Texts Created</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-600">{hasContests ? "✓" : "0"}</div>
            <div className="text-xs text-gray-500">Contests Joined</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-600">{hasAgents ? "✓" : "0"}</div>
            <div className="text-xs text-gray-500">AI Agents</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickActions; 