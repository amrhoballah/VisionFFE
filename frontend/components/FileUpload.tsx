import React, { useCallback, useState } from 'react';
import { UploadIcon } from './Icons';

interface FileUploadProps {
  onFileUpload: (files: FileList) => void;
  isLoading: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUpload, isLoading }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(e.target.files);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileUpload(e.dataTransfer.files);
    }
  }, [onFileUpload]);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  }, [isDragging]);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const openFileDialog = () => {
    document.getElementById('file-upload-input')?.click();
  };

  return (
    <div
      className={`relative w-full max-w-2xl mx-auto border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
        isDragging ? 'border-brand-primary bg-base-200' : 'border-base-300'
      } ${isLoading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer hover:border-brand-secondary'}`}
      onDrop={isLoading ? undefined : handleDrop}
      onDragOver={isLoading ? undefined : handleDragOver}
      onDragLeave={isLoading ? undefined : handleDragLeave}
      onClick={isLoading ? undefined : openFileDialog}
    >
      <input
        type="file"
        id="file-upload-input"
        className="hidden"
        onChange={handleFileChange}
        accept="image/png, image/jpeg, image/webp"
        disabled={isLoading}
        multiple
      />
      <div className="flex flex-col items-center justify-center space-y-4 text-base-content/70">
        <UploadIcon className="w-12 h-12" />
        <p className="font-semibold">
          <span className="text-brand-primary">Click to upload images</span> or drag and drop
        </p>
        <p className="text-sm">Provide multiple angles for better results</p>
        <p className="text-xs text-base-content/50">PNG, JPG, or WEBP supported</p>
      </div>
    </div>
  );
};

export default FileUpload;