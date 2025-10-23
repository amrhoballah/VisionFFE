import React from 'react';
import { ExtractedItem } from '../types';
import { CheckCircleIcon } from './Icons';

interface ItemCardProps {
  item: ExtractedItem;
  isSelected: boolean;
  onSelect: (id: string) => void;
}

const ItemCard: React.FC<ItemCardProps> = ({ item, isSelected, onSelect }) => {
  const imageUrl = `data:image/png;base64,${item.imageBase64}`;

  return (
    <div
      onClick={() => onSelect(item.id)}
      className={`group relative bg-base-200 rounded-lg overflow-hidden shadow-lg transition-all duration-300 hover:scale-105 cursor-pointer
        ${isSelected ? 'ring-2 ring-brand-primary' : ''}
      `}
      aria-pressed={isSelected}
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
  );
};

export default ItemCard;