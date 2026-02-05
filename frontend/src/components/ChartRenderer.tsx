"use client";

import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { Download, FileSpreadsheet, FileJson, Copy, Check } from 'lucide-react';
import { ChartDataPoint } from '@/types';
import { Card } from '@/components/ui/Card';
import { exportToCSV, exportToExcel, exportToJSON, copyToClipboard } from '@/lib/export';

interface ChartRendererProps {
  data: ChartDataPoint[];
  type?: string; 
  title?: string;
}

const COLORS = ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#d1fae5'];

export const ChartRenderer: React.FC<ChartRendererProps> = ({ data, type = 'bar', title }) => {
  const [copied, setCopied] = useState(false);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);

  if (!data || data.length === 0) return null;

  const handleCopy = async () => {
    const success = await copyToClipboard(data);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleExportCSV = () => {
    exportToCSV(data, 'chart-data.csv');
    setExportMenuOpen(false);
  };

  const handleExportExcel = () => {
    exportToExcel(data, 'chart-data.xlsx');
    setExportMenuOpen(false);
  };

  const handleExportJSON = () => {
    exportToJSON(data, 'chart-data.json');
    setExportMenuOpen(false);
  };

  const renderChart = () => {
    switch (type.toLowerCase()) {
      case 'line':
        return (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="name" stroke="#888" />
            <YAxis stroke="#888" />
            <Tooltip 
              contentStyle={{ backgroundColor: 'hsl(217 33% 17%)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
              itemStyle={{ color: '#fff' }}
            />
            <Legend wrapperStyle={{ color: '#9ca3af' }} />
            <Line type="monotone" dataKey="value" stroke="#10b981" strokeWidth={3} dot={{ r: 5, fill: '#10b981' }} />
          </LineChart>
        );
      case 'pie':
        return (
          <PieChart>
             <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ backgroundColor: '#1e1e24', border: 'none', borderRadius: '8px' }}
            />
             <Legend />
          </PieChart>
        );
      case 'bar':
      default:
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="name" stroke="#9ca3af" tick={{ fill: '#9ca3af' }} />
            <YAxis stroke="#9ca3af" tick={{ fill: '#9ca3af' }} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'hsl(217 33% 17%)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
              cursor={{ fill: 'rgba(16, 185, 129, 0.1)' }}
            />
            <Legend wrapperStyle={{ color: '#9ca3af' }} />
            <Bar dataKey="value" fill="#10b981" radius={[8, 8, 0, 0]} />
          </BarChart>
        );
    }
  };

  return (
    <Card className="w-full p-4 mt-4 glass border-none relative">
      {/* Header with Export Buttons */}
      <div className="flex items-center justify-between mb-4">
        {title && <h3 className="text-sm font-medium text-gray-400">{title}</h3>}
        
        <div className="flex items-center space-x-2 ml-auto">
          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors group"
            title="Panoya Kopyala"
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4 text-gray-400 group-hover:text-gray-200" />
            )}
          </button>

          {/* Export Dropdown */}
          <div className="relative">
            <button
              onClick={() => setExportMenuOpen(!exportMenuOpen)}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors group flex items-center space-x-1"
              title="Dışa Aktar"
            >
              <Download className="w-4 h-4 text-gray-400 group-hover:text-gray-200" />
            </button>

            {/* Dropdown Menu */}
            {exportMenuOpen && (
              <div className="absolute right-0 top-full mt-2 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-10 min-w-[160px]">
                <button
                  onClick={handleExportCSV}
                  className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 flex items-center space-x-2 rounded-t-lg"
                >
                  <FileSpreadsheet className="w-4 h-4" />
                  <span>CSV Olarak İndir</span>
                </button>
                <button
                  onClick={handleExportExcel}
                  className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 flex items-center space-x-2"
                >
                  <FileSpreadsheet className="w-4 h-4" />
                  <span>Excel Olarak İndir</span>
                </button>
                <button
                  onClick={handleExportJSON}
                  className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 flex items-center space-x-2 rounded-b-lg"
                >
                  <FileJson className="w-4 h-4" />
                  <span>JSON Olarak İndir</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
