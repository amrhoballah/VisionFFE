import React, { useState } from 'react';
import { ExtractedItem } from '../types';
import { CheckCircleIcon } from './Icons';

interface ItemCardProps {
  item: ExtractedItem;
  isSelected: boolean;
  onSelect: (id: string) => void;
}

const ItemCard: React.FC<ItemCardProps> = ({ item, isSelected, onSelect }) => {
  const [showResults, setShowResults] = useState(false);
  const imageUrl = `data:image/png;base64,${item.imageBase64}`;

  return (
    <div className="relative">
      <div
        onClick={() => onSelect(item.id)}
        className={`group relative bg-base-200 rounded-lg overflow-hidden shadow-lg transition-all duration-300 hover:scale-105 cursor-pointer
          ${isSelected ? 'ring-2 ring-brand-primary' : ''}
        `}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => (e.key === ' ' || e.key === 'Enter') && onSelect(item.id)}
      >
        {isSelected && (
          <div className="absolute top-2 right-2 z-10">
            <CheckCircleIcon className="w-6 h-6 text-brand-primary bg-white rounded-full" />
          </div>
        )}
        <div className="aspect-w-1 aspect-h-1 w-full bg-transparent flex items-center justify-center p-4">
          <img
            src={imageUrl}
            alt={item.name}
            className="w-full h-full object-contain"
          />
        </div>
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
          <h3 className="text-sm font-medium text-white truncate capitalize">{item.name}</h3>
        </div>
      </div>
      
      {/* Search Results Section */}
      {item.searchResults && item.searchResults.length > 0 && (
        <div className="mt-4 bg-base-200 rounded-lg shadow-lg p-4">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowResults(!showResults);
            }}
            className="w-full text-left flex items-center justify-between mb-2 text-sm font-semibold text-base-content"
          >
            <span>Similar Items ({item.searchResults.length})</span>
            <span className="text-base-content/70">{showResults ? '▲' : '▼'}</span>
          </button>
          
          {showResults && (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {item.searchResults.map((result, index) => (
                <div
                  key={`${result.id}-${index}`}
                  className="bg-base-300 rounded-md p-3 text-sm"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-base-content truncate">{result.filename || 'Item'}</span>
                    <span className="text-brand-primary font-semibold">
                      {(result.similarity_score * 100).toFixed(1)}%
                    </span>
                  </div>
                  {result.image_path && (
                    <a
                      href={result.image_path}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:underline text-xs"
                    >
                      View Image
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ItemCard;