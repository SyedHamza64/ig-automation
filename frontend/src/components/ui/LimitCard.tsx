// frontend/src/components/ui/LimitCard.tsx

import React from "react";

interface LimitCardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
  icon?: React.ReactNode;
}

export function LimitCard({ title, children, className = "", icon }: LimitCardProps) {
  return (
    <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 ${className}`}>
      <div className="flex items-center space-x-2 mb-3">
        {icon && <div className="text-gray-500 dark:text-gray-400">{icon}</div>}
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
      </div>
      <div className="space-y-3">
        {children}
      </div>
    </div>
  );
}

interface LimitInputProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  className?: string;
}

export function LimitInput({ 
  label, 
  value, 
  onChange, 
  min = 0, 
  max = 10000, 
  step = 1, 
  unit = "", 
  className = "" 
}: LimitInputProps) {
  const increment = () => {
    const newValue = Math.min(value + step, max);
    onChange(newValue);
  };

  const decrement = () => {
    const newValue = Math.max(value - step, min);
    onChange(newValue);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = Number(e.target.value);
    if (!isNaN(newValue) && newValue >= min && newValue <= max) {
      onChange(newValue);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      increment();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      decrement();
    }
  };

  return (
    <div className={`space-y-1 ${className}`}>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>
      
      {/* Clean input with integrated +/- buttons */}
      <div className="relative">
        <input
          type="number"
          value={value}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          min={min}
          max={max}
          step={step}
          className="w-full px-3 py-2 pr-16 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
        />
        
        {/* Integrated increment/decrement buttons */}
        <div className="absolute right-1 top-1/2 transform -translate-y-1/2 flex flex-col">
          <button
            type="button"
            onClick={increment}
            disabled={value >= max}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm hover:bg-gray-100 dark:hover:bg-gray-600"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
          <button
            type="button"
            onClick={decrement}
            disabled={value <= min}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm hover:bg-gray-100 dark:hover:bg-gray-600"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
        </div>

        {unit && (
          <div className="absolute right-12 top-1/2 transform -translate-y-1/2 text-sm text-gray-500 dark:text-gray-400">
            {unit}
          </div>
        )}
      </div>
    </div>
  );
}

interface LimitCheckboxProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  description?: string;
  className?: string;
}

export function LimitCheckbox({ 
  label, 
  checked, 
  onChange, 
  description, 
  className = "" 
}: LimitCheckboxProps) {
  return (
    <div className={`space-y-1 ${className}`}>
      <label className="flex items-start space-x-3 cursor-pointer">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="mt-1 h-4 w-4 text-blue-600 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500 dark:bg-gray-700"
        />
        <div className="flex-1">
          <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {label}
          </div>
          {description && (
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {description}
            </div>
          )}
        </div>
      </label>
    </div>
  );
}

interface LimitRangeProps {
  label: string;
  minValue: number;
  maxValue: number;
  onMinChange: (value: number) => void;
  onMaxChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  className?: string;
}

export function LimitRange({ 
  label, 
  minValue, 
  maxValue, 
  onMinChange, 
  onMaxChange, 
  min = 0, 
  max = 10000, 
  step = 1, 
  unit = "", 
  className = "" 
}: LimitRangeProps) {
  const handleMinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = Number(e.target.value);
    if (!isNaN(newValue) && newValue >= min && newValue <= maxValue - step) {
      onMinChange(newValue);
    }
  };

  const handleMaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = Number(e.target.value);
    if (!isNaN(newValue) && newValue >= minValue + step && newValue <= max) {
      onMaxChange(newValue);
    }
  };

  return (
    <div className={`space-y-1 ${className}`}>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>
      
      {/* Clean range input */}
      <div className="flex items-center space-x-2">
        <div className="relative flex-1">
          <input
            type="number"
            value={minValue}
            onChange={handleMinChange}
            min={min}
            max={maxValue - step}
            step={step}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
            placeholder="Min"
          />
        </div>
        <span className="text-gray-500 dark:text-gray-400">-</span>
        <div className="relative flex-1">
          <input
            type="number"
            value={maxValue}
            onChange={handleMaxChange}
            min={minValue + step}
            max={max}
            step={step}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
            placeholder="Max"
          />
        </div>
        {unit && (
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {unit}
          </div>
        )}
      </div>
    </div>
  );
}
