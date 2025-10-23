import React from 'react';

interface LoaderProps {
  message: string;
}

const Loader: React.FC<LoaderProps> = ({ message }) => {
  return (
    <div className="absolute inset-0 bg-base-100/80 backdrop-blur-sm flex flex-col items-center justify-center z-20 rounded-lg">
      <div className="w-12 h-12 border-4 border-base-300 border-t-brand-primary rounded-full animate-spin"></div>
      <p className="mt-4 text-base-content font-semibold text-center px-4">{message}</p>
    </div>
  );
};

export default Loader;
