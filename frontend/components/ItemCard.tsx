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
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {item.searchResults.map((result, index) => (
                <div
                  key={`${result.id}-${index}`}
                  className="bg-base-300 rounded-md p-3 hover:bg-base-400 transition-colors"
                >
                  <div className="flex gap-3">
                    {/* Image */}
                    {result.metadata?.image_url && (
                      <div className="flex-shrink-0">
                        <img
                          src={result.metadata?.image_urlh}
                          alt={result.metadata?.title || result.filename}
                          className="w-20 h-20 object-cover rounded-md bg-base-200"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      </div>
                    )}
                    
                    {/* Content */}
                    <div className="flex-grow min-w-0">
                      {/* Title */}
                      {result.metadata?.title && (
                        <h4 className="font-semibold text-base-content truncate mb-1">
                          {result.metadata.title}
                        </h4>
                      )}
                      
                      {/* Brand */}
                      {result.metadata?.brand && (
                        <p className="text-sm text-base-content/70 mb-1">
                          Brand: {result.metadata.brand}
                        </p>
                      )}
                      
                      {/* Price */}
                      {result.metadata?.price && (
                        <p className="text-sm font-semibold text-brand-primary mb-1">
                          ${typeof result.metadata.price === 'string' 
                            ? result.metadata.price 
                            : result.metadata.price.toFixed(2)}
                        </p>
                      )}
                      
                      {/* Similarity Score */}
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-base-content/60">
                          {result.filename || 'Item'}
                        </span>
                        <span className="text-xs font-semibold text-brand-primary bg-brand-primary/10 px-2 py-1 rounded">
                          {(result.similarity_score * 100).toFixed(1)}% match
                        </span>
                      </div>
                    </div>
                  </div>
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