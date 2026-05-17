'use client';

import React, { useState, useEffect } from 'react';
import { Upload, FileJson, BarChart3, TrendingUp, Clock, HardDrive, Info } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ZAxis
} from 'recharts';

type BenchmarkResult = {
  file: string;
  method: string;
  compression_ratio: number;
  encode_time_ms_mean: number;
  encode_time_ms_std: number;
  decode_time_ms_mean: number;
  decode_time_ms_std: number;
  peak_memory_mb_mean: number;
  psnr_mean: number | "Infinity";
  ssim_mean: number;
};

type BenchmarkData = {
  metadata: {
    dataset_path: string;
    trials: number;
  };
  results: BenchmarkResult[];
};

export default function Home() {
  const [data, setData] = useState<BenchmarkData | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Load demo data
  const loadDemoData = async () => {
    try {
      const res = await fetch('/demo_results.json');
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error("Failed to load demo data", e);
    }
  };

  useEffect(() => {
    loadDemoData();
  }, []);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const json = JSON.parse(event.target?.result as string);
          setData(json);
        } catch (err) {
          alert('Invalid JSON file format.');
        }
      };
      reader.readAsText(file);
    }
  };

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="animate-pulse flex items-center gap-2">
          <HardDrive className="h-5 w-5 text-gray-500" />
          <span className="text-gray-500 font-medium">Loading Dashboard...</span>
        </div>
      </div>
    );
  }

  // Formatting for graphs
  const formatLatencyData = () => {
    return data.results.map((r) => ({
      name: r.method,
      Encode: Math.round(r.encode_time_ms_mean),
      Decode: Math.round(r.decode_time_ms_mean),
    }));
  };

  const formatRDData = () => {
    // Only plot lossy methods for RD curve
    return data.results
      .filter((r) => r.psnr_mean !== "Infinity")
      .map((r) => ({
        name: r.method,
        cr: Number(r.compression_ratio.toFixed(2)),
        psnr: Number(r.psnr_mean),
        ssim: Number(r.ssim_mean),
      }));
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header & Upload */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-gray-200">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-gray-900">KMRI Benchmark Suite</h1>
            <p className="text-gray-500 mt-1">Medical Imaging Compression Reporting & Analytics</p>
          </div>
          
          <div className="flex items-center gap-3">
            <label className="relative cursor-pointer bg-white border border-gray-300 shadow-sm hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-md transition-colors flex items-center gap-2">
              <Upload className="h-4 w-4" />
              <span>Upload Results JSON</span>
              <input 
                type="file" 
                accept=".json" 
                className="sr-only" 
                onChange={handleFileUpload} 
              />
            </label>
          </div>
        </header>

        {/* Top Cards */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-100 p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-blue-50 rounded-md p-3">
                <FileJson className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Dataset Path</dt>
                  <dd className="text-lg font-semibold text-gray-900 truncate" title={data.metadata.dataset_path}>
                    {data.metadata.dataset_path}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-100 p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-emerald-50 rounded-md p-3">
                <TrendingUp className="h-6 w-6 text-emerald-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Test Trials</dt>
                  <dd className="text-lg font-semibold text-gray-900">{data.metadata.trials}</dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-100 p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-purple-50 rounded-md p-3">
                <BarChart3 className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Methods Tested</dt>
                  <dd className="text-lg font-semibold text-gray-900">{data.results.length}</dd>
                </dl>
              </div>
            </div>
          </div>
          <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-100 p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-orange-50 rounded-md p-3">
                <Clock className="h-6 w-6 text-orange-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Hardware Tier</dt>
                  <dd className="text-lg font-semibold text-gray-900">CPU-Only Bias</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Latency Plot */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-6">Latency Profile (ms)</h3>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={formatLatencyData()}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                  <RechartsTooltip 
                    cursor={{fill: '#F3F4F6'}}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '20px' }}/>
                  <Bar dataKey="Encode" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Decode" fill="#10B981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Rate Distortion */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-medium text-gray-900">Rate-Distortion Performance</h3>
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">Lossy Only</span>
            </div>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis type="number" dataKey="cr" name="Compression Ratio" domain={['auto', 'auto']} tick={{ fontSize: 12 }}>
                  </XAxis>
                  <YAxis type="number" dataKey="psnr" name="PSNR (dB)" domain={['auto', 'auto']} tick={{ fontSize: 12 }}>
                  </YAxis>
                  <ZAxis type="category" dataKey="name" name="Method" />
                  <RechartsTooltip 
                    cursor={{strokeDasharray: '3 3'}}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Legend />
                  {formatRDData().map((entry, index) => (
                     <Scatter key={index} name={entry.name} data={[entry]} fill="#6366F1" shape="circle" />
                  ))}
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Detailed Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
            <h3 className="text-base font-semibold text-gray-900">Comprehensive Baseline Comparison</h3>
            <div className="flex items-center text-sm text-gray-500">
              <Info className="h-4 w-4 mr-1.5" />
              Showing mean across {data.metadata.trials} trials
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-white">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Method</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Ratio</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Encode (ms)</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Decode (ms)</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">PSNR (dB)</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">SSIM</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Peak Mem (MB)</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.results.map((row, idx) => (
                  <tr key={idx} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{row.method}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-mono">{row.compression_ratio.toFixed(2)}x</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-mono">{row.encode_time_ms_mean.toFixed(1)} ± {row.encode_time_ms_std.toFixed(1)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-mono">{row.decode_time_ms_mean.toFixed(1)} ± {row.decode_time_ms_std.toFixed(1)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-mono">
                      {row.psnr_mean === "Infinity" ? "Lossless" : Number(row.psnr_mean).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-mono">{row.ssim_mean.toFixed(4)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-mono">{row.peak_memory_mb_mean.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
