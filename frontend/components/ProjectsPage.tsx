import React, { useEffect, useState } from 'react';
import { listProjects, createProject, Project } from '../services/projectService';
import { useAuth } from '../contexts/AuthContext';

interface ProjectsPageProps {
  onSelectProject: (project: Project) => void;
}

const ProjectsPage: React.FC<ProjectsPageProps> = ({ onSelectProject }) => {
  const { user, logout } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await listProjects();
        setProjects(data);
      } catch (e: any) {
        setError(e.message || 'Failed to load projects');
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const p = await createProject(newName.trim());
      setProjects(prev => [p, ...prev]);
      setNewName('');
      onSelectProject(p);
    } catch (e: any) {
      setError(e.message || 'Failed to create project');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="min-h-screen bg-base-100 text-base-content p-4 sm:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-6 flex items-center justify-between">
          <div className="text-sm text-base-content/70">Welcome, {user?.username || 'User'}</div>
          <button onClick={logout} className="px-4 py-2 text-sm font-medium bg-base-300 rounded-lg hover:bg-base-200 transition-colors">Logout</button>
        </header>

        <h1 className="text-2xl font-bold mb-4">Your Projects</h1>

        <div className="mb-6 flex gap-2">
          <input
            value={newName}
            onChange={e => setNewName(e.target.value)}
            placeholder="New project name"
            className="w-full max-w-md bg-base-300 border border-base-300 text-base-content rounded-lg p-2.5 focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition"
          />
          <button
            onClick={handleCreate}
            disabled={creating || !newName.trim()}
            className="flex items-center justify-center px-6 py-2.5 font-bold text-white bg-gradient-to-r from-brand-primary to-brand-secondary rounded-lg hover:scale-105 transform transition-transform duration-300 ease-in-out shadow-md disabled:opacity-60 disabled:cursor-not-allowed disabled:scale-100"
          >
            {creating ? (
              <div className="w-5 h-5 border-2 border-white/50 border-t-white rounded-full animate-spin"></div>
            ) : (
              'Create'
            )}
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded bg-red-900/50 border border-red-700 text-red-200 text-sm">{error}</div>
        )}

        {loading ? (
          <div className="flex justify-center items-center p-8">
            <div className="w-8 h-8 border-2 border-base-300 border-t-brand-primary rounded-full animate-spin"></div>
          </div>
        ) : (
          <ul className="divide-y divide-base-300 rounded-lg border border-base-300 overflow-hidden">
            {projects.map(p => (
              <li key={p.id} className="p-4 flex items-center justify-between hover:bg-base-200 transition-colors">
                <div>
                  <div className="font-medium">{p.name}</div>
                  <div className="text-xs text-base-content/60">{new Date(p.created_at).toLocaleString()} • {p.photo_urls.length} photos</div>
                </div>
                <button className="px-3 py-1.5 text-sm font-medium text-base-content bg-base-300 rounded-lg hover:bg-base-200 transition-colors" onClick={() => onSelectProject(p)}>Open</button>
              </li>
            ))}
            {projects.length === 0 && (
              <li className="p-6 text-center text-base-content/70">No projects yet. Create your first project above.</li>
            )}
          </ul>
        )}
      </div>
    </div>
  );
};

export default ProjectsPage;