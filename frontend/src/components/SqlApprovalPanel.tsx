import React, { useState } from 'react';
import { Play, Edit2, Copy, Check, AlertTriangle, Download } from 'lucide-react';
import { executeSql } from '@/lib/api';
import { exportToCSV, exportToExcel, exportToJSON } from '@/lib/export';

interface SqlApprovalPanelProps {
  initialSql: string;
  sessionId: string;
  onExecutionComplete?: (result: any) => void;
}

export default function SqlApprovalPanel({
  initialSql,
  sessionId,
  onExecutionComplete
}: SqlApprovalPanelProps) {
  const [sql, setSql] = useState(initialSql);
  const [isEditing, setIsEditing] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [copied, setCopied] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExecute = async () => {
    setExecuting(true);
    setResult(null);

    try {
      const response = await executeSql(sql, sessionId);
      setResult(response);
      
      if (onExecutionComplete) {
        onExecutionComplete(response);
      }
    } catch (error: any) {
      setResult({
        success: false,
        error: error.message || 'Sorgu çalıştırılamadı'
      });
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="mt-3 border border-blue-500/30 rounded-lg overflow-hidden bg-gray-900/50">
      {/* Header */}
      <div className="bg-blue-500/10 px-4 py-2 flex items-center justify-between border-b border-blue-500/20">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-yellow-400" />
          <span className="text-sm font-medium text-blue-300">SQL Sorgusu Oluşturuldu</span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="p-1.5 hover:bg-gray-700 rounded transition-colors"
            title={isEditing ? 'Düzenlemeyi Bitir' : 'Düzenle'}
          >
            <Edit2 className="w-4 h-4 text-gray-400" />
          </button>
          <button
            onClick={handleCopy}
            className="p-1.5 hover:bg-gray-700 rounded transition-colors"
            title="Kopyala"
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4 text-gray-400" />
            )}
          </button>
        </div>
      </div>

      {/* SQL Editor */}
      <div className="p-4">
        {isEditing ? (
          <textarea
            value={sql}
            onChange={(e) => setSql(e.target.value)}
            className="w-full bg-gray-950 text-green-400 font-mono text-sm p-3 rounded border border-gray-700 focus:border-blue-500 focus:outline-none min-h-[120px] resize-y"
            spellCheck={false}
          />
        ) : (
          <pre className="bg-gray-950 text-green-400 font-mono text-sm p-3 rounded overflow-x-auto">
            <code>{sql}</code>
          </pre>
        )}

        {/* Execute Button */}
        <button
          onClick={handleExecute}
          disabled={executing || !sql.trim()}
          className="mt-3 w-full py-2.5 px-4 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-all flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/20"
        >
          {executing ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
              <span>Çalıştırılıyor...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Sorguyu Onayla ve Çalıştır</span>
            </>
          )}
        </button>

        {/* Result Display */}
        {result && (
          <div className="mt-3 space-y-2">
            <div
              className={`p-3 rounded-lg flex items-start space-x-2 ${
                result.success
                  ? 'bg-green-500/10 border border-green-500/30'
                  : 'bg-red-500/10 border border-red-500/30'
              }`}
            >
              {result.success ? (
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <p
                  className={`text-sm ${
                    result.success ? 'text-green-300' : 'text-red-300'
                  }`}
                >
                  {result.message || result.error}
                </p>
                {result.row_count !== undefined && (
                  <p className="text-xs text-gray-400 mt-1">
                    Dönen satır sayısı: {result.row_count}
                  </p>
                )}
              </div>
            </div>

            {/* Export buttons for full result set */}
            {result.success && Array.isArray(result.data) && result.data.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-gray-400 mr-2">
                  Tüm sonuçları indir:
                </span>
                <button
                  type="button"
                  onClick={() => exportToCSV(result.data, 'query-results.csv')}
                  className="inline-flex items-center px-2.5 py-1.5 text-xs rounded-md bg-gray-800 hover:bg-gray-700 text-gray-100 border border-gray-700 transition-colors"
                >
                  <Download className="w-3 h-3 mr-1" />
                  CSV
                </button>
                <button
                  type="button"
                  onClick={() => exportToExcel(result.data, 'query-results.xlsx', 'Results')}
                  className="inline-flex items-center px-2.5 py-1.5 text-xs rounded-md bg-gray-800 hover:bg-gray-700 text-gray-100 border border-gray-700 transition-colors"
                >
                  <Download className="w-3 h-3 mr-1" />
                  Excel
                </button>
                <button
                  type="button"
                  onClick={() => exportToJSON(result.data, 'query-results.json')}
                  className="inline-flex items-center px-2.5 py-1.5 text-xs rounded-md bg-gray-800 hover:bg-gray-700 text-gray-100 border border-gray-700 transition-colors"
                >
                  <Download className="w-3 h-3 mr-1" />
                  JSON
                </button>
              </div>
            )}
          </div>
        )}

        {/* Security Notice */}
        <p className="text-xs text-gray-500 mt-3 flex items-start space-x-1">
          <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
          <span>
            Güvenlik nedeniyle sadece SELECT sorguları çalıştırılabilir. 
            Veri değiştiren işlemler (INSERT, UPDATE, DELETE) engellenmiştir.
          </span>
        </p>
      </div>
    </div>
  );
}
