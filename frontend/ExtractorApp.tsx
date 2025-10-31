import React, { useState, useCallback, useEffect, useRef } from 'react';
import { ExtractedItem } from './types';
import { identifyItems, extractItemImage } from './services/geminiService';
import { authService } from './services/authService';
import { useAuth } from './contexts/AuthContext';
import config from './config';
import FileUpload from './components/FileUpload';
import ItemCard from './components/ItemCard';
import Loader from './components/Loader';
import { DownloadIcon, ResetIcon, ImageIcon, SendIcon, XIcon } from './components/Icons';
import { deleteProjectPhoto } from './services/projectService';

// Declare JSZip for TypeScript since it's loaded from a CDN
declare var JSZip: any;

interface ExtractorAppProps {
  projectId: string;
  projectName: string;
  onChangeProject: () => void;
}

const ExtractorApp: React.FC<ExtractorAppProps> = ({ projectId, projectName, onChangeProject }) => {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [uploadedImagePreviews, setUploadedImagePreviews] = useState<string[]>([]);
  const [extractedItems, setExtractedItems] = useState<ExtractedItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingMessage, setLoadingMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [selectedItemIds, setSelectedItemIds] = useState<Set<string>>(new Set());
  const [isSending, setIsSending] = useState<boolean>(false);
  const [apiFeedback, setApiFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [deletingPhotoUrl, setDeletingPhotoUrl] = useState<string | null>(null);
  
  const { logout, user } = useAuth();
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load existing project data when component mounts or projectId changes
  useEffect(() => {
    const loadProjectData = async () => {
      try {
        const response = await authService.authenticatedFetch(
          `${config.api.baseUrl}/projects/${projectId}`
        );
        if (response.ok) {
          const project = await response.json();
          
          // Load photo URLs and set as previews
          if (project.photo_urls && project.photo_urls.length > 0) {
            setUploadedImagePreviews(project.photo_urls);
          }
          
          // Load extracted items
          if (project.extracted_items && project.extracted_items.length > 0) {
            // Convert extracted items to ExtractedItem format
            const items: ExtractedItem[] = await Promise.all(
              project.extracted_items.map(async (item: any, index: number) => {
                // Fetch image from URL and convert to base64
                let imageBase64 = '';
                try {
                  const imageResponse = await fetch(item.url);
                  const blob = await imageResponse.blob();
                  imageBase64 = await new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onloadend = () => {
                      const base64String = (reader.result as string).split(',')[1];
                      resolve(base64String);
                    };
                    reader.readAsDataURL(blob);
                  });
                } catch (error) {
                  console.error(`Failed to load image from ${item.url}`, error);
                }
                
                return {
                  id: `${item.name.replace(/\s+/g, '-')}-${Date.now()}-${index}`,
                  name: item.name,
                  imageBase64,
                  imageUrl: item.url
                };
              })
            );
            setExtractedItems(items);
          }
        }
      } catch (error) {
        console.error('Failed to load project data', error);
      }
    };

    loadProjectData();
  }, [projectId]);

  const resetState = useCallback(() => {
    setUploadedFiles([]);
    setUploadedImagePreviews(prev => {
        // Only revoke object URLs created locally, not remote URLs from DB
        prev.forEach(url => {
            if (url.startsWith('blob:')) {
                URL.revokeObjectURL(url);
            }
        });
        return [];
    });
    setExtractedItems([]);
    setIsLoading(false);
    setLoadingMessage('');
    setError(null);
    setSelectedItemIds(new Set());
    setIsSending(false);
    setApiFeedback(null);
    setDeletingPhotoUrl(null);
  }, []);

  const handleFileUpload = async (files: FileList) => {
    const fileArray = Array.from(files);
    
    // Append new files instead of replacing
    setUploadedFiles(prev => [...prev, ...fileArray]);
    
    // Create blob URLs for new files and append to previews
    const newBlobUrls = fileArray.map(file => URL.createObjectURL(file));
    setUploadedImagePreviews(prev => [...prev, ...newBlobUrls]);
    
    // Upload to backend project for persistence
    // try {
    //   const form = new FormData();
    //   fileArray.forEach(f => form.append('files', f));
    //   const endpoint = `${config.api.baseUrl}/projects/${projectId}/photos`;
    //   const res = await authService.authenticatedFetch(endpoint, { method: 'POST', body: form });
    //   if (!res.ok) {
    //     // Non-blocking: allow analysis to proceed even if persistence fails
    //     console.warn('Failed to persist photos to project');
    //   } else {
    //     // Update previews with actual URLs from backend
    //     const project = await res.json();
    //     if (project.photo_urls) {
    //       // Revoke the blob URLs we created
    //       newBlobUrls.forEach(url => URL.revokeObjectURL(url));
    //       // Use all URLs from backend
    //       setUploadedImagePreviews(project.photo_urls);
    //     }
    //   }
    // } catch (e) {
    //   console.warn('Upload to project failed', e);
    // }
  };
  
  const runExtractionProcess = useCallback(async () => {
    // Check if we have images to work with
    const hasFiles = uploadedFiles.length > 0;
    const hasUrls = uploadedImagePreviews.some(url => url.startsWith('http'));
    
    if (!hasFiles && !hasUrls) return;

    setIsLoading(true);
    setError(null);
    setExtractedItems([]);
    setApiFeedback(null);
    setSelectedItemIds(new Set());

    try {
      setLoadingMessage('Analyzing room and identifying items...');
      
      let itemNames: string[] = [];
      
      // Use backend identify endpoint if we have URLs or files
      if (hasUrls || hasFiles) {
        const formData = new FormData();
        
        // Add files if we have them
        if (hasFiles) {
          uploadedFiles.forEach(file => {
            formData.append('files', file);
          });
        }
        
        // Add URLs if we have them
        if (hasUrls) {
          const urls = uploadedImagePreviews.filter(url => url.startsWith('http'));
          formData.append('urls', JSON.stringify(urls));
        }
        
        const response = await authService.authenticatedFetch(
          `${config.api.baseUrl}/projects/${projectId}/identify`,
          {
            method: 'POST',
            body: formData,
          }
        );
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Failed to identify items' }));
          throw new Error(errorData.detail || 'Failed to identify items');
        }
        
        const data = await response.json();
        itemNames = data.items || [];
      } else {
        // Fallback to frontend Gemini service
        setLoadingMessage('Preparing images...');
        
        const imagePromises = uploadedFiles.map(file => {
          return new Promise<{base64: string, mimeType: string}>((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onloadend = () => {
              const base64String = (reader.result as string).split(',')[1];
              resolve({ base64: base64String, mimeType: file.type });
            };
            reader.onerror = (error) => reject(error);
          });
        });

        const images = await Promise.all(imagePromises);
        itemNames = await identifyItems(images);
      }

      if (!itemNames || itemNames.length === 0) {
        setError("No items could be identified in the images. Please try different ones.");
        setIsLoading(false);
        return;
      }

      // Prepare images for extraction
      setLoadingMessage('Preparing images for extraction...');
      // let images: {base64: string, mimeType: string}[] = [];
      
      // if (hasFiles) {
      //   // Get base64 from files
      //   const imagePromises = uploadedFiles.map(file => {
      //     return new Promise<{base64: string, mimeType: string}>((resolve, reject) => {
      //       const reader = new FileReader();
      //       reader.readAsDataURL(file);
      //       reader.onloadend = () => {
      //         const base64String = (reader.result as string).split(',')[1];
      //         resolve({ base64: base64String, mimeType: file.type });
      //       };
      //       reader.onerror = (error) => reject(error);
      //     });
      //   });
      //   images = await Promise.all(imagePromises);
      // } else if (hasUrls) {
      //   // For URLs, we need to fetch and convert to base64
      //   const urlList = uploadedImagePreviews.filter(url => url.startsWith('http'));
      //   const imagePromises = urlList.map(async (url) => {
      //     const response = await fetch(url);
      //     const blob = await response.blob();
      //     return new Promise<{base64: string, mimeType: string}>((resolve, reject) => {
      //       const reader = new FileReader();
      //       reader.readAsDataURL(blob);
      //       reader.onloadend = () => {
      //         const base64String = (reader.result as string).split(',')[1];
      //         resolve({ base64: base64String, mimeType: blob.type });
      //       };
      //       reader.onerror = (error) => reject(error);
      //     });
      //   });
      //   images = await Promise.all(imagePromises);
      // }

      const itemsToPersist: { name: string; base64: string }[] = [];
      for (let i = 0; i < itemNames.length; i++) {
        newFormData = formData;
        const name = itemNames[i];
        newFormData.append('item_name', name);
        setLoadingMessage(`Extracting "${name}"... (${i + 1} of ${itemNames.length})`);
        try {
          const itemImageBase64 = await authService.authenticatedFetch(
            `${config.api.baseUrl}/projects/${projectId}/extract`,
            {
              method: 'POST',
              body: formData,
            }
          );
          setExtractedItems(prev => [
            ...prev,
            { id: `${name.replace(/\s+/g, '-')}-${Date.now()}`, name, imageBase64: itemImageBase64 }
          ]);
          // Queue for backend persistence under project
          itemsToPersist.push({ name, base64: itemImageBase64 });
        } catch (extractionError) {
            console.warn(`Could not extract "${name}". Skipping.`);
        }
      }


    } catch (err: any) {
        setError(err.message || 'An unexpected error occurred.');
    } finally {
        setIsLoading(false);
        setLoadingMessage('');
    }
  }, [uploadedFiles, uploadedImagePreviews, projectId]);


  const handleDownloadZip = async () => {
    if (extractedItems.length === 0) return;
    
    const zip = new JSZip();
    const folder = zip.folder("extracted_furniture");

    if (folder) {
        extractedItems.forEach(item => {
            const fileName = `${item.name.replace(/\s+/g, '_')}.png`;
            folder.file(fileName, item.imageBase64, { base64: true });
        });
    }

    zip.generateAsync({ type: "blob" }).then(content => {
      const link = document.createElement('a');
      link.href = URL.createObjectURL(content);
      link.download = "extracted_items.zip";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    });
  };

  const handleItemSelect = (itemId: string) => {
    setApiFeedback(null);
    setSelectedItemIds(prev => {
        const newSet = new Set(prev);
        if (newSet.has(itemId)) {
            newSet.delete(itemId);
        } else {
            newSet.add(itemId);
        }
        return newSet;
    });
  };

  const handleSendToApi = async () => {
    if (selectedItemIds.size === 0) return;

    setIsSending(true);
    setApiFeedback(null);

    const selectedItems = extractedItems.filter(item => selectedItemIds.has(item.id));
    
    // Use the project-specific search endpoint
    const FASTAPI_ENDPOINT = `${config.api.baseUrl}/projects/${projectId}/search`;

    try {
        // Use URLs if available, otherwise convert to files
        const hasUrls = selectedItems.every(item => item.imageUrl);
        
        let formData: FormData;
        
        if (hasUrls) {
            // Use URL-based search
            const urls = selectedItems.map(item => item.imageUrl!).filter(Boolean);
            formData = new FormData();
            formData.append('urls', JSON.stringify(urls));
        } else {
            // Fallback: Convert base64 images to files for upload
            const files = selectedItems.map(item => {
                const byteCharacters = atob(item.imageBase64);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], { type: 'image/png' });
                return new File([blob], `${item.name}.png`, { type: 'image/png' });
            });
            
            formData = new FormData();
            files.forEach(file => {
                formData.append('files', file);
            });
        }

        // Use authenticated fetch
        const response = await authService.authenticatedFetch(FASTAPI_ENDPOINT, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'An unknown server error occurred.' }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        // Update each selected item with its search results
        if (result.success && result.results) {
            setExtractedItems(prevItems => {
                return prevItems.map(item => {
                    if (selectedItemIds.has(item.id)) {
                        // Find matching result by identifier (filename or URL)
                        const itemIdentifier = item.imageUrl || `${item.name}.png`;
                        const matchingResult = result.results.find((res: any) => 
                            res.query_identifier === itemIdentifier || res.query_identifier === `${item.name}.png`
                        );
                        
                        if (matchingResult && matchingResult.success) {
                            return {
                                ...item,
                                searchResults: matchingResult.results
                            };
                        }
                    }
                    return item;
                });
            });
        }
        
        setApiFeedback({ 
            type: 'success', 
            message: `Found results for ${result.total_queries} item(s)!` 
        });
        setSelectedItemIds(new Set()); // Clear selection on success

    } catch (err: any) {
        setApiFeedback({ 
            type: 'error', 
            message: err.message || 'Failed to upload items to the backend.' 
        });
    } finally {
        setIsSending(false);
    }
  };

  const handleDeletePhoto = async (photoUrl: string) => {
    setDeletingPhotoUrl(photoUrl);
    setError(null);
    try {
      await deleteProjectPhoto(projectId, photoUrl);
      setUploadedImagePreviews(prev => prev.filter(url => url !== photoUrl));
    } catch (err: any) {
      setError(`Failed to delete image: ${err.message}`);
    } finally {
      setDeletingPhotoUrl(null);
    }
  };

  const handleAddMorePhotos = () => {
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files);
    }
    // Reset the input so the same file can be selected again
    if (e.target) {
      e.target.value = '';
    }
  };


  return (
    <div className="min-h-screen bg-base-100 text-base-content p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="text-center mb-8">
            <div className="flex items-center justify-center gap-3 mb-2">
                <ImageIcon className="w-8 h-8 text-brand-primary" />
                <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-brand-primary to-brand-secondary">
                    VisionFFE
                </h1>
            </div>
            <div className="flex items-center justify-between max-w-2xl mx-auto mb-4">
                <div className="text-left text-sm text-base-content/70">
                    <div>Welcome, {user?.username || 'User'}</div>
                    <div className="mt-1 text-base-content">Project: <span className="font-semibold">{projectName}</span></div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={onChangeProject}
                        className="px-4 py-2 text-sm font-medium text-base-content bg-base-300 rounded-lg hover:bg-opacity-80 transition-all"
                    >
                        Change project
                    </button>
                    <button
                        onClick={logout}
                        className="px-4 py-2 text-sm font-medium text-base-content bg-base-300 rounded-lg hover:bg-opacity-80 transition-all"
                    >
                        Logout
                    </button>
                </div>
            </div>
            <p className="text-base-content/70 max-w-2xl mx-auto">
            Upload multiple angles of a room to automatically detect, isolate, and download each piece of furniture.
          </p>
        </header>

        <main>
          {/* Hidden file input for adding more photos */}
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileInputChange}
            accept="image/png, image/jpeg, image/webp"
            multiple
            aria-label="Add more photos"
          />
          
          {uploadedImagePreviews.length === 0 ? (
            <FileUpload onFileUpload={handleFileUpload} isLoading={isLoading} />
          ) : (
            <div className="space-y-8">
              <div className="relative w-full max-w-5xl mx-auto bg-base-200 rounded-lg shadow-lg p-4">
                {isLoading && <Loader message={loadingMessage} />}
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-base-content">Uploaded Angles ({uploadedImagePreviews.length})</h3>
                  <button
                    onClick={handleAddMorePhotos}
                    disabled={isLoading}
                    className="flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-brand-primary to-brand-secondary rounded-lg hover:scale-105 transform transition-transform duration-300 ease-in-out shadow-md disabled:opacity-60 disabled:cursor-not-allowed disabled:scale-100"
                  >
                    <ImageIcon className="w-4 h-4" />
                    Add More Photos
                  </button>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 max-h-[40vh] overflow-y-auto pr-2">
                  {uploadedImagePreviews.map((src, index) => {
                    const isPersisted = src.startsWith('http');
                    return (
                        <div key={src} className="group relative aspect-w-1 aspect-h-1 bg-base-300 rounded-md overflow-hidden">
                            <img src={src} alt={`Uploaded room angle ${index + 1}`} className="w-full h-full object-cover" />
                            {isPersisted && (
                                <button
                                  onClick={() => handleDeletePhoto(src)}
                                  disabled={deletingPhotoUrl === src}
                                  className="absolute top-1.5 right-1.5 bg-black/60 p-1 rounded-full text-white opacity-0 group-hover:opacity-100 focus:opacity-100 hover:bg-black/80 transition-all disabled:opacity-70 disabled:cursor-wait"
                                  aria-label="Delete image"
                                >
                                  {deletingPhotoUrl === src ? (
                                    <div className="w-4 h-4 border-2 border-white/50 border-t-white rounded-full animate-spin"></div>
                                  ) : (
                                    <XIcon className="w-4 h-4" />
                                  )}
                                </button>
                            )}
                        </div>
                    );
                  })}
                </div>
              </div>

              {error && (
                <div className="text-center bg-red-900/50 border border-red-700 text-red-200 p-4 rounded-lg max-w-3xl mx-auto">
                    <p className="font-semibold">An Error Occurred</p>
                    <p>{error}</p>
                </div>
              )}
              
              <div className="flex items-center justify-center gap-4 flex-wrap">
                <button
                  onClick={resetState}
                  className="flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-medium text-base-content bg-base-300 rounded-lg hover:bg-opacity-80 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={isLoading}
                >
                  <ResetIcon className="w-5 h-5" />
                  Start Over
                </button>
                <button
                    onClick={runExtractionProcess}
                    disabled={isLoading || extractedItems.length > 0}
                    className="flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-bold text-white bg-gradient-to-r from-brand-primary to-brand-secondary rounded-lg hover:scale-105 transform transition-transform duration-300 ease-in-out shadow-md disabled:opacity-60 disabled:cursor-not-allowed disabled:scale-100"
                >
                    <ImageIcon className="w-5 h-5" />
                    Extract Items
                </button>
                <button
                    onClick={handleSendToApi}
                    disabled={isLoading || isSending || selectedItemIds.size === 0}
                    className="flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-bold text-white bg-gradient-to-r from-brand-primary to-brand-secondary rounded-lg hover:scale-105 transform transition-transform duration-300 ease-in-out shadow-md disabled:opacity-60 disabled:cursor-not-allowed disabled:scale-100"
                >
                    {isSending ? (
                        <div className="w-5 h-5 border-2 border-white/50 border-t-white rounded-full animate-spin"></div>
                    ) : (
                        <SendIcon className="w-5 h-5" />
                    )}
                    Send Selection ({selectedItemIds.size})
                </button>
                <button
                    onClick={handleDownloadZip}
                    disabled={isLoading || extractedItems.length === 0}
                    className="flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-bold text-white bg-gradient-to-r from-brand-primary to-brand-secondary rounded-lg hover:scale-105 transform transition-transform duration-300 ease-in-out shadow-md disabled:opacity-60 disabled:cursor-not-allowed disabled:scale-100"
                >
                    <DownloadIcon className="w-5 h-5" />
                    Download All (.zip)
                </button>
              </div>

            {apiFeedback && (
                <div className={`mt-4 text-center p-3 rounded-lg max-w-3xl mx-auto text-sm ${
                    apiFeedback.type === 'success'
                    ? 'bg-green-900/50 border border-green-700 text-green-200'
                    : 'bg-red-900/50 border border-red-700 text-red-200'
                }`}>
                    <p>{apiFeedback.message}</p>
                </div>
            )}

            </div>
          )}

          {extractedItems.length > 0 && (
            <div className="mt-12">
              <h2 className="text-2xl font-semibold text-center mb-6">Extracted Items ({extractedItems.length})</h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                {extractedItems.map(item => (
                  <ItemCard 
                    key={item.id} 
                    item={item}
                    isSelected={selectedItemIds.has(item.id)}
                    onSelect={handleItemSelect}
                  />
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default ExtractorApp;