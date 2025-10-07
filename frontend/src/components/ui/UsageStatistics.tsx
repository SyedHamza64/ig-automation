import React from 'react';
import { useQuery } from '@tanstack/react-query';
import type { LimitsData } from '../../api/limits';
import { listRecentLogs } from '../../api/logs';

interface UsageData {
  follows: { used: number; limit: number; hourlyUsed: number; hourlyLimit: number };
  likes: { used: number; limit: number; hourlyUsed: number; hourlyLimit: number };
  dms: { used: number; limit: number; hourlyUsed: number; hourlyLimit: number };
  unfollows: { used: number; limit: number; hourlyUsed: number; hourlyLimit: number };
  comments: { used: number; limit: number; hourlyUsed: number; hourlyLimit: number };
  stories: { used: number; limit: number; hourlyUsed: number; hourlyLimit: number };
}

interface UsageStatisticsProps {
  accountId: number;
  limits: LimitsData;
  className?: string;
}

export const UsageStatistics: React.FC<UsageStatisticsProps> = ({ 
  accountId, 
  limits, 
  className = "" 
}) => {
  // Get today's date for filtering
  const today = new Date().toISOString().split('T')[0];
  
  // Fetch recent logs (same as Actions page)
  const { data: recentLogs = [], isLoading: logsLoading } = useQuery({
    queryKey: ["recent-logs"],
    queryFn: () => listRecentLogs(100),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Note: We're not using account stats anymore since they were incorrect
  // const { data: accountStats, isLoading: statsLoading } = useQuery({
  //   queryKey: ["account-stats", accountId],
  //   queryFn: () => getAccountStats(accountId, 1), // Get last 1 day
  //   refetchInterval: 30000,
  // });

  // Calculate today's usage from recent logs (filtered by account)
  const calculateTodayUsage = () => {
    const todayActions = recentLogs.filter((log: any) => {
      const actionDate = new Date(log.created_at).toISOString().split('T')[0];
      return actionDate === today && 
             log.status === 'success' && 
             log.account_id === accountId;
    });

    // Calculate hourly usage (last hour)
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    const hourlyActions = recentLogs.filter((log: any) => {
      const actionTime = new Date(log.created_at);
      return actionTime >= oneHourAgo && 
             log.status === 'success' && 
             log.account_id === accountId;
    });


    const dailyUsage = {
      follows: 0,
      likes: 0,
      dms: 0,
      unfollows: 0,
      comments: 0,
      stories: 0,
    };

    const hourlyUsage = {
      follows: 0,
      likes: 0,
      dms: 0,
      unfollows: 0,
      comments: 0,
      stories: 0,
    };

    // Process daily actions
    todayActions.forEach((log: any) => {
      const result = log.result || log.payload?.result;
      const actedCount = result?.acted || 0;
      
      if (log.action === 'mass_follow' || (log.action === 'follow' && actedCount > 0)) {
        dailyUsage.follows += actedCount;
      } else if (log.action === 'mass_unfollow' || (log.action === 'unfollow' && actedCount > 0)) {
        dailyUsage.unfollows += actedCount;
      } else {
        switch (log.action) {
          case 'follow':
            dailyUsage.follows++;
            break;
          case 'unfollow':
            dailyUsage.unfollows++;
            break;
          case 'like':
          case 'like-recent':
            dailyUsage.likes++;
            break;
          case 'dm':
            dailyUsage.dms++;
            break;
          case 'comment':
            dailyUsage.comments++;
            break;
          case 'story':
            dailyUsage.stories++;
            break;
        }
      }
    });

    // Process hourly actions
    hourlyActions.forEach((log: any) => {
      const result = log.result || log.payload?.result;
      const actedCount = result?.acted || 0;
      
      if (log.action === 'mass_follow' || (log.action === 'follow' && actedCount > 0)) {
        hourlyUsage.follows += actedCount;
      } else if (log.action === 'mass_unfollow' || (log.action === 'unfollow' && actedCount > 0)) {
        hourlyUsage.unfollows += actedCount;
      } else {
        switch (log.action) {
          case 'follow':
            hourlyUsage.follows++;
            break;
          case 'unfollow':
            hourlyUsage.unfollows++;
            break;
          case 'like':
          case 'like-recent':
            hourlyUsage.likes++;
            break;
          case 'dm':
            hourlyUsage.dms++;
            break;
          case 'comment':
            hourlyUsage.comments++;
            break;
          case 'story':
            hourlyUsage.stories++;
            break;
        }
      }
    });


    return { dailyUsage, hourlyUsage };
  };

  const { dailyUsage, hourlyUsage } = calculateTodayUsage();

  // Use calculated usage (from recent logs) instead of account stats
  // Account stats might be outdated or incorrect
  const usageData: UsageData = {
    follows: { 
      used: dailyUsage.follows, 
      limit: limits.follow.per_day,
      hourlyUsed: hourlyUsage.follows,
      hourlyLimit: limits.follow.per_hour
    },
    likes: { 
      used: dailyUsage.likes, 
      limit: limits.like.per_day,
      hourlyUsed: hourlyUsage.likes,
      hourlyLimit: limits.like.per_hour
    },
    dms: { 
      used: dailyUsage.dms, 
      limit: limits.dm.per_day,
      hourlyUsed: hourlyUsage.dms,
      hourlyLimit: limits.dm.per_hour
    },
    unfollows: { 
      used: dailyUsage.unfollows, 
      limit: limits.unfollow.per_day,
      hourlyUsed: hourlyUsage.unfollows,
      hourlyLimit: limits.unfollow.per_hour
    },
    comments: { 
      used: dailyUsage.comments, 
      limit: 50, // Default limit for comments
      hourlyUsed: hourlyUsage.comments,
      hourlyLimit: 10 // Default hourly limit for comments
    },
    stories: { 
      used: dailyUsage.stories, 
      limit: 20, // Default limit for stories
      hourlyUsed: hourlyUsage.stories,
      hourlyLimit: 5 // Default hourly limit for stories
    },
  };

  const getProgressColor = (percentage: number): string => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    if (percentage >= 50) return 'bg-blue-500';
    return 'bg-green-500';
  };

  const getProgressBgColor = (percentage: number): string => {
    if (percentage >= 90) return 'bg-red-100 dark:bg-red-900/20';
    if (percentage >= 75) return 'bg-yellow-100 dark:bg-yellow-900/20';
    if (percentage >= 50) return 'bg-blue-100 dark:bg-blue-900/20';
    return 'bg-green-100 dark:bg-green-900/20';
  };

  const StatCard = ({ 
    title, 
    used, 
    limit, 
    hourlyUsed,
    hourlyLimit,
    color, 
    icon 
  }: { 
    title: string; 
    used: number; 
    limit: number; 
    hourlyUsed: number;
    hourlyLimit: number;
    color: string; 
    icon: string;
  }) => {
    const dailyPercentage = limit > 0 ? (used / limit) * 100 : 0;
    const hourlyPercentage = hourlyLimit > 0 ? (hourlyUsed / hourlyLimit) * 100 : 0;
    const dailyProgressColor = getProgressColor(dailyPercentage);
    const hourlyProgressColor = getProgressColor(hourlyPercentage);
    const bgColor = getProgressBgColor(dailyPercentage);

    return (
      <div className={`${bgColor} rounded-lg p-4 border border-gray-200 dark:border-gray-700`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{icon}</span>
            <h4 className="font-medium text-gray-900 dark:text-white">{title}</h4>
          </div>
          <div className="text-right">
            <div className={`text-sm font-semibold ${color}`}>
              {used}/{limit}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {hourlyUsed}/{hourlyLimit} per hour
            </div>
          </div>
        </div>
        
        {/* Daily Progress */}
        <div className="mb-3">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-600 dark:text-gray-400">Daily</span>
            <span className="text-gray-600 dark:text-gray-400">{Math.round(dailyPercentage)}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={`${dailyProgressColor} h-2 rounded-full transition-all duration-300`}
              style={{ width: `${Math.min(100, dailyPercentage)}%` }}
            ></div>
          </div>
        </div>

        {/* Hourly Progress */}
        <div className="mb-2">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-600 dark:text-gray-400">Hourly</span>
            <span className="text-gray-600 dark:text-gray-400">{Math.round(hourlyPercentage)}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
            <div
              className={`${hourlyProgressColor} h-1.5 rounded-full transition-all duration-300`}
              style={{ width: `${Math.min(100, hourlyPercentage)}%` }}
            ></div>
          </div>
        </div>
        
        <div className="text-xs text-gray-500 dark:text-gray-400">
          {limit - used} remaining today • {hourlyLimit - hourlyUsed} remaining this hour
        </div>
      </div>
    );
  };

  if (logsLoading) {
    return (
      <div className={`p-6 bg-white dark:bg-gray-800 rounded-lg shadow ${className}`}>
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Usage Statistics - Account {accountId}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Loading usage data...
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4 animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded mb-2"></div>
              <div className="h-6 bg-gray-200 dark:bg-gray-600 rounded mb-2"></div>
              <div className="h-2 bg-gray-200 dark:bg-gray-600 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`p-6 bg-white dark:bg-gray-800 rounded-lg shadow ${className}`}>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Usage Statistics - Account {accountId}
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Daily usage vs limits (resets at midnight) • {recentLogs.length} recent logs analyzed
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          title="Follows"
          used={usageData.follows.used}
          limit={usageData.follows.limit}
          hourlyUsed={usageData.follows.hourlyUsed}
          hourlyLimit={usageData.follows.hourlyLimit}
          color="text-blue-600"
          icon="👥"
        />
        <StatCard
          title="Likes"
          used={usageData.likes.used}
          limit={usageData.likes.limit}
          hourlyUsed={usageData.likes.hourlyUsed}
          hourlyLimit={usageData.likes.hourlyLimit}
          color="text-red-600"
          icon="❤️"
        />
        <StatCard
          title="DMs"
          used={usageData.dms.used}
          limit={usageData.dms.limit}
          hourlyUsed={usageData.dms.hourlyUsed}
          hourlyLimit={usageData.dms.hourlyLimit}
          color="text-purple-600"
          icon="💬"
        />
        <StatCard
          title="Unfollows"
          used={usageData.unfollows.used}
          limit={usageData.unfollows.limit}
          hourlyUsed={usageData.unfollows.hourlyUsed}
          hourlyLimit={usageData.unfollows.hourlyLimit}
          color="text-orange-600"
          icon="👋"
        />
        <StatCard
          title="Comments"
          used={usageData.comments.used}
          limit={usageData.comments.limit}
          hourlyUsed={usageData.comments.hourlyUsed}
          hourlyLimit={usageData.comments.hourlyLimit}
          color="text-green-600"
          icon="💭"
        />
        <StatCard
          title="Stories"
          used={usageData.stories.used}
          limit={usageData.stories.limit}
          hourlyUsed={usageData.stories.hourlyUsed}
          hourlyLimit={usageData.stories.hourlyLimit}
          color="text-pink-600"
          icon="📱"
        />
      </div>

      {/* Recent Actions Summary */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
          Actions Summary
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {dailyUsage.follows}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Follows Today
            </div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {dailyUsage.unfollows}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Unfollows Today
            </div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {dailyUsage.likes}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Likes Today
            </div>
          </div>
        </div>
        <div className="mt-3 grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {hourlyUsage.follows}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Follows This Hour
            </div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {hourlyUsage.unfollows}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Unfollows This Hour
            </div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {hourlyUsage.likes}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Likes This Hour
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-gray-600 dark:text-gray-400">Low usage (0-50%)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-gray-600 dark:text-gray-400">Medium usage (50-75%)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <span className="text-gray-600 dark:text-gray-400">High usage (75-90%)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span className="text-gray-600 dark:text-gray-400">Near limit (90%+)</span>
            </div>
          </div>
          <span className="text-gray-500 dark:text-gray-400">
            Last updated: {new Date().toLocaleTimeString()}
          </span>
        </div>
      </div>
    </div>
  );
};

export default UsageStatistics;

