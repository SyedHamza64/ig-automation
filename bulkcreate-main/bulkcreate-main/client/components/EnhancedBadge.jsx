import React, { memo } from 'react';

const EnhancedBadge = memo(() => {
  // Fixed dimensions to prevent flickering
  const badgeWidth = 60; // Approximate width of "Enhanced" text
  const badgeHeight = 20; // Approximate height
  const loopPadding = 8;
  const loopWidth = badgeWidth + (loopPadding * 2);
  const loopHeight = badgeHeight + (loopPadding * 2);
  
  // Pre-calculated infinity symbol path
  const centerX = loopWidth / 2;
  const centerY = loopHeight / 2;
  const radius = Math.min(loopWidth, loopHeight) / 4;
  
  const leftCircleX = centerX - radius * 0.6;
  const rightCircleX = centerX + radius * 0.6;
  
  const infinityPath = `
    M ${leftCircleX} ${centerY}
    C ${leftCircleX - radius} ${centerY - radius * 0.8} ${leftCircleX - radius} ${centerY + radius * 0.8} ${leftCircleX} ${centerY + radius}
    C ${leftCircleX + radius * 0.3} ${centerY + radius * 1.2} ${rightCircleX - radius * 0.3} ${centerY + radius * 1.2} ${rightCircleX} ${centerY + radius}
    C ${rightCircleX + radius} ${centerY + radius * 0.8} ${rightCircleX + radius} ${centerY - radius * 0.8} ${rightCircleX} ${centerY - radius}
    C ${rightCircleX - radius * 0.3} ${centerY - radius * 1.2} ${leftCircleX + radius * 0.3} ${centerY - radius * 1.2} ${leftCircleX} ${centerY - radius}
    Z
  `;

  return (
    <div className="relative inline-flex items-center group cursor-pointer">
      {/* Infinity loop container */}
      <div className="relative">
        {/* Infinity loop SVG that wraps around the badge */}
        <svg
          className="absolute animate-spin opacity-70 group-hover:opacity-100 group-hover:animate-pulse transition-all duration-300"
          style={{ 
            animationDuration: '3s',
            width: loopWidth,
            height: loopHeight,
            left: -loopPadding,
            top: -loopPadding,
            zIndex: 1
          }}
          fill="none"
          viewBox={`0 0 ${loopWidth} ${loopHeight}`}
        >
          <defs>
            <linearGradient id="infinity-gradient-enhanced" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#3B82F6" />
              <stop offset="25%" stopColor="#8B5CF6" />
              <stop offset="50%" stopColor="#F59E0B" />
              <stop offset="75%" stopColor="#EF4444" />
              <stop offset="100%" stopColor="#3B82F6" />
            </linearGradient>
            <linearGradient id="infinity-gradient-hover" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#60A5FA" />
              <stop offset="25%" stopColor="#A78BFA" />
              <stop offset="50%" stopColor="#FBBF24" />
              <stop offset="75%" stopColor="#F87171" />
              <stop offset="100%" stopColor="#60A5FA" />
            </linearGradient>
          </defs>
          <path
            d={infinityPath}
            stroke="url(#infinity-gradient-enhanced)"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
            className="group-hover:stroke-[url(#infinity-gradient-hover)] group-hover:stroke-[2] transition-all duration-300"
          />
        </svg>
        
        {/* Badge container - smaller size with hover effects */}
        <div 
          className="relative px-1.5 py-0.5 rounded text-xs bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-400/30 backdrop-blur-sm group-hover:from-blue-500/20 group-hover:to-purple-500/20 group-hover:border-yellow-400/50 group-hover:shadow-lg group-hover:shadow-yellow-400/20 group-hover:scale-105 transition-all duration-300"
          style={{ zIndex: 2 }}
        >
          {/* Badge text with golden gradient and hover effects */}
          <span className="font-medium bg-gradient-to-r from-yellow-400 via-yellow-300 to-yellow-500 text-transparent bg-clip-text group-hover:from-yellow-300 group-hover:via-yellow-200 group-hover:to-yellow-400 group-hover:text-yellow-200 transition-all duration-300">
            Enhanced
          </span>
        </div>
        
        {/* Floating particles around the badge - enhanced on hover */}
        <div className="absolute -top-1 -right-1 w-0.5 h-0.5 bg-yellow-400 rounded-full animate-bounce opacity-60 group-hover:opacity-100 group-hover:bg-yellow-300 group-hover:w-1 group-hover:h-1 transition-all duration-300" style={{ animationDelay: '0s', animationDuration: '2s', zIndex: 3 }}></div>
        <div className="absolute -bottom-1 -left-1 w-0.5 h-0.5 bg-blue-400 rounded-full animate-bounce opacity-60 group-hover:opacity-100 group-hover:bg-blue-300 group-hover:w-1 group-hover:h-1 transition-all duration-300" style={{ animationDelay: '1s', animationDuration: '2s', zIndex: 3 }}></div>
        <div className="absolute -top-0.5 -left-0.5 w-0.5 h-0.5 bg-purple-400 rounded-full animate-bounce opacity-40 group-hover:opacity-80 group-hover:bg-purple-300 group-hover:w-0.75 group-hover:h-0.75 transition-all duration-300" style={{ animationDelay: '0.5s', animationDuration: '1.5s', zIndex: 3 }}></div>
        <div className="absolute -bottom-0.5 -right-0.5 w-0.5 h-0.5 bg-pink-400 rounded-full animate-bounce opacity-40 group-hover:opacity-80 group-hover:bg-pink-300 group-hover:w-0.75 group-hover:h-0.75 transition-all duration-300" style={{ animationDelay: '1.5s', animationDuration: '1.8s', zIndex: 3 }}></div>
        
        {/* Additional hover particles that appear on hover */}
        <div className="absolute -top-2 -right-2 w-0.5 h-0.5 bg-cyan-400 rounded-full opacity-0 group-hover:opacity-60 group-hover:animate-bounce transition-all duration-500" style={{ animationDelay: '0.2s', animationDuration: '1.2s', zIndex: 3 }}></div>
        <div className="absolute -bottom-2 -left-2 w-0.5 h-0.5 bg-emerald-400 rounded-full opacity-0 group-hover:opacity-60 group-hover:animate-bounce transition-all duration-500" style={{ animationDelay: '0.8s', animationDuration: '1.4s', zIndex: 3 }}></div>
        <div className="absolute -top-1 -left-2 w-0.5 h-0.5 bg-orange-400 rounded-full opacity-0 group-hover:opacity-60 group-hover:animate-bounce transition-all duration-500" style={{ animationDelay: '0.4s', animationDuration: '1.6s', zIndex: 3 }}></div>
        <div className="absolute -bottom-1 -right-2 w-0.5 h-0.5 bg-rose-400 rounded-full opacity-0 group-hover:opacity-60 group-hover:animate-bounce transition-all duration-500" style={{ animationDelay: '1.2s', animationDuration: '1.8s', zIndex: 3 }}></div>
        
        {/* Glow effect that appears on hover */}
        <div className="absolute -inset-3 rounded-lg bg-gradient-to-r from-yellow-400/10 via-blue-400/10 to-purple-400/10 opacity-0 group-hover:opacity-100 group-hover:animate-pulse blur-sm transition-all duration-300" style={{ zIndex: 0 }}></div>
        
        {/* Tooltip-like effect */}
        <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-slate-800 text-white text-xs px-2 py-1 rounded shadow-lg opacity-0 group-hover:opacity-100 group-hover:-translate-y-1 transition-all duration-300 whitespace-nowrap z-50">
          Advanced Anti-Detection
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-2 border-r-2 border-t-2 border-transparent border-t-slate-800"></div>
        </div>
      </div>
    </div>
  );
});

EnhancedBadge.displayName = 'EnhancedBadge';

export default EnhancedBadge;
