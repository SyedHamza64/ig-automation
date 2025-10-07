// frontend/src/components/ui/LimitsForm.tsx

import { LimitCard, LimitInput, LimitCheckbox, LimitRange } from "./LimitCard";
import { type LimitsData } from "../../api/limits";

interface LimitsFormProps {
  limits: LimitsData;
  onChange: (limits: LimitsData) => void;
  className?: string;
}

export function LimitsForm({ limits, onChange, className = "" }: LimitsFormProps) {
  const updateLimit = (path: string, value: any) => {
    const newLimits = { ...limits };
    const keys = path.split('.');
    let current: any = newLimits;
    
    for (let i = 0; i < keys.length - 1; i++) {
      current = current[keys[i]];
    }
    
    current[keys[keys.length - 1]] = value;
    onChange(newLimits);
  };

  const updateRange = (path: string, index: number, value: number) => {
    const newLimits = { ...limits };
    const keys = path.split('.');
    let current: any = newLimits;
    
    for (let i = 0; i < keys.length - 1; i++) {
      current = current[keys[i]];
    }
    
    const array = [...current[keys[keys.length - 1]]];
    array[index] = value;
    current[keys[keys.length - 1]] = array;
    onChange(newLimits);
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Follow & Unfollow Limits */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LimitCard 
          title="Follow Limits" 
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
            </svg>
          }
        >
          <LimitInput
            label="Per Hour"
            value={limits.follow.per_hour}
            onChange={(value) => updateLimit('follow.per_hour', value)}
            min={0}
            max={1000}
            unit="actions"
          />
          <LimitInput
            label="Per Day"
            value={limits.follow.per_day}
            onChange={(value) => updateLimit('follow.per_day', value)}
            min={0}
            max={10000}
            unit="actions"
          />
          <LimitCheckbox
            label="Enable Warmup"
            checked={limits.follow.warmup ?? false}
            onChange={(checked) => updateLimit('follow.warmup', checked)}
            description="Gradually increase follow rate for new accounts"
          />
        </LimitCard>

        <LimitCard 
          title="Unfollow Limits" 
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          }
        >
          <LimitInput
            label="Per Hour"
            value={limits.unfollow.per_hour}
            onChange={(value) => updateLimit('unfollow.per_hour', value)}
            min={0}
            max={1000}
            unit="actions"
          />
          <LimitInput
            label="Per Day"
            value={limits.unfollow.per_day}
            onChange={(value) => updateLimit('unfollow.per_day', value)}
            min={0}
            max={10000}
            unit="actions"
          />
        </LimitCard>
      </div>

      {/* Like & DM Limits */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LimitCard 
          title="Like Limits" 
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          }
        >
          <LimitInput
            label="Per Hour"
            value={limits.like.per_hour}
            onChange={(value) => updateLimit('like.per_hour', value)}
            min={0}
            max={1000}
            unit="actions"
          />
          <LimitInput
            label="Per Day"
            value={limits.like.per_day}
            onChange={(value) => updateLimit('like.per_day', value)}
            min={0}
            max={10000}
            unit="actions"
          />
        </LimitCard>

        <LimitCard 
          title="DM Limits" 
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          }
        >
          <LimitInput
            label="Per Hour"
            value={limits.dm.per_hour}
            onChange={(value) => updateLimit('dm.per_hour', value)}
            min={0}
            max={1000}
            unit="actions"
          />
          <LimitInput
            label="Per Day"
            value={limits.dm.per_day}
            onChange={(value) => updateLimit('dm.per_day', value)}
            min={0}
            max={10000}
            unit="actions"
          />
        </LimitCard>
      </div>

      {/* Timing Settings */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LimitCard 
          title="Timing Settings" 
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        >
          <LimitRange
            label="Random Delay"
            minValue={limits.random_delay_ms[0]}
            maxValue={limits.random_delay_ms[1]}
            onMinChange={(value) => updateRange('random_delay_ms', 0, value)}
            onMaxChange={(value) => updateRange('random_delay_ms', 1, value)}
            min={0}
            max={10000}
            step={100}
            unit="ms"
          />
        </LimitCard>

        <LimitCard 
          title="Block Settings" 
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728" />
            </svg>
          }
        >
          <LimitInput
            label="Block Cooldown"
            value={limits.block_cooldown_minutes}
            onChange={(value) => updateLimit('block_cooldown_minutes', value)}
            min={0}
            max={1440}
            unit="minutes"
          />
        </LimitCard>
      </div>
    </div>
  );
}
