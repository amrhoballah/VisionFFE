import config from '../config';
import { authService } from './authService';

export interface Project {
  id: string;
  name: string;
  user_id: string;
  photo_urls: string[];
  created_at: string;
  updated_at?: string;
}

export async function listProjects(): Promise<Project[]> {
  const res = await authService.authenticatedFetch(`${config.api.baseUrl}/projects/`);
  if (!res.ok) throw new Error('Failed to load projects');
  return res.json();
}

export async function createProject(name: string): Promise<Project> {
  const res = await authService.authenticatedFetch(`${config.api.baseUrl}/projects/`, {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Failed to create project');
  }
  return res.json();
}

export async function uploadProjectPhotos(projectId: string, files: FileList | File[]): Promise<Project> {
  const form = new FormData();
  const arr = Array.isArray(files) ? files : Array.from(files);
  arr.forEach(f => form.append('files', f));
  const res = await authService.authenticatedFetch(`${config.api.baseUrl}/projects/${projectId}/photos`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error('Failed to upload photos');
  return res.json();
}

export async function deleteProjectPhoto(projectId: string, photoUrl: string): Promise<void> {
  const res = await authService.authenticatedFetch(`${config.api.baseUrl}/projects/${projectId}/photos`, {
    method: 'DELETE',
    body: JSON.stringify({ photo_url: photoUrl }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Failed to delete photo');
  }
}