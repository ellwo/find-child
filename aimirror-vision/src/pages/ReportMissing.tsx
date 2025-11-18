import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { createMissingReport } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Upload, Camera, CheckCircle2, Loader2 } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { CameraCapture } from '@/components/CameraCapture';

const ReportMissing: React.FC = () => {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [formData, setFormData] = useState({
    reporter_name: '',
    reporter_email: '',
    reporter_phone: '',
    child_name: '',
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [showCamera, setShowCamera] = useState(false);
  const [reportNumber, setReportNumber] = useState<string | null>(null);

  const createReportMutation = useMutation({
    mutationFn: (formDataToSend: FormData) => createMissingReport(formDataToSend),
    onSuccess: (data) => {
      setReportNumber(data.report_number);
      toast({
        title: t('report.success'),
        description: t('report.createdSuccessfully'),
      });
      // Reset form
      setFormData({
        reporter_name: '',
        reporter_email: '',
        reporter_phone: '',
        child_name: '',
      });
      setSelectedFile(null);
      setImagePreview(null);
    },
    onError: (error: any) => {
      const errorMessage =
        error?.response?.data?.detail || t('report.error');
      toast({
        title: t('report.error'),
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

  const handleCameraCapture = (file: File) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
    setShowCamera(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedFile) {
      toast({
        title: t('report.error'),
        description: t('report.selectImage'),
        variant: 'destructive',
      });
      return;
    }

    const formDataToSend = new FormData();
    formDataToSend.append('reporter_name', formData.reporter_name);
    formDataToSend.append('reporter_email', formData.reporter_email);
    formDataToSend.append('reporter_phone', formData.reporter_phone);
    formDataToSend.append('child_name', formData.child_name);
    formDataToSend.append('child_photo', selectedFile);

    createReportMutation.mutate(formDataToSend);
  };

  if (reportNumber) {
    return (
      <div className="space-y-6 animate-slide-up">
        <Card className="glass-effect shadow-card border-green-500">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-green-500 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold">{t('report.success')}</h2>
              <p className="text-muted-foreground">{t('report.reportCreated')}</p>
              <div className="bg-muted p-4 rounded-lg">
                <p className="text-sm text-muted-foreground mb-2">{t('report.reportNumber')}</p>
                <p className="text-2xl font-bold font-mono">{reportNumber}</p>
              </div>
              <p className="text-sm text-muted-foreground">
                {t('report.saveNumber')}
              </p>
              <Button
                onClick={() => {
                  setReportNumber(null);
                  setFormData({
                    reporter_name: '',
                    reporter_email: '',
                    reporter_phone: '',
                    child_name: '',
                  });
                  setSelectedFile(null);
                  setImagePreview(null);
                }}
                variant="outline"
              >
                {t('report.createAnother')}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-accent flex items-center justify-center glow-effect">
          <AlertCircle className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">{t('report.title')}</h1>
          <p className="text-muted-foreground">{t('report.description')}</p>
        </div>
      </div>

      <Card className="glass-effect shadow-card">
        <CardHeader>
          <CardTitle>{t('report.reportForm')}</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="reporter_name">{t('report.reporterName')} *</Label>
                <Input
                  id="reporter_name"
                  value={formData.reporter_name}
                  onChange={(e) =>
                    setFormData({ ...formData, reporter_name: e.target.value })
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reporter_email">{t('report.reporterEmail')} *</Label>
                <Input
                  id="reporter_email"
                  type="email"
                  value={formData.reporter_email}
                  onChange={(e) =>
                    setFormData({ ...formData, reporter_email: e.target.value })
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reporter_phone">{t('report.reporterPhone')} *</Label>
                <Input
                  id="reporter_phone"
                  type="tel"
                  value={formData.reporter_phone}
                  onChange={(e) =>
                    setFormData({ ...formData, reporter_phone: e.target.value })
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="child_name">{t('report.childName')} *</Label>
                <Input
                  id="child_name"
                  value={formData.child_name}
                  onChange={(e) =>
                    setFormData({ ...formData, child_name: e.target.value })
                  }
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>{t('report.childPhoto')} *</Label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex-1"
                >
                  <Upload className="mr-2 h-4 w-4" />
                  {t('report.uploadPhoto')}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowCamera(true)}
                  className="flex-1"
                >
                  <Camera className="mr-2 h-4 w-4" />
                  {t('report.capturePhoto')}
                </Button>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
              />
              {imagePreview && (
                <div className="mt-4">
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="w-full max-w-md rounded-lg border"
                  />
                </div>
              )}
            </div>

            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {t('report.faceRequired')}
              </AlertDescription>
            </Alert>

            <Button
              type="submit"
              className="w-full bg-gradient-primary"
              disabled={createReportMutation.isPending || !selectedFile}
            >
              {createReportMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('report.creating')}
                </>
              ) : (
                t('report.submit')
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {showCamera && (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={() => setShowCamera(false)}
        />
      )}
    </div>
  );
};

export default ReportMissing;

