import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { searchByImage } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Search as SearchIcon, Upload, Camera, X, ChevronDown, ChevronUp } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';
import { toast } from '@/hooks/use-toast';
import { CameraCapture } from '@/components/CameraCapture';

const Search: React.FC = () => {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [showCamera, setShowCamera] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [threshold, setThreshold] = useState(0.7);
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  const searchMutation = useMutation({
    mutationFn: searchByImage,
    onSuccess: (data) => {
      toast({
        title: t('search.results'),
        description: t('search.foundResults', { count: data?.total || 0 }),
      });
    },
    onError: (error: unknown) => {
      const errorMessage = error instanceof Error 
        ? error.message 
        : (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      toast({
        title: t('common.error'),
        description: errorMessage,
        variant: 'destructive',
      });
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleCameraCapture = (blob: Blob) => {
    const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });
    setSelectedFile(file);
    
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
    
    setShowCamera(false);
    
    // Show success message
    toast({
      title: t('search.results') || 'Photo captured',
      description: 'Searching for matches...',
    });
    
    // Auto-search after a short delay to ensure UI updates
    setTimeout(() => {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('threshold', threshold.toString());
      if (dateRange.start) formData.append('start_ts', dateRange.start);
      if (dateRange.end) formData.append('end_ts', dateRange.end);
      searchMutation.mutate(formData);
    }, 300);
  };

  const handleCameraClose = () => {
    setShowCamera(false);
  };

  const handleSearch = () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('image', selectedFile);
    formData.append('threshold', threshold.toString());
    if (dateRange.start) formData.append('start_ts', dateRange.start);
    if (dateRange.end) formData.append('end_ts', dateRange.end);

    searchMutation.mutate(formData);
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setImagePreview(null);
    // Clear search results when clearing selection
    searchMutation.reset();
  };

  return (
    <div className="space-y-6 animate-slide-up max-w-6xl mx-auto">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-accent flex items-center justify-center glow-effect">
          <SearchIcon className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">{t('search.title')}</h1>
          <p className="text-muted-foreground">{t('search.subtitle')}</p>
        </div>
      </div>

      {/* Camera Capture Modal */}
      {showCamera && (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={handleCameraClose}
        />
      )}

      {/* Upload Section */}
      <Card className="glass-effect shadow-card">
        <CardContent className="pt-6">
          {!imagePreview ? (
            <div className="space-y-4">
              <div
                className="border-2 border-dashed border-border rounded-xl p-12 text-center hover:border-primary transition-colors cursor-pointer"
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                <p className="text-lg mb-2">{t('search.uploadZone')}</p>
                <p className="text-sm text-muted-foreground mb-4">{t('search.orUseCamera')}</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Camera Button */}
                <button
                  type="button"
                  onClick={() => setShowCamera(true)}
                  className="relative group flex flex-col items-center justify-center h-48 border-2 border-dashed border-primary/40 rounded-2xl cursor-pointer overflow-hidden transition-all hover:border-primary hover:shadow-glow"
                >
                  <div className="absolute inset-0 gradient-primary opacity-0 group-hover:opacity-10 transition-opacity" />
                  <div className="relative z-10 flex flex-col items-center">
                    <div className="p-4 rounded-full bg-primary/10 group-hover:bg-primary/20 transition-colors mb-3">
                      <Camera className="w-8 h-8 text-primary" />
                    </div>
                    <span className="text-sm font-semibold text-foreground mb-1">
                      {t('search.openCamera') || 'Open Camera'}
                    </span>
                    <span className="text-xs text-muted-foreground px-4 text-center">
                      {t('search.cameraDescription') || 'Take a photo with your camera'}
                    </span>
                  </div>
                </button>

                {/* Upload Button */}
                <label
                  htmlFor="file-upload"
                  className="relative group flex flex-col items-center justify-center h-48 border-2 border-dashed border-accent/40 rounded-2xl cursor-pointer overflow-hidden transition-all hover:border-accent hover:shadow-glow"
                >
                  <div className="absolute inset-0 gradient-secondary opacity-0 group-hover:opacity-10 transition-opacity" />
                  <div className="relative z-10 flex flex-col items-center">
                    <div className="p-4 rounded-full bg-accent/10 group-hover:bg-accent/20 transition-colors mb-3">
                      <Upload className="w-8 h-8 text-accent" />
                    </div>
                    <span className="text-sm font-semibold text-foreground mb-1">
                      {t('common.import') || 'Upload Photo'}
                    </span>
                    <span className="text-xs text-muted-foreground px-4 text-center">
                      {t('search.uploadDescription') || 'Select an image from your device'}
                    </span>
                  </div>
                  <input
                    id="file-upload"
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleFileSelect}
                  />
                </label>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="relative rounded-xl overflow-hidden border-2 border-primary/30 shadow-glow">
                <img src={imagePreview} alt="Preview" className="w-full max-h-96 object-contain mx-auto" />
                <Button
                  size="icon"
                  variant="destructive"
                  className="absolute top-4 right-4"
                  onClick={clearSelection}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
              <Button onClick={handleSearch} className="w-full bg-gradient-primary" disabled={searchMutation.isPending}>
                <SearchIcon className="w-4 h-4 mr-2" />
                {searchMutation.isPending ? t('search.searching') : t('search.searchButton')}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Advanced Options */}
      <Card className="glass-effect shadow-card">
        <CardHeader>
          <Button
            variant="ghost"
            className="w-full flex items-center justify-between p-0"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            <CardTitle>{t('search.advancedOptions')}</CardTitle>
            {showAdvanced ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </Button>
        </CardHeader>
        {showAdvanced && (
          <CardContent className="space-y-6">
            <div>
              <Label>{t('search.threshold')}: {(threshold * 100).toFixed(0)}%</Label>
              <Slider
                value={[threshold]}
                onValueChange={([value]) => setThreshold(value)}
                min={0}
                max={1}
                step={0.01}
                className="mt-2"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>{t('search.startDate')}</Label>
                <Input
                  type="datetime-local"
                  value={dateRange.start}
                  onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                />
              </div>
              <div>
                <Label>{t('search.endDate')}</Label>
                <Input
                  type="datetime-local"
                  value={dateRange.end}
                  onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                />
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Results */}
      {searchMutation.data && (
        <Card className="glass-effect shadow-card">
          <CardHeader>
            <CardTitle>
              {t('search.foundResults', { count: searchMutation.data.total })}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {searchMutation.data.results.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                {t('search.noResults')}
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {searchMutation.data.results.map((result: { image_url: string; camera_id: string; camera_name?: string; timestamp: string; similarity: number }, index: number) => (
                  <Card key={index} className="glass-effect hover:shadow-elevated transition-all duration-300 hover:-translate-y-1 overflow-hidden">
                    <div className="aspect-square overflow-hidden">
                      <img
                        src={result.image_url}
                        alt="Match"
                        className="w-full h-full object-cover hover:scale-110 transition-transform duration-300"
                      />
                    </div>
                    <CardContent className="p-3 space-y-2">
                      <Badge variant="default" className="bg-gradient-primary">
                        {(result.similarity * 100).toFixed(1)}% {t('search.similarity')}
                      </Badge>
                      <Badge variant="secondary" className="text-xs">
                        {result.camera_name || result.camera_id}
                      </Badge>
                      <p className="text-xs text-muted-foreground">
                        {format(new Date(result.timestamp), 'PPp')}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Search;
