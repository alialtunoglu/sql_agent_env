/**
 * Data Export Utilities
 * Provides functions to export chart data to various formats (CSV, Excel)
 */

import { ChartDataPoint } from '@/types';

/**
 * Convert data to CSV format and trigger download
 */
export function exportToCSV(data: ChartDataPoint[], filename: string = 'data.csv'): void {
  if (!data || data.length === 0) {
    console.warn('No data to export');
    return;
  }

  // Get all unique keys from all data points
  const allKeys = Array.from(
    new Set(data.flatMap(item => Object.keys(item)))
  );

  // Create CSV header
  const csvHeader = allKeys.join(',');

  // Create CSV rows
  const csvRows = data.map(item => {
    return allKeys
      .map(key => {
        const value = item[key];
        // Escape values that contain commas or quotes
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value ?? '';
      })
      .join(',');
  });

  // Combine header and rows
  const csv = [csvHeader, ...csvRows].join('\n');

  // Create blob and trigger download
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  downloadBlob(blob, filename);
}

/**
 * Convert data to Excel format and trigger download
 * Uses the xlsx library
 */
export async function exportToExcel(
  data: ChartDataPoint[],
  filename: string = 'data.xlsx',
  sheetName: string = 'Data'
): Promise<void> {
  if (!data || data.length === 0) {
    console.warn('No data to export');
    return;
  }

  try {
    // Dynamically import xlsx to reduce initial bundle size
    const XLSX = await import('xlsx');

    // Create worksheet from data
    const worksheet = XLSX.utils.json_to_sheet(data);

    // Create workbook and add worksheet
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);

    // Generate Excel file and trigger download
    XLSX.writeFile(workbook, filename);
  } catch (error) {
    console.error('Failed to export to Excel:', error);
    // Fallback to CSV if Excel export fails
    console.log('Falling back to CSV export...');
    exportToCSV(data, filename.replace('.xlsx', '.csv'));
  }
}

/**
 * Export data to JSON format
 */
export function exportToJSON(data: ChartDataPoint[], filename: string = 'data.json'): void {
  if (!data || data.length === 0) {
    console.warn('No data to export');
    return;
  }

  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: 'application/json;charset=utf-8;' });
  downloadBlob(blob, filename);
}

/**
 * Helper function to trigger file download
 */
function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Copy data to clipboard as tab-separated values (Excel-compatible)
 */
export async function copyToClipboard(data: ChartDataPoint[]): Promise<boolean> {
  if (!data || data.length === 0) {
    console.warn('No data to copy');
    return false;
  }

  try {
    // Get all unique keys
    const allKeys = Array.from(
      new Set(data.flatMap(item => Object.keys(item)))
    );

    // Create tab-separated values (TSV) format
    const header = allKeys.join('\t');
    const rows = data.map(item =>
      allKeys.map(key => item[key] ?? '').join('\t')
    );
    const tsv = [header, ...rows].join('\n');

    // Copy to clipboard
    await navigator.clipboard.writeText(tsv);
    return true;
  } catch (error) {
    console.error('Failed to copy to clipboard:', error);
    return false;
  }
}
