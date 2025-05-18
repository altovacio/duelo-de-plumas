import React, { useState, useEffect, useRef } from 'react';
import MDEditor from '@uiw/react-md-editor';

interface TextFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (text: { title: string; content: string; author: string }) => void;
  initialText?: { title: string; content: string; author: string };
  isEditing?: boolean;
}

const TextFormModal: React.FC<TextFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialText = { title: '', content: '', author: '' },
  isEditing = false,
}) => {
  // Track if this is the first render or if isOpen changed
  const firstRender = useRef(true);
  const wasOpen = useRef(isOpen);
  
  const [title, setTitle] = useState(initialText.title);
  const [content, setContent] = useState(initialText.content);
  const [author, setAuthor] = useState(initialText.author);
  const [uploadType, setUploadType] = useState<'markdown' | 'pdf'>('markdown');
  const [pdfFile, setPdfFile] = useState<File | null>(null);

  // Only update form values when the modal opens or initialText changes significantly
  useEffect(() => {
    // Only run this effect when modal opens or on first render with initialText
    if ((isOpen && !wasOpen.current) || firstRender.current) {
      setTitle(initialText.title);
      setContent(initialText.content);
      setAuthor(initialText.author);
      firstRender.current = false;
    }
    
    // Update the ref tracking if modal is open
    wasOpen.current = isOpen;
  }, [isOpen, initialText]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ title, content, author });
    onClose();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setPdfFile(file);
      // In a real implementation, we would need to handle PDF upload and conversion
      // For now, we'll just set a placeholder message
      setContent(`[PDF File: ${file.name}]`);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  {isEditing ? 'Edit Text' : 'Create New Text'}
                </h3>
              </div>

              <div className="mb-4">
                <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                  Title
                </label>
                <input
                  type="text"
                  id="title"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                />
              </div>

              <div className="mb-4">
                <label htmlFor="author" className="block text-sm font-medium text-gray-700">
                  Author
                </label>
                <input
                  type="text"
                  id="author"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  value={author}
                  onChange={(e) => setAuthor(e.target.value)}
                  required
                  placeholder="Who wrote this text?"
                />
              </div>

              <div className="mb-4">
                <div className="flex items-center mb-2">
                  <label className="block text-sm font-medium text-gray-700 mr-4">
                    Text Type
                  </label>
                  <div className="flex border rounded-md overflow-hidden">
                    <button
                      type="button"
                      className={`px-4 py-2 text-sm font-medium ${
                        uploadType === 'markdown'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-white text-gray-700 hover:bg-gray-50'
                      }`}
                      onClick={() => setUploadType('markdown')}
                    >
                      Write Markdown
                    </button>
                    <button
                      type="button"
                      className={`px-4 py-2 text-sm font-medium ${
                        uploadType === 'pdf'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-white text-gray-700 hover:bg-gray-50'
                      }`}
                      onClick={() => setUploadType('pdf')}
                    >
                      Upload PDF
                    </button>
                  </div>
                </div>

                {uploadType === 'markdown' ? (
                  <div data-color-mode="light">
                    <MDEditor
                      value={content}
                      onChange={(value) => setContent(value || '')}
                      height={300}
                    />
                  </div>
                ) : (
                  <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                    <div className="space-y-1 text-center">
                      <svg
                        className="mx-auto h-12 w-12 text-gray-400"
                        stroke="currentColor"
                        fill="none"
                        viewBox="0 0 48 48"
                        aria-hidden="true"
                      >
                        <path
                          d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4h-12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                          strokeWidth={2}
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      <div className="flex text-sm text-gray-600">
                        <label
                          htmlFor="file-upload"
                          className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500"
                        >
                          <span>Upload a PDF file</span>
                          <input
                            id="file-upload"
                            name="file-upload"
                            type="file"
                            className="sr-only"
                            accept="application/pdf"
                            onChange={handleFileChange}
                          />
                        </label>
                        <p className="pl-1">or drag and drop</p>
                      </div>
                      <p className="text-xs text-gray-500">PDF up to 10MB</p>
                      {pdfFile && (
                        <p className="text-sm text-indigo-600">
                          Selected: {pdfFile.name}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
              >
                {isEditing ? 'Save Changes' : 'Create Text'}
              </button>
              <button
                type="button"
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                onClick={onClose}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TextFormModal; 