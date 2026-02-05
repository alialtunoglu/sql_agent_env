import React, { useState } from 'react';
import { Upload, X, Database, CheckCircle, AlertCircle, Trash2 } from 'lucide-react';
import { uploadFile, getDatabaseStatus, deleteDatabase } from '@/lib/api';

interface FileUploadProps {
  sessionId: string;
  onUploadSuccess?: () => void;
}

export default function FileUpload({ sessionId, onUploadSuccess }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });
  const [databaseInfo, setDatabaseInfo] = useState<any>(null);
  const [showUploadSection, setShowUploadSection] = useState(false);

  // Check database status on mount (only if sessionId exists)
  React.useEffect(() => {
    if (sessionId) {
      checkDatabaseStatus();
    }
  }, [sessionId]);

  const checkDatabaseStatus = async () => {
    try {
      const status = await getDatabaseStatus(sessionId);
      if (status.has_database && status.metadata) {
        setDatabaseInfo(status.metadata);
      } else {
        setDatabaseInfo(null);
      }
    } catch (error) {
      console.error('Database status check failed:', error);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      const validTypes = ['.csv', '.xlsx', '.xls'];
      const fileExt = selectedFile.name.toLowerCase().slice(selectedFile.name.lastIndexOf('.'));
      
      if (validTypes.includes(fileExt)) {
        setFile(selectedFile);
        setUploadStatus({ type: null, message: '' });
      } else {
        setUploadStatus({
          type: 'error',
          message: 'Desteklenmeyen dosya formatı. Lütfen CSV veya Excel dosyası seçin.'
        });
      }
    }
  };

  const handleUpload = async () => {
    if (!file || !sessionId) return;

    setUploading(true);
    setUploadStatus({ type: null, message: '' });

    try {
      const result = await uploadFile(file, sessionId);
      
      setUploadStatus({
        type: 'success',
        message: `Dosya başarıyla yüklendi! ${result.row_count} satır, ${result.column_count} sütun.`
      });
      
      setFile(null);
      setShowUploadSection(false);
      
      // Refresh database status
      await checkDatabaseStatus();
      
      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (error: any) {
      setUploadStatus({
        type: 'error',
        message: error.message || 'Dosya yüklenirken bir hata oluştu.'
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDatabase = async () => {
    if (!confirm('Yüklediğiniz veritabanını silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      await deleteDatabase(sessionId);
      setDatabaseInfo(null);
      setUploadStatus({
        type: 'success',
        message: 'Veritabanı başarıyla silindi.'
      });
    } catch (error: any) {
      setUploadStatus({
        type: 'error',
        message: error.message || 'Veritabanı silinirken bir hata oluştu.'
      });
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto mb-4 bg-slate-700">
      {/* Database Status Card */}
      {databaseInfo ? (
        <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-lg p-4 mb-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <Database className="w-5 h-5 text-green-400 mt-1" />
              <div>
                <h3 className="text-sm font-semibold text-green-300">Özel Veritabanı Aktif</h3>
                <p className="text-xs text-gray-400 mt-1">
                  {databaseInfo.original_filename} ({databaseInfo.row_count} satır, {databaseInfo.column_count} sütun)
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Tablo: <span className="text-green-400 font-mono">{databaseInfo.table_name}</span>
                </p>
              </div>
            </div>
            <button
              onClick={handleDeleteDatabase}
              className="p-2 hover:bg-red-500/20 rounded-lg transition-colors group"
              title="Veritabanını Sil"
            >
              <Trash2 className="w-4 h-4 text-gray-400 group-hover:text-red-400" />
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowUploadSection(!showUploadSection)}
          className="w-full bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-lg p-3 hover:border-blue-400/50 transition-all flex items-center justify-center space-x-2"
        >
          <Database className="w-5 h-5 text-blue-400" />
          <span className="text-sm text-gray-300">
            {showUploadSection ? 'Yükleme Panelini Kapat' : 'Kendi Verinizi Yükleyin'}
          </span>
        </button>
      )}

      {/* Upload Section */}
      {showUploadSection && !databaseInfo && (
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-4 mt-2">
          <div className="space-y-4">
            <div className="text-center">
              <label
                htmlFor="file-upload"
                className="cursor-pointer inline-flex items-center justify-center space-x-2 px-4 py-3 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/50 rounded-lg transition-all"
              >
                <Upload className="w-5 h-5 text-blue-400" />
                <span className="text-sm text-gray-300">
                  {file ? file.name : 'CSV veya Excel Dosyası Seçin'}
                </span>
              </label>
              <input
                id="file-upload"
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileChange}
                className="hidden"
              />
              
              {file && (
                <button
                  onClick={() => setFile(null)}
                  className="ml-2 p-2 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              )}
            </div>

            {file && (
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="w-full py-2 px-4 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-all flex items-center justify-center space-x-2"
              >
                {uploading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                    <span>Yükleniyor...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    <span>Dosyayı Yükle</span>
                  </>
                )}
              </button>
            )}
          </div>

          <p className="text-xs text-gray-500 mt-3 text-center">
            CSV veya Excel dosyanızı yükledikten sonra, verileriniz üzerinde doğal dil ile sorgulama yapabilirsiniz.
          </p>
        </div>
      )}

      {/* Status Messages */}
      {uploadStatus.type && (
        <div
          className={`mt-3 p-3 rounded-lg flex items-center space-x-2 ${
            uploadStatus.type === 'success'
              ? 'bg-green-500/10 border border-green-500/30'
              : 'bg-red-500/10 border border-red-500/30'
          }`}
        >
          {uploadStatus.type === 'success' ? (
            <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          )}
          <p
            className={`text-sm ${
              uploadStatus.type === 'success' ? 'text-green-300' : 'text-red-300'
            }`}
          >
            {uploadStatus.message}
          </p>
        </div>
      )}
    </div>
  );
}
