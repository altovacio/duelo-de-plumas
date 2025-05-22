import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { createText, updateText, Text } from '../../services/textService';
import BackButton from '../../components/ui/BackButton';
import MDEditor from '@uiw/react-md-editor';

const MarkdownEditorPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const initialText = location.state?.text as Text | undefined;
  
  const [title, setTitle] = useState(initialText?.title || '');
  const [content, setContent] = useState(initialText?.content || '');
  const [author, setAuthor] = useState(initialText?.author || '');
  const [isSaving, setIsSaving] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  // Set up window beforeunload event to warn about unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (unsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [unsavedChanges]);

  // Mark changes as unsaved when any form field changes
  useEffect(() => {
    if (title !== (initialText?.title || '') || 
        content !== (initialText?.content || '') || 
        author !== (initialText?.author || '')) {
      setUnsavedChanges(true);
    }
  }, [title, content, author, initialText]);

  const handleSave = async () => {
    if (!title.trim() || !content.trim() || !author.trim()) {
      toast.error('Please fill in all fields');
      return;
    }

    setIsSaving(true);
    try {
      const textData = { title, content, author };
      
      if (initialText) {
        // Update existing text
        await updateText(initialText.id, textData);
        toast.success('Text updated successfully');
      } else {
        // Create new text
        await createText(textData);
        toast.success('Text created successfully');
      }
      
      setUnsavedChanges(false);
      navigate('/dashboard');
    } catch (error) {
      console.error('Error saving text:', error);
      toast.error('Failed to save text');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    if (unsavedChanges) {
      if (window.confirm('You have unsaved changes. Are you sure you want to leave?')) {
        navigate('/dashboard');
      }
    } else {
      navigate('/dashboard');
    }
  };

  // Simple markdown to HTML conversion for preview
  const renderMarkdown = (text: string) => {
    // This is a very basic markdown renderer, in a real app you would use a library like marked
    return text
      .replace(/# (.*?)$/gm, '<h1>$1</h1>')
      .replace(/## (.*?)$/gm, '<h2>$1</h2>')
      .replace(/### (.*?)$/gm, '<h3>$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/!\[(.*?)\]\((.*?)\)/g, '<img alt="$1" src="$2" />')
      .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>')
      .replace(/\n/g, '<br />');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div className="flex items-center">
            <BackButton to="/dashboard" label="Back to Dashboard" />
            <h1 className="ml-4 text-xl font-bold text-gray-900">
              {initialText ? 'Edit Text' : 'Create New Text'}
            </h1>
          </div>
          <div className="flex space-x-2">
            <button
              type="button"
              onClick={() => setPreviewMode(!previewMode)}
              className="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              {previewMode ? 'Edit' : 'Preview'}
            </button>
            <button
              type="button"
              onClick={handleCancel}
              className="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="px-4 py-2 bg-indigo-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400"
            >
              {isSaving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      </header>
      
      <div className="flex-1 flex flex-col max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {!previewMode ? (
          <div className="flex-1 flex flex-col space-y-4">
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700">Title</label>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Enter a title for your text"
              />
            </div>
            
            <div>
              <label htmlFor="author" className="block text-sm font-medium text-gray-700">Author</label>
              <input
                type="text"
                id="author"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Enter author name"
              />
            </div>
            
            <div className="flex-1 flex flex-col">
              <label htmlFor="content" className="block text-sm font-medium text-gray-700">Content (Markdown)</label>
              <div className="mt-1 flex-1 flex flex-col">
                <div data-color-mode="light">
                  <MDEditor
                    value={content}
                    onChange={(value) => setContent(value || '')}
                    height={500}
                  />
                </div>
              </div>
            </div>
            
            <div className="text-sm text-gray-500">
              <p>Use the toolbar above to format your text with markdown: headings, bold, italic, links, and more.</p>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col space-y-4">
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="px-4 py-5 sm:px-6">
                <h2 className="text-2xl font-bold text-gray-900">{title || 'Untitled'}</h2>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">By {author || 'Anonymous'}</p>
              </div>
              <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
                <div 
                  className="prose max-w-none"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MarkdownEditorPage; 